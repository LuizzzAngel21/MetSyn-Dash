"""
Etapa 1.5 — Imputación (adaptador default: KNN).

Lee `data/clean/metsyn_clean.csv` y produce `data/imputed/metsyn_imputed.csv`.

Imputa las 6 columnas que portan los criterios ATP-III usando `KNNImputer`
sobre el espacio numérico clínico completo (+ `sexo` codificado). Antes de
imputar registra la máscara de faltantes y emite:

  - columnas booleanas `imp_<col>` por cada criterio imputado, y
  - una columna `imputed_flags` (JSON) con la lista de criterios imputados por
    fila — la misma forma que consumirá la tabla `clinical_records` (Sprint 2).

Esto permite reportar prevalencia CON y SIN imputación, mitigando el riesgo de
`perabd` 100 % ausente en 2025. La firma de `imputar_df` respeta `ImputacionPort`
del dominio hexagonal: (DataFrame) -> (DataFrame, dict de metadatos).
"""
from __future__ import annotations

import json

import pandas as pd
from sklearn.impute import KNNImputer

from ml.common import (
    CRITERIO_NUMERIC,
    DIR_CLEAN,
    DIR_IMPUTED,
    FILE_CLEAN,
    FILE_IMPUTED,
    NUMERIC_COLS,
    asegurar_dir,
)

N_NEIGHBORS = 5


def imputar_df(df: pd.DataFrame, n_neighbors: int = N_NEIGHBORS) -> tuple[pd.DataFrame, dict]:
    df = df.copy()

    # Asegurar tipo numérico de las columnas de trabajo.
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Máscara de faltantes en los criterios ANTES de imputar.
    mask = df[CRITERIO_NUMERIC].isna()

    # Matriz de features: numéricas clínicas + sexo codificado como apoyo.
    feat_cols = [c for c in NUMERIC_COLS if c in df.columns]
    matriz = df[feat_cols].copy()
    matriz["sexo_code"] = df["sexo"].map({"M": 0.0, "F": 1.0})

    imputer = KNNImputer(n_neighbors=n_neighbors, weights="distance")
    imputado = pd.DataFrame(
        imputer.fit_transform(matriz),
        columns=matriz.columns,
        index=matriz.index,
    )

    # Escribir de vuelta sólo las columnas de features (no sexo_code).
    for col in feat_cols:
        df[col] = imputado[col]

    # Banderas de imputación por criterio + JSON consolidado por fila.
    for col in CRITERIO_NUMERIC:
        df[f"imp_{col}"] = mask[col].values
    df["imputed_flags"] = [
        json.dumps([c for c in CRITERIO_NUMERIC if bool(row[c])])
        for _, row in mask.iterrows()
    ]

    meta = {
        "n_neighbors": n_neighbors,
        "imputados_por_criterio": {c: int(mask[c].sum()) for c in CRITERIO_NUMERIC},
        "filas": int(len(df)),
    }
    return df, meta


def imputar() -> None:
    df = pd.read_csv(DIR_CLEAN / FILE_CLEAN)
    out_df, meta = imputar_df(df)

    asegurar_dir(DIR_IMPUTED)
    out = DIR_IMPUTED / FILE_IMPUTED
    out_df.to_csv(out, index=False, encoding="utf-8")

    print(f"[impute] {len(out_df)} filas -> {out}")
    print(f"[impute] imputados por criterio: {meta['imputados_por_criterio']}")


if __name__ == "__main__":
    imputar()
