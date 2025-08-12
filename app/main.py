from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import Base, engine
from app.routes.user_routes import router as user_router
from app.routes.transaction_routes import router as transaction_router
from app.routes.categoria_routes import router as categoria_router
from app.routes.presupuestos_routes import router as presupuesto_router
from app.routes.pago_routes import router as pago_router
from app.routes.estadisticas_routes import router as estadistica_router
from app.routes import resumen_routes
from app.cron_jobs import iniciar_cron_jobs  

app = FastAPI(
    title="API de Finanzas Personales",
    description="Backend completo para gestionar usuarios, transacciones, presupuestos, pagos y estadísticas.",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_credentials=False,     
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(user_router, tags=["Usuarios"])
app.include_router(transaction_router, tags=["Transacciones"])
app.include_router(categoria_router, tags=["Categorías"])
app.include_router(presupuesto_router, tags=["Presupuestos"])
app.include_router(pago_router, tags=["Pagos"])
app.include_router(estadistica_router, tags=["Estadísticas"])
app.include_router(resumen_routes.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def _startup():
    """
    Inicia los cron jobs solo si ENABLE_CRON=1 (por defecto 1).
    Evita iniciar múltiples schedulers en servidores con varios workers
    controlándolo con la env var a nivel del proceso que quieras que los corra.
    """
    if os.environ.get("ENABLE_CRON", "1") == "1":
        iniciar_cron_jobs()
