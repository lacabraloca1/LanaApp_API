from pydantic import BaseModel
from datetime import datetime

class PagoCreate(BaseModel):
    id_usuario: int
    descripcion: str
    monto: float
    fecha_programada: datetime

class PagoResponse(BaseModel):
    id_pago: int
    id_usuario: int
    descripcion: str
    monto: float
    fecha_programada: datetime

    class Config:
        orm_mode = True
