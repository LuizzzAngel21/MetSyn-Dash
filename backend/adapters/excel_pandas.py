"""Adaptador de IngestaPort — lectura de Excel con pandas/openpyxl."""
from __future__ import annotations

import pandas as pd


class ExcelPandasAdapter:
    """Implementa `IngestaPort`: lee una hoja (período) de un Excel a DataFrame."""

    def leer_excel(self, ruta: str, periodo: str) -> pd.DataFrame:
        df = pd.read_excel(ruta, sheet_name=periodo, dtype=object)
        df["period"] = periodo
        return df

    def hojas(self, ruta: str) -> list[str]:
        """Lista los nombres de hoja (períodos) presentes en el archivo."""
        return pd.ExcelFile(ruta).sheet_names
