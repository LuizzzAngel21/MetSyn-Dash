"""Adaptador de ImputacionPort — imputación KNN (reusa la lógica del pipeline)."""
from __future__ import annotations

import pandas as pd

from adapters import _paths  # noqa: F401  (añade la raíz del repo a sys.path)
from ml.impute import imputar_df


class KNNImputerAdapter:
    """Implementa `ImputacionPort`: KNN con máscara `imputed_flags`.

    Cambiar a MissForest/MICE en el futuro es sustituir este adaptador en
    `deps.py` — el dominio no se entera.
    """

    def __init__(self, n_neighbors: int = 5):
        self.n_neighbors = n_neighbors

    def imputar(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        return imputar_df(df, n_neighbors=self.n_neighbors)
