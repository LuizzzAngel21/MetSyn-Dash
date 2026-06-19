"""
Etapa 1.2 — Validación estructural con Great Expectations.

Carga el Excel crudo y corre dos suites (ver `ml/expectations.py`):

  - estructural sobre el crudo (columnas obligatorias, period categórico): es la
    puerta de calidad — si falla, la etapa termina con código ≠ 0 y `dvc repro`
    se detiene.
  - clínica sobre una vista LIMPIA en memoria (sexo ∈ {M,F}, rangos de los 5
    criterios): informa la calidad de valores tras el saneamiento.

Escribe `validations/metsyn_validation.html` (reporte legible que pide el DoD)
y `validations/metsyn_validation.json` (resultado máquina-legible).
"""
from __future__ import annotations

import json
import sys

from ml.clean import limpiar_df
from ml.common import DIR_VALIDATIONS, asegurar_dir, cargar_crudo
from ml.expectations import (
    ejecutar_suite,
    render_html,
    suite_clinica,
    suite_estructural,
)


def validar() -> bool:
    crudo = cargar_crudo()
    rep_estructural = ejecutar_suite(crudo, suite_estructural)

    # La suite clínica corre sobre datos limpios (sexo/numéricos ya saneados).
    limpio = limpiar_df(crudo)
    rep_clinica = ejecutar_suite(limpio, suite_clinica)

    asegurar_dir(DIR_VALIDATIONS)
    html = render_html([rep_estructural, rep_clinica])
    (DIR_VALIDATIONS / "metsyn_validation.html").write_text(html, encoding="utf-8")
    (DIR_VALIDATIONS / "metsyn_validation.json").write_text(
        json.dumps([rep_estructural, rep_clinica], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(
        f"[validate] estructural={'OK' if rep_estructural['success'] else 'FALLA'} "
        f"({rep_estructural['n_failed']} fallidas) · "
        f"clinica={'OK' if rep_clinica['success'] else 'FALLA'} "
        f"({rep_clinica['n_failed']} fallidas)"
    )
    print(f"[validate] reporte -> {DIR_VALIDATIONS / 'metsyn_validation.html'}")

    # La PUERTA es la suite estructural: bloquea si el crudo no tiene la forma.
    return rep_estructural["success"]


if __name__ == "__main__":
    ok = validar()
    sys.exit(0 if ok else 1)
