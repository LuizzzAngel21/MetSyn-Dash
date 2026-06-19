"""
Etapa 1.4 — Limpieza y estandarización.

Lee `data/anon/metsyn_anon.csv` y produce `data/clean/metsyn_clean.csv`:

  1. Normaliza `sexo` a {'M','F'} (descarta variantes y números de ID).
  2. Descarta filas-basura (sin `sexo` válido y sin ninguna medición clínica),
     que en el crudo corresponden al bloque desalineado al final de 2021.
  3. Convierte literales de faltante ("NA", "-", "_", …) a nulos reales y tipa
     todas las columnas numéricas.
  4. Parsea `presionarterial` ('120/70 mmHg.') y rellena `presion_sis`/
     `presion_dia` cuando faltan, usando las columnas numéricas como fuente
     principal.

La función `limpiar_df` es pura (DataFrame → DataFrame) para poder reutilizarla
desde el adaptador de ingesta de la API sin tocar disco.
"""
from __future__ import annotations

import pandas as pd

from ml.common import (
    CRITERIO_NUMERIC,
    DIR_ANON,
    DIR_CLEAN,
    FILE_ANON,
    FILE_CLEAN,
    NUMERIC_COLS,
    a_numerico,
    aplicar_rangos_plausibles,
    asegurar_dir,
    normalizar_sexo,
    parsear_presion,
)


def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Normalizar sexo (prerrequisito de los umbrales ATP-III por género).
    df["sexo"] = normalizar_sexo(df["sexo"])

    # 3. Tipar numéricos (convierte literales de faltante a NaN).
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = a_numerico(df[col])

    # 4. Parsear presión combinada y rellenar sis/dia faltantes.
    if "presionarterial" in df.columns:
        pa = parsear_presion(df["presionarterial"])
        df["presion_sis"] = df["presion_sis"].fillna(pa["pa_sis"])
        df["presion_dia"] = df["presion_dia"].fillna(pa["pa_dia"])

    # 5. Valores fuera de rango fisiológico (trig=0, presion=11, edad=124…) → NaN.
    df = aplicar_rangos_plausibles(df)

    # 2. Descartar filas-basura: sin sexo válido y sin ninguna medición clínica.
    tiene_clinica = df[CRITERIO_NUMERIC].notna().any(axis=1)
    sexo_valido = df["sexo"].notna()
    basura = ~sexo_valido & ~tiene_clinica
    n_basura = int(basura.sum())
    df = df[~basura].reset_index(drop=True)

    if n_basura:
        print(f"[clean] filas-basura descartadas: {n_basura}")

    return df


def limpiar() -> None:
    df = pd.read_csv(DIR_ANON / FILE_ANON, dtype=object)
    limpio = limpiar_df(df)

    asegurar_dir(DIR_CLEAN)
    out = DIR_CLEAN / FILE_CLEAN
    limpio.to_csv(out, index=False, encoding="utf-8")

    print(f"[clean] {len(limpio)} filas -> {out}")
    print(f"[clean] sexo: {limpio['sexo'].value_counts(dropna=False).to_dict()}")


if __name__ == "__main__":
    limpiar()
