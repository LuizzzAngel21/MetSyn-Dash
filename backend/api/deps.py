"""
Inyección de dependencias — conecta puertos con adaptadores.
Cambia un adaptador aquí sin tocar el dominio (único punto de cableado).
"""
from functools import lru_cache

from adapters.excel_pandas import ExcelPandasAdapter
from adapters.ge_validator import GEValidatorAdapter
from adapters.imputer_knn import KNNImputerAdapter


@lru_cache
def get_ingesta():
    return ExcelPandasAdapter()


@lru_cache
def get_validacion():
    return GEValidatorAdapter()


@lru_cache
def get_imputacion():
    # Adaptador default de ImputacionPort. Cambiar a MissForest/MICE = una línea.
    return KNNImputerAdapter(n_neighbors=5)


@lru_cache
def get_repositorio():
    raise NotImplementedError("Implementar en Sprint 2 (Supabase + RLS)")


@lru_cache
def get_modelo():
    raise NotImplementedError("Implementar en Sprint 5")


@lru_cache
def get_explicabilidad():
    raise NotImplementedError("Implementar en Sprint 5")
