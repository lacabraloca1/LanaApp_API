from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Enum, Boolean
from datetime import datetime
from app.database import Base

class PagoFijo(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    descripcion = Column(String, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha_programada = Column(DateTime, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=True)
    periodicidad = Column(Enum('none', 'weekly', 'monthly'), nullable=False, default='none')
    proxima_ejecucion = Column(Date, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
