"""Tests del endpoint POST /api/ingesta/upload (Sprint 1 DoD)."""
import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

COLUMNAS = [
    "ID2", "sexo", "edad", "perabd", "trig", "hdl",
    "glu", "presion_sis", "presion_dia", "presionarterial",
]


def _excel(columnas, periodo="2021") -> bytes:
    df = pd.DataFrame(
        [
            [533, "M", 40, 95, 160, 35, 105, 135, 80, "135/80 mmHg."],
            [611, "FEMENINO", 35, 75, 140, 55, 90, 120, 70, "120/70 mmHg."],
        ],
        columns=COLUMNAS,
    )[columnas]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, sheet_name=periodo, index=False)
    return buf.getvalue()


def test_upload_excel_valido_calcula_metsyn(monkeypatch):
    # Mock del repositorio: no se toca Supabase en los tests.
    class _FakeRepo:
        def upsert_registros(self, df, periodo):
            return len(df)

    monkeypatch.setattr("api.routes_ingesta.get_repositorio", lambda: _FakeRepo())

    data = _excel(COLUMNAS)
    resp = client.post(
        "/api/ingesta/upload",
        files={"file": ("ok.xlsx", data,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["total_registros"] == 2
    assert body["por_periodo"][0]["period"] == "2021"
    # Persistencia real (Sprint 2): el repo mockeado confirma 2 filas upserteadas.
    assert body["persistencia"]["estado"] == "ok"
    assert body["persistencia"]["filas_insertadas"] == 2


def test_upload_excel_invalido_se_rechaza_con_html():
    # Falta la columna obligatoria 'hdl' -> la suite estructural debe fallar.
    cols = [c for c in COLUMNAS if c != "hdl"]
    data = _excel(cols)
    resp = client.post(
        "/api/ingesta/upload",
        files={"file": ("bad.xlsx", data,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 422
    assert "text/html" in resp.headers["content-type"]
    assert "metsyn_estructural" in resp.text


def test_upload_rechaza_no_excel():
    resp = client.post(
        "/api/ingesta/upload",
        files={"file": ("data.csv", b"a,b,c", "text/csv")},
    )
    assert resp.status_code == 400
