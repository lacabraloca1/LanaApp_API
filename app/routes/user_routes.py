from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import re

from app.database import SessionLocal
from app.models.user_model import User

router = APIRouter(tags=["Usuarios"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UsuarioCrear(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    nombre: str
    correo: EmailStr
    telefono: str
    contrasena: str = Field(alias='contraseña')

    @field_validator("contrasena")
    @classmethod
    def validar_password_fuerte(cls, v: str):
        if len(v) < 10:
            raise ValueError("La contraseña debe tener al menos 10 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Incluye al menos una letra MAYÚSCULA")
        if not re.search(r"[a-z]", v):
            raise ValueError("Incluye al menos una letra minúscula")
        if not re.search(r"\d", v):
            raise ValueError("Incluye al menos un número")
        if not re.search(r"[^\w\s]", v):
            raise ValueError("Incluye al menos un símbolo (p. ej. !@#$%)")
        if re.search(r"\s", v):
            raise ValueError("La contraseña no debe contener espacios")
        return v

class UsuarioLogin(BaseModel):
    correo: EmailStr
    contrasena: str

class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_usuario: int
    nombre: str
    correo: EmailStr
    telefono: str
    saldo: float

def obtener_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/usuarios/registrar", response_model=UsuarioRespuesta)
def registrar(usuario: UsuarioCrear, db: Session = Depends(obtener_db)):
    correo_norm = usuario.correo.lower().strip()
    tel_norm = usuario.telefono.strip()
    nombre_norm = usuario.nombre.strip()

    # Evitar contraseñas parecidas a correo/nombre
    local_mail = correo_norm.split("@")[0]
    if local_mail and local_mail.lower() in usuario.contrasena.lower():
        raise HTTPException(status_code=400, detail="La contraseña no debe contener tu correo")
    if nombre_norm and nombre_norm.lower() in usuario.contrasena.lower():
        raise HTTPException(status_code=400, detail="La contraseña no debe contener tu nombre")

    existente = db.query(User).filter(
        (User.correo == correo_norm) | (User.telefono == tel_norm)
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Correo o teléfono ya están registrados")

    hash_contrasena = pwd_context.hash(usuario.contrasena)

    nuevo = User(
        nombre=nombre_norm,
        correo=correo_norm,
        telefono=tel_norm,
        contrasena_hash=hash_contrasena,
        saldo=0.0
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.post("/usuarios/login", response_model=UsuarioRespuesta)
def login(datos: UsuarioLogin, db: Session = Depends(obtener_db)):
    usuario = db.query(User).filter(User.correo == datos.correo.lower().strip()).first()
    if not usuario or not pwd_context.verify(datos.contrasena, usuario.contrasena_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return usuario

@router.get("/usuarios/{id_usuario}", response_model=UsuarioRespuesta)
def obtener_usuario(id_usuario: int, db: Session = Depends(obtener_db)):
    usuario = db.query(User).filter(User.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
