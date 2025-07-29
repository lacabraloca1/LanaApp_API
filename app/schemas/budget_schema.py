from pydantic import BaseModel
from datetime import date

class BudgetCreate(BaseModel):
    id_usuario: int
    id_categoria: int
    monto_mensual: float
    mes: int
    año: int

class BudgetResponse(BaseModel):
    id_presupuesto: int
    id_usuario: int
    id_categoria: int
    monto_mensual: float
    mes: int
    año: int

    class Config:
        orm_mode = True
