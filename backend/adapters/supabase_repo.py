"""
Adaptador de `RepositorioPort` — persistencia en Supabase (PostgreSQL).

Toda la dependencia de la librería `supabase` vive aquí (infraestructura). El
dominio sólo conoce el puerto. El cliente se obtiene de forma perezosa para que
construir el adaptador no requiera credenciales (útil en tests con mock).
"""
from __future__ import annotations

import json

import pandas as pd

from adapters import _paths  # noqa: F401  (añade la raíz del repo a sys.path)
from adapters._mappers import featured_to_records
from adapters.supabase_client import get_supabase_client
from ml.contracts import PERIODOS_VALIDOS

# Criterio ATP-III (nombre lógico) -> columna booleana persistida.
CRITERIOS_COLS = {
    "perabd": "criterio_perabd",
    "trig": "criterio_trig",
    "hdl": "criterio_hdl",
    "presion": "criterio_presion",
    "glu": "criterio_glu",
}

# Criterios cuyo faltante se rastrea en `imputed_flags` (nombres del ETL).
CRITERIOS_IMPUTABLES = ["perabd", "trig", "hdl", "glu", "presion_sis", "presion_dia"]


class SupabaseRepositorioAdapter:
    """Implementa `RepositorioPort` sobre la tabla `clinical_records`."""

    TABLE = "clinical_records"

    def __init__(self, client=None):
        # Inyectable para tests; en producción se resuelve perezosamente.
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def upsert_registros(self, df: pd.DataFrame, periodo: str) -> int:
        """Inserta/actualiza los registros del DataFrame por (patient_id, period)."""
        registros = featured_to_records(df)
        if not registros:
            return 0
        resp = (
            self.client.table(self.TABLE)
            .upsert(registros, on_conflict="patient_id,period")
            .execute()
        )
        return len(resp.data or [])

    def obtener_prevalencia(self, periodo: str | None = None, sexo: str | None = None) -> dict:
        """Prevalencia de MetSyn (positivos/total) con filtros opcionales."""

        def _contar(metsyn: bool | None = None) -> int:
            q = self.client.table(self.TABLE).select("patient_id", count="exact")
            if periodo is not None:
                q = q.eq("period", periodo)
            if sexo is not None:
                q = q.eq("sexo", sexo)
            if metsyn is not None:
                q = q.eq("metsyn_flag", metsyn)
            return q.execute().count or 0

        total = _contar()
        positivos = _contar(metsyn=True)
        prevalencia = round(positivos / total * 100, 1) if total else 0.0
        return {
            "periodo": periodo,
            "sexo": sexo,
            "total": total,
            "positivos": positivos,
            "prevalencia_pct": prevalencia,
        }

    def obtener_registros(self, page: int = 1, page_size: int = 50, **filtros) -> dict:
        """Lista paginada de registros con filtros opcionales (period/sexo/metsyn_flag)."""
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), 200))
        inicio = (page - 1) * page_size
        fin = inicio + page_size - 1

        q = self.client.table(self.TABLE).select("*", count="exact")
        for campo in ("period", "sexo", "metsyn_flag"):
            valor = filtros.get(campo)
            if valor is not None:
                q = q.eq(campo, valor)

        resp = q.order("patient_id").range(inicio, fin).execute()
        return {
            "page": page,
            "page_size": page_size,
            "total": resp.count or 0,
            "items": resp.data or [],
        }

    def obtener_tendencias(self, sexo: str | None = None) -> dict:
        """Serie de prevalencia por período (eje temporal categórico)."""
        serie = []
        for periodo in PERIODOS_VALIDOS:
            p = self.obtener_prevalencia(periodo=periodo, sexo=sexo)
            serie.append(
                {
                    "period": periodo,
                    "total": p["total"],
                    "positivos": p["positivos"],
                    "prevalencia_pct": p["prevalencia_pct"],
                }
            )
        return {"sexo": sexo, "serie": serie}

    def obtener_criterios(self, periodo: str | None = None, sexo: str | None = None) -> dict:
        """Conteo (y %) de positivos por criterio ATP-III, con filtros opcionales."""

        def _contar(col: str | None = None) -> int:
            q = self.client.table(self.TABLE).select("patient_id", count="exact")
            if periodo is not None:
                q = q.eq("period", periodo)
            if sexo is not None:
                q = q.eq("sexo", sexo)
            if col is not None:
                q = q.eq(col, True)
            return q.execute().count or 0

        total = _contar()
        conteo = {nombre: _contar(col) for nombre, col in CRITERIOS_COLS.items()}
        pct = {n: round(c / total * 100, 1) if total else 0.0 for n, c in conteo.items()}
        return {"periodo": periodo, "sexo": sexo, "total": total, "conteo": conteo, "pct": pct}

    def obtener_missingness(self, periodo: str | None = None) -> dict:
        """Conteo (y %) de valores imputados por criterio (vía `imputed_flags`)."""

        def _contar(criterio: str | None = None) -> int:
            q = self.client.table(self.TABLE).select("patient_id", count="exact")
            if periodo is not None:
                q = q.eq("period", periodo)
            if criterio is not None:
                # Columna jsonb: el valor de contención debe ir como JSON string
                # (p. ej. '["perabd"]'); una lista de Python produciría sintaxis
                # de array de Postgres ('{perabd}'), inválida para jsonb.
                q = q.contains("imputed_flags", json.dumps([criterio]))
            return q.execute().count or 0

        total = _contar()
        conteo = {c: _contar(c) for c in CRITERIOS_IMPUTABLES}
        pct = {c: round(n / total * 100, 1) if total else 0.0 for c, n in conteo.items()}
        return {"periodo": periodo, "total": total, "imputados": conteo, "pct": pct}
