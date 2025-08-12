from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models.budget_model import Budget
from app.models.categoria_model import Categoria
from app.models.transaction_model import Transaction
from app.models.user_model import User
from app.utils.notificaciones import enviar_alerta_presupuesto

from datetime import datetime

router = APIRouter(tags=["Presupuestos"])

# ────── Esquemas ──────
class PresupuestoCrear(BaseModel):
    id_usuario: int
    id_categoria: int
    monto_mensual: float
    mes: int
    año: int

class PresupuestoRespuesta(BaseModel):
    id_presupuesto: int
    id_usuario: int
    id_categoria: int
    monto_mensual: float
    mes: int
    año: int

    class Config:
        orm_mode = True

def obtener_presupuesto_disponible(db: Session, id_usuario: int, categoria_id: int, fecha_ref: datetime) -> float:
    from sqlalchemy import func
    mes = fecha_ref.month
    anio = fecha_ref.year

    presupuesto = db.query(Budget).filter(
        Budget.id_usuario == id_usuario,
        Budget.id_categoria == categoria_id,
        Budget.mes == mes,
        Budget.año == anio
    ).first()

    if not presupuesto:
        # Si no hay presupuesto definido, interpretamos "sin límite"
        return float('inf')

    total_egresado = (
        db.query(func.sum(Transaction.monto))
        .filter(
            Transaction.id_usuario == id_usuario,
            Transaction.categoria_id == categoria_id,
            Transaction.tipo == "egreso",
            func.extract("month", Transaction.fecha) == mes,
            func.extract("year", Transaction.fecha) == anio,
        )
        .scalar()
    ) or 0

    return float(presupuesto.monto_mensual) - float(total_egresado)

# ────── Crear ──────
@router.post("/presupuestos", response_model=PresupuestoRespuesta)
def crear_presupuesto(data: PresupuestoCrear, db: Session = Depends(get_db)):
    existente = db.query(Budget).filter(
        Budget.id_usuario == data.id_usuario,
        Budget.id_categoria == data.id_categoria,
        Budget.mes == data.mes,
        Budget.año == data.año
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un presupuesto para este usuario, categoría y mes.")

    nuevo = Budget(**data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ────── Obtener todos ──────
@router.get("/presupuestos", response_model=List[PresupuestoRespuesta])
def listar_presupuestos(
    id_usuario: int = Query(...),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return db.query(Budget).filter(Budget.id_usuario == id_usuario).offset(skip).limit(limit).all()

# ────── Actualizar ──────
@router.put("/presupuestos/{id_presupuesto}", response_model=PresupuestoRespuesta)
def actualizar_presupuesto(id_presupuesto: int, data: PresupuestoCrear, db: Session = Depends(get_db)):
    presupuesto = db.query(Budget).filter(Budget.id_presupuesto == id_presupuesto).first()
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    for key, value in data.dict().items():
        setattr(presupuesto, key, value)

    db.commit()
    db.refresh(presupuesto)
    return presupuesto

# ────── Verificación automática de exceso de presupuesto ──────
@router.get("/presupuestos/verificar-alertas")
def verificar_alertas_presupuesto(
    id_usuario: int = Query(...),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    from sqlalchemy import func
    from app.models.categoria_model import Categoria

    hoy = datetime.now()
    mes = hoy.month
    año = hoy.year

    presupuestos = db.query(Budget).filter(
        Budget.id_usuario == id_usuario,
        Budget.mes == mes,
        Budget.año == año
    ).all()

    usuario = db.query(User).filter(User.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for presupuesto in presupuestos:
        total_gastado = (
            db.query(func.sum(Transaction.monto))
            .filter(
                Transaction.id_usuario == id_usuario,
                Transaction.categoria_id == presupuesto.id_categoria,
                Transaction.tipo == "egreso",
                func.extract("month", Transaction.fecha) == mes,
                func.extract("year", Transaction.fecha) == año,
            )
            .scalar()
        ) or 0

        categoria_nombre = (
            db.query(Categoria.nombre)
            .filter(Categoria.id_categoria == presupuesto.id_categoria)
            .scalar()
        ) or "Sin categoría"

        porcentaje = (total_gastado / presupuesto.monto_mensual) * 100 if presupuesto.monto_mensual else 0

        if porcentaje >= 100 or porcentaje >= 80:
            enviar_alerta_presupuesto(usuario.correo, categoria_nombre, float(total_gastado), float(porcentaje))

    return {"mensaje": "Verificación completada"}

# ────── Eliminar ──────
@router.delete("/presupuestos/{id_presupuesto}")
def eliminar_presupuesto(id_presupuesto: int, db: Session = Depends(get_db)):
    presupuesto = db.query(Budget).filter(Budget.id_presupuesto == id_presupuesto).first()
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    db.delete(presupuesto)
    db.commit()
    return {"mensaje": "Presupuesto eliminado correctamente"}
