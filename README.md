# MetSyn Dashboard — GICC · USIL 2026

Dashboard interactivo para monitoreo de Síndrome Metabólico en la comunidad universitaria USIL.

## Arranque rápido

```bash
# 1. Clonar y entrar al repo
git clone <url> metsyn && cd metsyn

# 2. Crear entornos Conda
conda env create -f environment.yml        # backend + ETL
conda env create -f environment-ml.yml     # ML e inferencia

# 3. Activar y descargar datos
conda activate metsyn-backend
dvc pull                                   # descarga data/raw desde el remote

# 4. Levantar el backend
cd backend && uvicorn main:app --reload

# 5. Levantar el frontend (otra terminal)
cd frontend && npm install && npm run dev
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | FastAPI hexagonal (dominio, puertos, adaptadores, rutas) |
| `ml/` | Pipeline DVC: ETL, imputación, entrenamiento, evaluación |
| `frontend/` | React + Shadcn/ui + Apache ECharts |
| `data/` | Gestionado por DVC — nunca commitear directamente |
| `models/` | Modelos serializados — gestionado por DVC |

## Stack

- **Backend:** FastAPI + Pydantic v2 + Supabase + Redis
- **ETL:** pandas + Great Expectations + Pandera
- **ML:** XGBoost / RandomForest + SHAP + LIME
- **Frontend:** React + Vite + Shadcn/ui + Apache ECharts + TanStack
- **Infra:** AWS EC2 + Gunicorn + Route53 (gicc.ai)
