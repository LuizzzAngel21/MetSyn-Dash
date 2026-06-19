"""
POST /api/ingesta/upload — recibe un Excel y ejecuta el ETL de ingesta.

Orquesta el pipeline hexagonal sobre cada hoja (período) del archivo:

    ingesta (leer) → validación (GE, PUERTA) → limpieza → imputación (KNN)
        → features (reglas ATP-III del dominio)

Un archivo que falla la suite estructural se rechaza con HTTP 422 y el reporte
HTML de Great Expectations. Un archivo válido se procesa de punta a punta y
devuelve el resumen de `metsyn_flag` por período.

La PERSISTENCIA en Supabase es Sprint 2: si el RepositorioPort aún no está
implementado, la respuesta lo indica explícitamente (`persistencia: pendiente`).
"""
from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from adapters._paths import REPO_ROOT  # noqa: F401  (raíz del repo en sys.path)
from adapters.ge_validator import ValidacionError
from api.deps import get_imputacion, get_ingesta, get_repositorio, get_validacion
from domain.atp3 import calcular_flags
from ml.clean import limpiar_df

router = APIRouter(tags=["ingesta"])


@router.post("/ingesta/upload")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Se espera un archivo Excel (.xlsx/.xls)")

    ingesta = get_ingesta()
    validador = get_validacion()
    imputador = get_imputacion()

    # Leer el upload en memoria (BytesIO) — sin archivos temporales ni bloqueos
    # de Windows. Un único ExcelFile se reutiliza para todas las hojas.
    contenido = await file.read()
    xls = pd.ExcelFile(io.BytesIO(contenido))

    try:
        resumen: list[dict] = []
        featured_por_periodo: dict[str, pd.DataFrame] = {}
        total = 0
        for periodo in xls.sheet_names:
            crudo = ingesta.leer_excel(xls, periodo)

            # PUERTA de calidad: estructura/dominio. Falla -> 422 con HTML de GE.
            try:
                validador.validar(crudo, periodo)
            except ValidacionError as e:
                return HTMLResponse(content=e.html, status_code=422)

            limpio = limpiar_df(crudo)
            imputado, _meta = imputador.imputar(limpio)
            featured = calcular_flags(imputado)
            featured_por_periodo[periodo] = featured

            n = len(featured)
            total += n
            resumen.append(
                {
                    "period": periodo,
                    "registros": n,
                    "metsyn_positivos": int(featured["metsyn_flag"].sum()),
                    "prevalencia_pct": round(float(featured["metsyn_flag"].mean()) * 100, 1),
                }
            )

        # Persistencia (Sprint 2): upsert real en Supabase por período.
        try:
            repo = get_repositorio()
            persistidos = sum(
                repo.upsert_registros(featured_por_periodo[p["period"]], p["period"])
                for p in resumen
            )
            persistencia = {"estado": "ok", "filas_insertadas": persistidos}
        except NotImplementedError:
            persistencia = {"estado": "pendiente", "sprint": 2}

        return {
            "status": "ok",
            "archivo": file.filename,
            "total_registros": total,
            "por_periodo": resumen,
            "persistencia": persistencia,
        }
    finally:
        xls.close()
