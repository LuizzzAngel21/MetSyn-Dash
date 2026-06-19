"""
Suites de Great Expectations (GE 1.x) — MetSyn Dashboard.

Define dos suites y un runner reutilizable tanto por la etapa DVC `validate`
como por el adaptador de ingesta de la API:

  - `suite_estructural`: ¿es éste el archivo correcto? Columnas obligatorias
    presentes, tabla no vacía, `period` dentro del dominio categórico. Es la
    PUERTA de ingesta: un Excel que la falla se rechaza.
  - `suite_clinica`: ¿son válidos los valores? `sexo` ∈ {M,F} y los 5 criterios
    ATP-III dentro de rango fisiológico. Se corre sobre datos ya limpios.

`ejecutar_suite` devuelve un dict serializable (éxito + detalle por expectativa)
del que `render_html` produce el reporte HTML que pide el DoD.
"""
from __future__ import annotations

import datetime as _dt
import html as _html

import great_expectations as gx
import pandas as pd
from great_expectations import expectations as gxe

PERIODOS_VALIDOS = ["2021", "2023", "2024", "2025"]

# Columnas mínimas que cualquier Excel de salud ocupacional debe traer.
COLUMNAS_OBLIGATORIAS = [
    "ID2", "sexo", "edad", "perabd", "trig", "hdl",
    "glu", "presion_sis", "presion_dia", "period",
]


def suite_estructural(context) -> gx.ExpectationSuite:
    suite = context.suites.add(gx.ExpectationSuite(name="metsyn_estructural"))
    for col in COLUMNAS_OBLIGATORIAS:
        suite.add_expectation(gxe.ExpectColumnToExist(column=col))
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=1))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeInSet(column="period", value_set=PERIODOS_VALIDOS)
    )
    return suite


def suite_clinica(context) -> gx.ExpectationSuite:
    suite = context.suites.add(gx.ExpectationSuite(name="metsyn_clinica"))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeInSet(
            column="sexo", value_set=["M", "F"], mostly=0.99
        )
    )
    # Rangos fisiológicos de los 5 criterios ATP-III (mostly tolera outliers leves).
    rangos = {
        "perabd": (30, 200),
        "trig": (10, 2000),
        "hdl": (5, 200),
        "glu": (20, 800),
        "presion_sis": (50, 300),
        "presion_dia": (30, 200),
    }
    for col, (lo, hi) in rangos.items():
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeBetween(
                column=col, min_value=lo, max_value=hi, mostly=0.95
            )
        )
    return suite


def ejecutar_suite(df: pd.DataFrame, suite_builder) -> dict:
    """Corre una suite sobre un DataFrame en memoria (contexto efímero).

    `suite_builder` es una de las funciones `suite_*` que recibe el contexto y
    devuelve la `ExpectationSuite` ya registrada en él.
    """
    context = gx.get_context(mode="ephemeral")
    # Silenciar las barras de progreso para no contaminar los logs de DVC/API.
    try:
        from great_expectations.data_context.types.base import ProgressBarsConfig

        context.variables.progress_bars = ProgressBarsConfig(
            globally=False, metric_calculations=False
        )
    except Exception:  # pragma: no cover — cosmético, nunca debe romper la suite
        pass
    suite = suite_builder(context)
    batch_def = (
        context.data_sources.add_pandas("pandas_runtime")
        .add_dataframe_asset(name="metsyn_asset")
        .add_batch_definition_whole_dataframe("batch")
    )
    vd = context.validation_definitions.add(
        gx.ValidationDefinition(data=batch_def, suite=suite, name=f"vd_{suite.name}")
    )
    result = vd.run(batch_parameters={"dataframe": df})

    detalle = []
    for r in result.results:
        cfg = r.expectation_config
        detalle.append(
            {
                "expectation": cfg.type,
                "kwargs": {k: v for k, v in cfg.kwargs.items() if k != "batch_id"},
                "success": bool(r.success),
                "observed": r.result.get("observed_value")
                if isinstance(r.result, dict)
                else None,
                "unexpected_pct": r.result.get("unexpected_percent")
                if isinstance(r.result, dict)
                else None,
            }
        )
    return {
        "suite": suite.name,
        "success": bool(result.success),
        "n_expectations": len(detalle),
        "n_failed": sum(1 for d in detalle if not d["success"]),
        "results": detalle,
    }


def render_html(reportes: list[dict], titulo: str = "Reporte de Validación — MetSyn") -> str:
    """Renderiza uno o más resultados de suite a un HTML legible y autónomo."""
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = []
    for rep in reportes:
        estado = "PASÓ" if rep["success"] else "FALLÓ"
        color = "#1a7f37" if rep["success"] else "#cf222e"
        filas.append(
            f'<h2>Suite: {_html.escape(rep["suite"])} '
            f'<span style="color:{color}">[{estado}]</span></h2>'
        )
        filas.append(
            f'<p>{rep["n_expectations"]} expectativas · '
            f'{rep["n_failed"]} fallidas</p><table>'
            "<tr><th>Expectativa</th><th>Parámetros</th>"
            "<th>Resultado</th><th>Observado</th></tr>"
        )
        for d in rep["results"]:
            ok = "OK" if d["success"] else "FALLA"
            bg = "#e6f4ea" if d["success"] else "#ffebe9"
            obs = d["observed"] if d["observed"] is not None else d["unexpected_pct"]
            filas.append(
                f'<tr style="background:{bg}">'
                f'<td>{_html.escape(d["expectation"])}</td>'
                f'<td>{_html.escape(str(d["kwargs"]))}</td>'
                f"<td>{ok}</td><td>{_html.escape(str(obs))}</td></tr>"
            )
        filas.append("</table>")

    cuerpo = "\n".join(filas)
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>{_html.escape(titulo)}</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:2rem;color:#1f2328}}
 h1{{border-bottom:2px solid #d0d7de;padding-bottom:.4rem}}
 table{{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}}
 th,td{{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left;font-size:.9rem}}
 th{{background:#f6f8fa}}
</style></head><body>
<h1>{_html.escape(titulo)}</h1>
<p>Great Expectations · generado {ts}</p>
{cuerpo}
</body></html>"""
