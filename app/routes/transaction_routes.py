from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.transaction_model import Transaction
from app.models.user_model import User
from app.models.categoria_model import Categoria
from app.models.budget_model import Budget
from app.utils.notificaciones import enviar_correo 

router = APIRouter(tags=["Transacciones"])

# ────── Esquemas ──────
class IngresoCrear(BaseModel):
    id_usuario: int
    monto: float
    descripcion: str
    categoria_id: Optional[int] = None   # 👈 nuevo

class EgresoCrear(BaseModel):
    id_usuario: int
    monto: float
    descripcion: str
    categoria_id: Optional[int] = None
    
class TransaccionActualizar(BaseModel):
    id_usuario: int
    monto: float
    descripcion: str

class TransaccionRespuesta(BaseModel):
    id_transaccion: int
    id_usuario: int
    tipo: str
    monto: float
    descripcion: str
    categoria_id: Optional[int]
    estado: str
    fecha: datetime

    class Config:
        orm_mode = True

def obtener_o_crear_categoria(db: Session, nombre: str, tipo: str) -> Categoria:
    nombre = (nombre or "").strip()
    cat = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if not cat:
        cat = Categoria(nombre=nombre, tipo=tipo)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat

# ────── INGRESOS ──────
@router.post("/transacciones/ingreso", response_model=TransaccionRespuesta)
def crear_ingreso(data: IngresoCrear, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id_usuario == data.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if data.categoria_id:
        categoria = db.query(Categoria).filter(Categoria.id_categoria == data.categoria_id).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    else:
        categoria = obtener_o_crear_categoria(db, data.descripcion, "ingreso")

    monto = Decimal(data.monto)
    nueva = Transaction(
        id_usuario=data.id_usuario,
        tipo="ingreso",
        monto=monto,
        descripcion=data.descripcion,
        categoria_id=categoria.id_categoria,
        estado="completada"
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    usuario.saldo = (usuario.saldo or Decimal("0.00")) + monto
    db.commit()
    return nueva

# ────── EGRESOS ──────
@router.post("/transacciones/egreso", response_model=TransaccionRespuesta)
def crear_egreso(data: EgresoCrear, db: Session = Depends(get_db)):
    from datetime import datetime
    usuario = db.query(User).filter(User.id_usuario == data.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    monto = Decimal(data.monto)
    if (usuario.saldo or Decimal("0.00")) < monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente.")

    # Resolver categoría
    if data.categoria_id:
        categoria = db.query(Categoria).filter(Categoria.id_categoria == data.categoria_id).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoría no encontrada.")
        categoria_id = categoria.id_categoria
    else:
        categoria = obtener_o_crear_categoria(db, data.descripcion, "egreso")
        categoria_id = categoria.id_categoria

    # === Verificación de presupuesto previo ===
    try:
        # Import local para evitar dependencia circular si lo pusiste en presupuestos_routes
        from app.routes.presupuestos_routes import obtener_presupuesto_disponible
    except Exception:
        # Si moviste el helper a otro módulo, ajusta el import arriba.
        raise HTTPException(status_code=500, detail="No se pudo cargar verificador de presupuesto.")

    disponible = obtener_presupuesto_disponible(db, data.id_usuario, categoria_id, datetime.utcnow())
    if disponible < float(monto):
        faltante = float(monto) - disponible
        raise HTTPException(
            status_code=400,
            detail=f"Presupuesto insuficiente en la categoría. Faltan ${faltante:.2f} para cubrir este egreso."
        )

    # Crear transacción de egreso
    nueva = Transaction(
        id_usuario=data.id_usuario,
        tipo="egreso",
        monto=monto,
        descripcion=data.descripcion,
        categoria_id=categoria_id,
        estado="completada"
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    usuario.saldo -= monto
    db.commit()
    return nueva

# ────── CONSULTAR TRANSACCIONES ──────
@router.get("/transacciones", response_model=List[TransaccionRespuesta])
def obtener_todas(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Transaction).offset(skip).limit(limit).all()

@router.get("/transacciones/usuario/{id_usuario}", response_model=List[TransaccionRespuesta])
def obtener_por_usuario(
    id_usuario: int,
    tipo: Optional[str] = Query(None, description="Opcional: 'ingreso' o 'egreso'"),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.id_usuario == id_usuario)
    if tipo in ("ingreso", "egreso"):
        query = query.filter(Transaction.tipo == tipo)
    transacciones = query.order_by(Transaction.fecha.desc()).all()
    return transacciones

# ────── ACTUALIZAR ──────
@router.put("/transacciones/{id}", response_model=TransaccionRespuesta)
def actualizar(id: int, data: TransaccionActualizar, db: Session = Depends(get_db)):
    trans = db.query(Transaction).filter(Transaction.id_transaccion == id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transacción no encontrada.")

    usuario = db.query(User).filter(User.id_usuario == data.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    diferencia = Decimal(data.monto) - trans.monto
    if trans.tipo == "ingreso":
        usuario.saldo += diferencia
    elif trans.tipo == "egreso":
        usuario.saldo -= diferencia

    trans.monto = Decimal(data.monto)
    trans.descripcion = data.descripcion
    db.commit()
    db.refresh(trans)

    return trans

# ────── ELIMINAR ──────
@router.delete("/transacciones/{id}")
def eliminar(id: int, db: Session = Depends(get_db)):
    trans = db.query(Transaction).filter(Transaction.id_transaccion == id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transacción no encontrada.")
    db.delete(trans)
    db.commit()
    return {"mensaje": "Transacción eliminada correctamente"}

