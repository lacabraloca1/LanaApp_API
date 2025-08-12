# app/models/transaction_model.py
from sqlalchemy import Column, Integer, Numeric, DateTime, String, ForeignKey, Enum
from datetime import datetime
from app.database import Base

class Transaction(Base):
    __tablename__ = "transacciones"

    id_transaccion  = Column(Integer, primary_key=True, index=True)
    id_usuario      = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    tipo            = Column(Enum('ingreso','egreso','envio','solicitud'), nullable=False)
    monto           = Column(Numeric(10, 2), nullable=False)
    fecha           = Column(DateTime, default=datetime.utcnow, nullable=False)
    descripcion     = Column(String, nullable=True)
    categoria_id    = Column(Integer, ForeignKey("categorias.id_categoria"), nullable=True)
    destinatario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    estado          = Column(Enum('pendiente','completada','cancelada'), default='completada', nullable=False)
