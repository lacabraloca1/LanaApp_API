from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate , UserLogin
from passlib.context import CryptContext
from app.models.user_model import User
from app.database import SessionLocal

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/registrar")
def registrar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    # Validar correo o teléfono duplicado
    usuario_existente = db.query(User).filter(
        (User.correo == usuario.correo) | (User.telefono == usuario.telefono)
    ).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El correo o teléfono ya están registrados.")

    # Hashear la contraseña
    hashed_password = pwd_context.hash(usuario.contraseña)

    # Crear usuario usando los campos necesarios manualmente
    nuevo_usuario = User(
        nombre=usuario.nombre,
        correo=usuario.correo,
        telefono=usuario.telefono,
        contraseña_hash=hashed_password,
        pin_seguridad=None,          # puedes cambiar esto si luego lo pides
        saldo=0.00                   # saldo inicial
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return {"mensaje": "Usuario registrado correctamente"}

@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id_usuario == id_usuario).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    return {
        "id_usuario": user.id_usuario,
        "nombre": user.nombre,
        "correo": user.correo,
        "telefono": user.telefono,
        "saldo": user.saldo,
        "url_perfil": user.url_perfil or None,   # opcional
    }

@router.post("/login")
def login_usuario(credentials: UserLogin, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.correo == credentials.correo).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not pwd_context.verify(credentials.contraseña, usuario.contraseña_hash):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    return {
        "mensaje": "Login exitoso",
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "telefono": usuario.telefono,
            "saldo": usuario.saldo
        }
    }