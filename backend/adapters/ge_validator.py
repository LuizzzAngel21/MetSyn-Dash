"""Adaptador de ValidacionPort — Great Expectations como puerta de ingesta."""
from __future__ import annotations

import pandas as pd

from adapters import _paths  # noqa: F401  (añade la raíz del repo a sys.path)
from ml.expectations import ejecutar_suite, render_html, suite_estructural


class ValidacionError(Exception):
    """Se lanza cuando un Excel no cumple la suite estructural.

    Lleva adjuntos el resultado de GE (`reporte`) y el HTML renderizado para
    devolverlo al cliente como rechazo explicativo.
    """

    def __init__(self, reporte: dict, html: str):
        self.reporte = reporte
        self.html = html
        super().__init__(f"Validación estructural fallida: {reporte['n_failed']} expectativas")


class GEValidatorAdapter:
    """Implementa `ValidacionPort`: valida estructura y dominio antes del ETL."""

    def validar(self, df: pd.DataFrame, periodo: str) -> pd.DataFrame:
        reporte = ejecutar_suite(df, suite_estructural)
        if not reporte["success"]:
            raise ValidacionError(reporte, render_html([reporte]))
        return df
