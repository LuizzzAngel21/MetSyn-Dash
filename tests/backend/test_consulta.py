"""
Tests de los endpoints de consulta (Sprint 3). El repositorio se MOCKEA con
monkeypatch sobre `api.routes_consulta.get_repositorio`: no se toca Supabase ni
la red — sólo se verifica el cableado HTTP ↔ puerto.
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class _FakeRepo:
    def obtener_prevalencia(self, periodo=None, sexo=None):
        return {"periodo": periodo, "sexo": sexo, "total": 10, "positivos": 3,
                "prevalencia_pct": 30.0}

    def obtener_criterios(self, periodo=None, sexo=None):
        return {"periodo": periodo, "sexo": sexo, "total": 10,
                "conteo": {"perabd": 5}, "pct": {"perabd": 50.0}}

    def obtener_missingness(self, periodo=None):
        return {"periodo": periodo, "total": 10, "imputados": {"perabd": 2},
                "pct": {"perabd": 20.0}}

    def obtener_tendencias(self, sexo=None):
        return {"sexo": sexo, "serie": [{"period": "2021", "prevalencia_pct": 30.0}]}

    def obtener_registros(self, page=1, page_size=50, **filtros):
        return {"page": page, "page_size": page_size, "total": 0,
                "items": [], "filtros": filtros}


@pytest.fixture(autouse=True)
def _mock_repo(monkeypatch):
    monkeypatch.setattr("api.routes_consulta.get_repositorio", lambda: _FakeRepo())


def test_prevalencia_pasa_filtros():
    resp = client.get("/api/prevalencia", params={"period": "2021", "sexo": "M"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["periodo"] == "2021"
    assert body["sexo"] == "M"
    assert body["prevalencia_pct"] == 30.0


def test_criterios_responde():
    resp = client.get("/api/criterios", params={"period": "2021"})
    assert resp.status_code == 200
    assert resp.json()["conteo"]["perabd"] == 5


def test_missingness_responde():
    resp = client.get("/api/missingness")
    assert resp.status_code == 200
    assert resp.json()["pct"]["perabd"] == 20.0


def test_tendencias_responde():
    resp = client.get("/api/tendencias", params={"sexo": "F"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sexo"] == "F"
    assert body["serie"][0]["period"] == "2021"


def test_registros_pagina_y_filtra():
    resp = client.get("/api/registros", params={"page": 2, "page_size": 25, "period": "2024"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["page_size"] == 25
    assert body["filtros"]["period"] == "2024"


def test_registros_valida_page_size():
    # page_size fuera de rango (>200) -> 422 por validación de FastAPI.
    resp = client.get("/api/registros", params={"page_size": 999})
    assert resp.status_code == 422
