"""
Etapa 1.3 — Anonimización.

Lee el Excel crudo y produce `data/anon/metsyn_anon.csv` sin identificadores
directos. `ID2` se transforma en `patient_id` mediante un hash estable (SHA-256
con sal) que preserva el seguimiento longitudinal: el mismo `ID2` produce el
mismo `patient_id` en todos los períodos, pero el original no es recuperable.

Las filas sin `ID2` reciben un identificador sustituto único por (período, fila)
con prefijo `anon-`: no son enlazables entre períodos, pero conservan su valor
clínico para los agregados de prevalencia.

La sal se lee de METSYN_ANON_SALT (ver `.env.example`). Debe permanecer estable
para que `dvc repro` sea reproducible y el enlace longitudinal no se rompa.
"""
from __future__ import annotations

import hashlib
import os

import pandas as pd
from dotenv import load_dotenv

from ml.common import DIR_ANON, FILE_ANON, PII_COLS, asegurar_dir, cargar_crudo

load_dotenv()

# Sal por defecto: estable y versionada para que el pipeline sea reproducible.
# En producción se sobreescribe vía variable de entorno METSYN_ANON_SALT.
SALT = os.getenv("METSYN_ANON_SALT", "metsyn-gicc-usil-2026")


def hash_id(valor) -> str:
    """SHA-256(salt + ID2) truncado a 16 hex chars → patient_id estable."""
    h = hashlib.sha256(f"{SALT}:{valor}".encode("utf-8")).hexdigest()
    return f"pid-{h[:16]}"


def anonimizar() -> None:
    df = cargar_crudo()

    # patient_id: hash estable cuando hay ID2; sustituto único cuando no.
    pids = []
    for idx, raw in df["ID2"].items():
        if pd.notna(raw):
            # ID2 llega como float (p.ej. 533.0) — normalizar a entero textual.
            try:
                clave = str(int(float(raw)))
            except (ValueError, TypeError):
                clave = str(raw).strip()
            pids.append(hash_id(clave))
        else:
            pids.append(f"anon-{df.at[idx, 'period']}-{idx}")
    df["patient_id"] = pids

    # Eliminar identificadores directos: nunca persisten ni a Git ni a DVC.
    df = df.drop(columns=[c for c in PII_COLS if c in df.columns])

    # Reordenar para que patient_id encabece.
    cols = ["patient_id", "period"] + [
        c for c in df.columns if c not in ("patient_id", "period")
    ]
    df = df[cols]

    asegurar_dir(DIR_ANON)
    out = DIR_ANON / FILE_ANON
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"[anonymize] {len(df)} filas -> {out}")
    print(f"[anonymize] patient_id únicos: {df['patient_id'].nunique()}")


if __name__ == "__main__":
    anonimizar()
