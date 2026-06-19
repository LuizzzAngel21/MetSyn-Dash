"""
Configuración central del backend — MetSyn Dashboard.

Único punto donde se leen las credenciales del entorno. Usa `pydantic-settings`
para validar y *fail-fast* si falta una variable obligatoria. Las credenciales
viven SIEMPRE en `.env` (no versionado); nunca se hardcodean en el código.

Variables esperadas (ver `.env.example`):
    SUPABASE_URL          (obligatoria)
    SUPABASE_SERVICE_KEY  (obligatoria — escrituras del backend, omite RLS)
    SUPABASE_ANON_KEY     (opcional — acceso de sólo lectura del frontend)
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env vive en la raíz del repo (un nivel por encima de backend/).
_REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str
    supabase_service_key: str
    supabase_anon_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Settings cacheado. Lanza `ValidationError` si falta una credencial."""
    return Settings()
