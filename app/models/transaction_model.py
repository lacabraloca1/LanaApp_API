from sqlalchemy import Column, Integer, Numeric, DateTime, String, ForeignKey, Enum, Date
from datetime import datetime
from app.database import Base

class Transaction(Base):
    __tablename__ = "transacciones"

    id_transaccion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    tipo = Column(Enum('ingreso', 'egreso', 'envio', 'solicitud'))
    monto = Column(Numeric(10, 2))
    fecha = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(String, nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=True)
    destinatario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    estado = Column(Enum('pendiente', 'completada', 'cancelada'), default='completada')
    frecuencia = Column(String, default="única vez")
    fecha_fin = Column(Date, nullable=True)
