from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    descripcion = Column(String, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha_programada = Column(DateTime, nullable=False)
