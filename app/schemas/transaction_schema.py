from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class IngresoCreate(BaseModel):
    id_usuario: int
    monto: float
    descripcion: str

class EgresoCreate(BaseModel):
    id_usuario: int
    monto: float
    descripcion: str

class TransaccionUpdate(BaseModel):
    id_usuario: int
    monto: float
    descripcion: str
    
class TransaccionResponse(BaseModel):
    id_transaccion: int
    id_usuario: int
    tipo: str
    monto: float
    descripcion: str
    categoria_id: int
    estado: str
    fecha: datetime 

    class Config:
        orm_mode = True
