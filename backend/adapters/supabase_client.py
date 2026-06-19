"""
Cliente base de Supabase — capa de infraestructura.

Thin wrapper sobre `supabase.create_client`. NO contiene lógica de negocio:
sólo entrega un `Client` autenticado con la SERVICE KEY (escrituras del backend,
omite RLS). Cacheado con `lru_cache` para reutilizar una sola conexión.

Es el único módulo, junto con `supabase_repo`, que importa la librería
`supabase`. El dominio nunca la ve (arquitectura hexagonal).
"""
from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Devuelve el cliente Supabase del backend (service role, cacheado)."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)
