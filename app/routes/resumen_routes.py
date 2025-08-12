from fastapi import APIRouter, HTTPException ,Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal , get_db
from app.models.transaction_model import Transaction


router = APIRouter(prefix="/resumen", tags=["Resumen"])

@router.get("/{id_usuario}")
def get_resumen(id_usuario: int, db: Session = Depends(get_db)):
    from sqlalchemy import func

    ingresos = (
        db.query(func.sum(Transaction.monto))
          .filter(Transaction.id_usuario == id_usuario, Transaction.tipo == "ingreso")
          .scalar()
    ) or 0
    egresos = (
        db.query(func.sum(Transaction.monto))
          .filter(Transaction.id_usuario == id_usuario, Transaction.tipo == "egreso")
          .scalar()
    ) or 0
    return {
        "id_usuario": id_usuario,
        "ingresos": float(ingresos),
        "egresos": float(egresos),
        "balance": float(ingresos) - float(egresos),
    }
    