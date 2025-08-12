from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.categoria_model import Categoria

router = APIRouter(tags=["Categorías"])

# ────── Esquemas ──────
class CategoriaCrear(BaseModel):
    nombre: str
    tipo: str  # ingreso, egreso, otro

class CategoriaRespuesta(BaseModel):
    id_categoria: int
    nombre: str
    tipo: str

    class Config:
        orm_mode = True

# ────── Crear ──────
@router.post("/categorias", response_model=CategoriaRespuesta)
def crear_categoria(data: CategoriaCrear, db: Session = Depends(get_db)):
    existente = db.query(Categoria).filter(Categoria.nombre == data.nombre.strip()).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"La categoría '{data.nombre}' ya existe.")
    
    nueva = Categoria(nombre=data.nombre.strip(), tipo=data.tipo.strip().lower())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

# ────── Obtener todas ──────
@router.get("/categorias", response_model=List[CategoriaRespuesta])
def listar_categorias(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: ingreso, egreso"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Categoria)
    if tipo:
        query = query.filter(Categoria.tipo == tipo.lower().strip())
    return query.offset(skip).limit(limit).all()

# ────── Obtener una ──────
@router.get("/categorias/{id_categoria}", response_model=CategoriaRespuesta)
def obtener_categoria(id_categoria: int, db: Session = Depends(get_db)):
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    return categoria

# ────── Actualizar ──────
@router.put("/categorias/{id_categoria}", response_model=CategoriaRespuesta)
def actualizar_categoria(id_categoria: int, data: CategoriaCrear, db: Session = Depends(get_db)):
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    
    categoria.nombre = data.nombre.strip()
    categoria.tipo = data.tipo.strip().lower()
    db.commit()
    db.refresh(categoria)
    return categoria

# ────── Eliminar ──────
@router.delete("/categorias/{id_categoria}")
def eliminar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    db.delete(categoria)
    db.commit()
    return {"mensaje": "Categoría eliminada correctamente"}