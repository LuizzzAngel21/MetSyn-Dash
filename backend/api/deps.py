"""
Inyección de dependencias — conecta puertos con adaptadores.
Cambia un adaptador aquí sin tocar el dominio.
"""
from functools import lru_cache

# from adapters.excel_pandas import ExcelPandasAdapter
# from adapters.ge_validator import GEValidatorAdapter
# from adapters.imputer_knn import KNNImputerAdapter
# from adapters.supabase_repo import SupabaseRepoAdapter
# from adapters.model_xgb import XGBoostAdapter
# from adapters.shap_explainer import ShapExplainerAdapter


@lru_cache
def get_ingesta():
    # return ExcelPandasAdapter()
    raise NotImplementedError("Implementar en Sprint 1")


@lru_cache
def get_validacion():
    raise NotImplementedError("Implementar en Sprint 1")


@lru_cache
def get_imputacion():
    raise NotImplementedError("Implementar en Sprint 1")


@lru_cache
def get_repositorio():
    raise NotImplementedError("Implementar en Sprint 2")


@lru_cache
def get_modelo():
    raise NotImplementedError("Implementar en Sprint 5")


@lru_cache
def get_explicabilidad():
    raise NotImplementedError("Implementar en Sprint 5")
