from pydantic import BaseModel
from typing import Literal

class CategoriaCreate(BaseModel):
    nombre: str
    tipo: Literal["ingreso", "egreso"]

class CategoriaResponse(BaseModel):
    id_categoria: int
    nombre: str
    tipo: str

    class Config:
        orm_mode = True
