"""
Puertos del dominio hexagonal — MetSyn Dashboard.
Cada puerto es un Protocol. Los adaptadores los implementan.
El dominio nunca importa adaptadores directamente.
"""
from typing import Protocol, runtime_checkable
import pandas as pd


@runtime_checkable
class IngestaPort(Protocol):
    def leer_excel(self, ruta: str, periodo: str) -> pd.DataFrame: ...


@runtime_checkable
class ValidacionPort(Protocol):
    def validar(self, df: pd.DataFrame, periodo: str) -> pd.DataFrame: ...


@runtime_checkable
class ImputacionPort(Protocol):
    def imputar(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]: ...


@runtime_checkable
class RepositorioPort(Protocol):
    def upsert_registros(self, df: pd.DataFrame, periodo: str) -> int: ...
    def obtener_prevalencia(self, periodo: str | None, sexo: str | None) -> dict: ...
    def obtener_registros(self, page: int, page_size: int, **filtros) -> dict: ...
    def obtener_tendencias(self, sexo: str | None) -> dict: ...
    def obtener_criterios(self, periodo: str | None, sexo: str | None) -> dict: ...
    def obtener_missingness(self, periodo: str | None) -> dict: ...


@runtime_checkable
class ModeloPort(Protocol):
    def predecir(self, features: dict) -> dict: ...


@runtime_checkable
class ExplicabilidadPort(Protocol):
    def explicar(self, features: dict, prediccion: dict) -> list[dict]: ...
