"""FastAPI entry point — MetSyn Dashboard."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MetSyn Dashboard API",
    description="API para monitoreo de Síndrome Metabólico — GICC · USIL",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers. La ingesta se activa en Sprint 1; consulta/predicción en S3/S5.
from api.routes_ingesta import router as ingesta_router

app.include_router(ingesta_router, prefix="/api")
# from api.routes_consulta import router as consulta_router      # Sprint 3
# from api.routes_prediccion import router as prediccion_router  # Sprint 5
# app.include_router(consulta_router, prefix="/api")
# app.include_router(prediccion_router, prefix="/api")


@app.get("/api/health")
def health():
    """Healthcheck — confirma que el servidor responde."""
    return {"status": "ok", "service": "metsyn-api"}
