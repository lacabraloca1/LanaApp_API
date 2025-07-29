from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import List
from app.models.transaction_model import Transaction
from app.models.user_model import User
from app.models.categoria_model import Categoria
from app.models.budget_model import Budget

from app.schemas.transaction_schema import (
    IngresoCreate, EgresoCreate,
    TransaccionUpdate, TransaccionResponse
)
from app.database import get_db

router = APIRouter()

# ——————— INGRESOS ———————
@router.post("/ingresos/crear", response_model=TransaccionResponse)
def crear_ingreso(transaction: IngresoCreate, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id_usuario == transaction.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    categoria = db.query(Categoria).filter(Categoria.nombre == transaction.descripcion).first()
    if not categoria:
        categoria = Categoria(nombre=transaction.descripcion, tipo="ingreso")
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

    monto = Decimal(transaction.monto)
    db_transaction = Transaction(
        id_usuario=transaction.id_usuario,
        tipo="ingreso",
        monto=monto,
        descripcion=transaction.descripcion,
        categoria_id=categoria.id_categoria,
        estado="completada"
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    usuario.saldo = (usuario.saldo or Decimal("0.00")) + monto
    db.commit()

    return db_transaction


# ——————— EGRESOS ———————
@router.post("/egresos/crear", response_model=TransaccionResponse)
def crear_egreso(transaction: EgresoCreate, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id_usuario == transaction.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    monto = Decimal(transaction.monto)
    if (usuario.saldo or Decimal("0.00")) < monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente.")

    categoria = db.query(Categoria).filter(Categoria.nombre == transaction.descripcion).first()
    if not categoria:
        categoria = Categoria(nombre=transaction.descripcion, tipo="egreso")
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

    db_transaction = Transaction(
        id_usuario=transaction.id_usuario,
        tipo="egreso",
        monto=monto,
        descripcion=transaction.descripcion,
        categoria_id=categoria.id_categoria,
        estado="completada"
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    usuario.saldo -= monto
    db.commit()

    # Verificación de presupuesto excedido
    presupuesto = db.query(Budget).filter(
        Budget.id_usuario == transaction.id_usuario,
        Budget.id_categoria == categoria.id_categoria,
        Budget.mes == datetime.utcnow().month,
        Budget.año == datetime.utcnow().year
    ).first()

    if presupuesto and monto > presupuesto.monto_mensual:
        print(f"[ALERTA] Presupuesto excedido para {categoria.nombre}")

    return db_transaction


# ——————— CRUD Transacciones ———————
@router.get("/transacciones", response_model=List[TransaccionResponse])
def obtener_todas(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Transaction).offset(skip).limit(limit).all()

@router.get("/transacciones/{id_usuario}", response_model=List[TransaccionResponse])
def obtener_por_usuario(id_usuario: int, db: Session = Depends(get_db)):
    transacciones = db.query(Transaction).filter(Transaction.id_usuario == id_usuario).order_by(Transaction.fecha.desc()).all()
    if not transacciones:
        raise HTTPException(status_code=404, detail="No se encontraron transacciones.")
    return transacciones

@router.put("/transacciones/{id}", response_model=TransaccionResponse)
def actualizar_transaccion(id: int, t: TransaccionUpdate, db: Session = Depends(get_db)):
    trans = db.query(Transaction).filter(Transaction.id_transaccion == id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transacción no encontrada.")

    usuario = db.query(User).filter(User.id_usuario == t.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    diferencia = Decimal(t.monto) - trans.monto
    if trans.tipo == "ingreso":
        usuario.saldo += diferencia
    elif trans.tipo == "egreso":
        usuario.saldo -= diferencia

    trans.monto = Decimal(t.monto)
    trans.descripcion = t.descripcion
    db.commit()
    db.refresh(trans)

    return trans

@router.delete("/transacciones/{id}")
def eliminar_transaccion(id: int, db: Session = Depends(get_db)):
    trans = db.query(Transaction).filter(Transaction.id_transaccion == id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transacción no encontrada.")
    db.delete(trans)
    db.commit()
    return {"detail": "Transacción eliminada"}
