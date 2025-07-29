from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.budget_model import Budget
from app.schemas.budget_schema import BudgetCreate, BudgetResponse
from app.database import get_db

router = APIRouter()

@router.post("/presupuestos/crear", response_model=BudgetResponse)
def crear_presupuesto(budget: BudgetCreate, db: Session = Depends(get_db)):
    nuevo = Budget(**budget.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/presupuestos", response_model=List[BudgetResponse])
def obtener_presupuestos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Budget).offset(skip).limit(limit).all()

@router.get("/presupuestos/{id}", response_model=BudgetResponse)
def obtener_presupuesto(id: int, db: Session = Depends(get_db)):
    presupuesto = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return presupuesto

@router.put("/presupuestos/{id}", response_model=BudgetResponse)
def actualizar_presupuesto(id: int, data: BudgetCreate, db: Session = Depends(get_db)):
    presupuesto = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    for key, value in data.dict().items():
        setattr(presupuesto, key, value)
    db.commit()
    db.refresh(presupuesto)
    return presupuesto

@router.delete("/presupuestos/{id}")
def eliminar_presupuesto(id: int, db: Session = Depends(get_db)):
    presupuesto = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    db.delete(presupuesto)
    db.commit()
    return {"detail": "Presupuesto eliminado"}
