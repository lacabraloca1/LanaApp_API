from sqlalchemy import Column, Integer, Numeric, ForeignKey
from app.database import Base

class Budget(Base):
    __tablename__ = "presupuestos"

    id_presupuesto = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"))
    monto_mensual = Column(Numeric(10, 2))
    mes = Column(Integer)
    año = Column(Integer)
