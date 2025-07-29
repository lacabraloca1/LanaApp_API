from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List ,Optional
from sqlalchemy.exc import IntegrityError
from app.models.categoria_model import Categoria
from app.schemas.categoria_schema import CategoriaCreate, CategoriaResponse
from app.database import get_db

router = APIRouter()

@router.post("/categorias/crear", response_model=CategoriaResponse)
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    existente = (
        db.query(Categoria)
          .filter(Categoria.nombre == categoria.nombre.strip())
          .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"La categoría '{categoria.nombre}' ya existe."
        )

    nueva = Categoria(**categoria.dict())
    db.add(nueva)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"La categoría '{categoria.nombre}' ya existe."
        )

    db.refresh(nueva)
    return nueva

@router.get("/categorias", response_model=List[CategoriaResponse])
def obtener_categorias(
    tipo: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    q = db.query(Categoria)
    if tipo:
        q = q.filter(Categoria.tipo == tipo.lower().strip())
    return q.offset(skip).limit(limit).all()

@router.get("/categorias/{id}", response_model=CategoriaResponse)
def obtener_categoria(id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    return cat

@router.put("/categorias/{id}", response_model=CategoriaResponse)
def actualizar_categoria(id: int, data: CategoriaCreate, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    cat.nombre = data.nombre
    cat.tipo = data.tipo
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categorias/{id}")
def eliminar_categoria(id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    db.delete(cat)
    db.commit()
    return {"detail": "Categoría eliminada correctamente"}
