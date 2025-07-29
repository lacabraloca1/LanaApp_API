from fastapi import FastAPI
from app.database import Base, engine
from app.routes import user_routes
from app.routes import transaction_routes
from app.routes import categoria_routes
from app.routes import budget_routes
from app.routes import pago_routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Crea las tablas
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rutas
app.include_router(user_routes.router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(transaction_routes.router, prefix="/api", tags=["Transacciones"])
app.include_router(categoria_routes.router, prefix="/api", tags=["Categorías"])
app.include_router(budget_routes.router, prefix="/api", tags=["Presupuestos"])
app.include_router(pago_routes.router, prefix="/api", tags=["Pagos"])