"""
Inyección de dependencias — conecta puertos con adaptadores.
Cambia un adaptador aquí sin tocar el dominio (único punto de cableado).
"""
from functools import lru_cache

from adapters.excel_pandas import ExcelPandasAdapter
from adapters.ge_validator import GEValidatorAdapter
from adapters.imputer_knn import KNNImputerAdapter
from adapters.supabase_repo import SupabaseRepositorioAdapter


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
    # Adaptador de RepositorioPort sobre Supabase/PostgreSQL (Sprint 2).
    # El cliente se resuelve perezosamente (no requiere credenciales al cablear).
    return SupabaseRepositorioAdapter()


@lru_cache
def get_modelo():
    raise NotImplementedError("Implementar en Sprint 5")


@lru_cache
def get_explicabilidad():
    raise NotImplementedError("Implementar en Sprint 5")
