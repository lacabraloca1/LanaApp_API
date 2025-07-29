from sqlalchemy import Column, Integer, String, DateTime, Numeric
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    correo = Column(String(255), unique=True, nullable=False)
    telefono = Column(String(20), unique=True, nullable=False)
    contraseña_hash = Column(String(255), nullable=False)
    pin_seguridad = Column(String(10), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    saldo = Column(Numeric(10, 2), default=0.00)
