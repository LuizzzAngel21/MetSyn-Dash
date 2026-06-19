"""
Etapa 1.6 — Criterios ATP-III + metsyn_flag.

Lee `data/imputed/metsyn_imputed.csv`, aplica `calcular_flags()` del DOMINIO
(núcleo hexagonal, `backend/domain/atp3.py`) y produce
`data/featured/metsyn_featured.csv`, listo para persistir en Supabase (Sprint 2)
y entrenar el modelo (Sprint 5).

La salida se valida contra el contrato Pandera (`ml/contracts.py`) antes de
escribirse: si una columna se sale de dominio, la etapa falla en vez de
propagar datos corruptos aguas abajo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# El dominio vive bajo `backend/`; garantizamos que la raíz del repo esté en path
# tanto si se ejecuta con `python -m ml.features` como desde un import externo.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.domain.atp3 import calcular_flags  # noqa: E402

from ml.common import (  # noqa: E402
    DIR_FEATURED,
    DIR_IMPUTED,
    FILE_FEATURED,
    FILE_IMPUTED,
    asegurar_dir,
)
from ml.contracts import validar_featured  # noqa: E402


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica las reglas ATP-III del dominio a un DataFrame imputado y limpio."""
    return calcular_flags(df)


def featurizar() -> None:
    df = pd.read_csv(DIR_IMPUTED / FILE_IMPUTED)
    featured = construir_features(df)

    # Contrato de salida: si no valida, la etapa falla (no escribe basura).
    validar_featured(featured)

    asegurar_dir(DIR_FEATURED)
    out = DIR_FEATURED / FILE_FEATURED
    featured.to_csv(out, index=False, encoding="utf-8")

    prev = featured.groupby("period")["metsyn_flag"].mean().mul(100).round(1)
    print(f"[features] {len(featured)} filas -> {out}")
    print(f"[features] prevalencia MetSyn % por período: {prev.to_dict()}")


if __name__ == "__main__":
    featurizar()
