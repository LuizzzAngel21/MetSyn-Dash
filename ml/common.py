"""
Utilidades compartidas por las etapas del ETL (Sprint 1).

Centraliza rutas, carga del Excel crudo por período y las reglas de
saneamiento de bajo nivel (normalización de `sexo`, coerción numérica,
parseo de `presionarterial`). El eje temporal se trata como CATEGÓRICO
discreto: los períodos válidos son 2021, 2023, 2024 y 2025 (2022 no existe).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

# --- Rutas del proyecto -------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW_XLSX = ROOT / "data" / "raw" / "metsyn_dataset.xlsx"

DIR_ANON = ROOT / "data" / "anon"
DIR_CLEAN = ROOT / "data" / "clean"
DIR_IMPUTED = ROOT / "data" / "imputed"
DIR_FEATURED = ROOT / "data" / "featured"
DIR_VALIDATIONS = ROOT / "validations"

# Nombre de archivo único por etapa (un CSV combinado con columna `period`).
FILE_ANON = "metsyn_anon.csv"
FILE_CLEAN = "metsyn_clean.csv"
FILE_IMPUTED = "metsyn_imputed.csv"
FILE_FEATURED = "metsyn_featured.csv"

# --- Dominio del dataset ------------------------------------------------------
PERIODOS = ["2021", "2023", "2024", "2025"]  # 2022 no existe (eje categórico)

# Columnas que portan los 5 criterios ATP-III (las que se imputan).
CRITERIO_NUMERIC = ["perabd", "trig", "hdl", "glu", "presion_sis", "presion_dia"]

# Otras columnas numéricas clínicas/antropométricas usadas como contexto.
OTRAS_NUMERIC = ["edad", "hb", "plaq", "leuc", "ct", "ldl", "imc", "fc"]

NUMERIC_COLS = CRITERIO_NUMERIC + OTRAS_NUMERIC

# Columnas consideradas identificadores directos: nunca persisten tras anonimizar.
PII_COLS = ["source", "ID2"]

# Valores que en este dataset representan "faltante" pero llegan como texto.
NA_LITERALS = {"NA", "N/A", "NAN", "NONE", "-", "_", "", "."}

# Rangos fisiológicamente plausibles. Un valor fuera de rango (p.ej. trig=0,
# presion_sis=11, edad=124) es un faltante/error codificado como número: se
# convierte a NaN en la limpieza para que luego lo trate la imputación. Estos
# rangos son ⊆ a los del contrato Pandera, de modo que los valores imputados
# (dentro del rango observado) siempre cumplen el contrato de salida.
RANGOS_PLAUSIBLES = {
    "edad":        (15, 100),
    "perabd":      (40, 200),
    "trig":        (10, 2000),
    "hdl":         (10, 150),
    "glu":         (40, 800),
    "presion_sis": (60, 300),
    "presion_dia": (30, 200),
    "imc":         (10, 80),
    "fc":          (30, 220),
}


def cargar_crudo() -> pd.DataFrame:
    """Lee las 4 hojas del Excel crudo y las concatena con columna `period`."""
    frames = []
    for periodo in PERIODOS:
        df = pd.read_excel(RAW_XLSX, sheet_name=periodo, dtype=object)
        df["period"] = periodo
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def normalizar_sexo(serie: pd.Series) -> pd.Series:
    """Mapea las múltiples variantes de `sexo` a {'M','F'} o NaN.

    Cubre M/F, MASCULINO/FEMENINO (y capitalizaciones), y deja como NaN los
    valores fuera de dominio (números de ID por desalineación, nulos, basura).
    """
    def _map(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip().upper()
        if s in ("M", "MASCULINO", "MASC", "HOMBRE", "H"):
            return "M"
        if s in ("F", "FEMENINO", "FEM", "MUJER"):
            return "F"
        return np.nan

    return serie.map(_map)


def a_numerico(serie: pd.Series) -> pd.Series:
    """Convierte a numérico tratando literales de faltante como NaN."""
    limpio = serie.map(
        lambda v: np.nan
        if (pd.isna(v) or str(v).strip().upper() in NA_LITERALS)
        else v
    )
    return pd.to_numeric(limpio, errors="coerce")


_PA_RE = re.compile(r"(\d{2,3})\s*/\s*(\d{2,3})")


def parsear_presion(serie: pd.Series) -> pd.DataFrame:
    """Extrae (sis, dia) del texto combinado `presionarterial` ('120/70 mmHg.').

    Devuelve un DataFrame con columnas `pa_sis` y `pa_dia` (float, NaN si no
    parsea). Se usa para rellenar `presion_sis`/`presion_dia` cuando faltan.
    """
    sis, dia = [], []
    for v in serie:
        m = _PA_RE.search(str(v)) if pd.notna(v) else None
        if m:
            sis.append(float(m.group(1)))
            dia.append(float(m.group(2)))
        else:
            sis.append(np.nan)
            dia.append(np.nan)
    return pd.DataFrame({"pa_sis": sis, "pa_dia": dia}, index=serie.index)


def aplicar_rangos_plausibles(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte a NaN los valores numéricos fuera de rango fisiológico."""
    df = df.copy()
    for col, (lo, hi) in RANGOS_PLAUSIBLES.items():
        if col in df.columns:
            fuera = (df[col] < lo) | (df[col] > hi)
            df.loc[fuera, col] = np.nan
    return df


def asegurar_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
