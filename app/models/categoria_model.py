from sqlalchemy import Column, Integer, String, Enum
from app.database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    tipo = Column(Enum('ingreso', 'egreso'), nullable=False)
