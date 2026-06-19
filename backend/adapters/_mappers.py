"""
Mapeo entre el DataFrame `featured` del ETL y las filas de la tabla
`clinical_records`. Reutiliza `ClinicalRecord` (ml.contracts) como validación y
fuente de verdad, de modo que el adaptador de persistencia no contiene lógica de
serialización.
"""
from __future__ import annotations

import math

import pandas as pd

from adapters import _paths  # noqa: F401  (añade la raíz del repo a sys.path)
from ml.contracts import ClinicalRecord


def _num(v) -> float | None:
    """Normaliza un valor numérico: NaN/None/no-convertible -> None.

    Postgres `numeric` no acepta NaN vía PostgREST, así que cualquier faltante
    se envía como NULL.
    """
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def featured_to_records(df: pd.DataFrame) -> list[dict]:
    """Proyecta el DataFrame featured a filas validadas listas para upsert.

    Cada fila pasa por `ClinicalRecord` (valida `period` categórico, `sexo`,
    rango de `criterios_n`, parseo de `imputed_flags`).
    """
    registros: list[dict] = []
    for _, row in df.iterrows():
        rec = ClinicalRecord(
            patient_id=str(row["patient_id"]),
            period=str(row["period"]),
            sexo=str(row["sexo"]),
            edad=_num(row.get("edad")),
            perabd=_num(row.get("perabd")),
            trig=_num(row.get("trig")),
            hdl=_num(row.get("hdl")),
            glu=_num(row.get("glu")),
            presion_sis=_num(row.get("presion_sis")),
            presion_dia=_num(row.get("presion_dia")),
            criterios_n=int(row["criterios_n"]),
            metsyn_flag=bool(row["metsyn_flag"]),
            imputed_flags=row.get("imputed_flags", []),
        )
        registros.append(rec.model_dump())
    return registros
