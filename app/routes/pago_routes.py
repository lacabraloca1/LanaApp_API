from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.models.pago_model import Pago
from app.models.user_model import User
from app.schemas.pago_schema import PagoCreate, PagoResponse
from app.database import get_db

router = APIRouter()

@router.post("/pagos/crear", response_model=PagoResponse)
def crear_pago(pago: PagoCreate, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id_usuario == pago.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    nuevo_pago = Pago(
        id_usuario=pago.id_usuario,
        descripcion=pago.descripcion,
        monto=Decimal(pago.monto),
        fecha_programada=pago.fecha_programada
    )
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago

@router.get("/pagos", response_model=List[PagoResponse])
def obtener_pagos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Pago).offset(skip).limit(limit).all()

@router.get("/pagos/{id}", response_model=PagoResponse)
def obtener_pago(id: int, db: Session = Depends(get_db)):
    pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    return pago

@router.put("/pagos/{id}", response_model=PagoResponse)
def actualizar_pago(id: int, data: PagoCreate, db: Session = Depends(get_db)):
    pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    for key, value in data.dict().items():
        setattr(pago, key, value)
    db.commit()
    db.refresh(pago)
    return pago

@router.delete("/pagos/{id}")
def eliminar_pago(id: int, db: Session = Depends(get_db)):
    pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    db.delete(pago)
    db.commit()
    return {"detail": "Pago eliminado correctamente"}
