from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from decimal import Decimal
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

# Configuración de la base de datos MySQL en Railway
DATABASE_URL = "mysql+pymysql://root:tzZfIAImhPszeqmloPtScAZShsGsaQWi@switchback.proxy.rlwy.net:37527/lana_app"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicialización de la aplicación FastAPI
app = FastAPI()

# Modelos de la base de datos
class User(Base):
    """
    Modelo para los usuarios registrados en la aplicación.
    """
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    correo = Column(String, unique=True, index=True)
    telefono = Column(String, unique=True)
    contraseña_hash = Column(String)
    pin_seguridad = Column(String, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    saldo = Column(Numeric(10, 2), default=0)  # Nuevo campo para manejar el saldo

class Transaction(Base):
    """
    Modelo para las transacciones realizadas por los usuarios.
    """
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

class Budget(Base):
    """
    Modelo para los presupuestos mensuales definidos por los usuarios.
    """
    __tablename__ = "presupuestos"
    id_presupuesto = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria"))
    monto_mensual = Column(Numeric(10, 2))
    mes = Column(Integer)
    año = Column(Integer)

class Categoria(Base):
    """
    Modelo para las categorías de ingresos y gastos.
    """
    __tablename__ = "categorias"
    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    tipo = Column(Enum('ingreso', 'egreso'), nullable=False)

class Pago(Base):
    """
    Modelo para los pagos fijos programados por los usuarios.
    """
    __tablename__ = "pagos"
    id_pago = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    descripcion = Column(String, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha_programada = Column(DateTime, nullable=False)

# Esquemas de Pydantic para validación de datos
class UserCreate(BaseModel):
    """
    Esquema para la creación de usuarios.
    """
    nombre: str
    correo: str
    telefono: str
    contraseña_hash: str

class TransactionCreate(BaseModel):
    """
    Esquema para la creación de transacciones.
    """
    id_usuario: int
    monto: float
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    destinatario_id: Optional[int] = None

class BudgetCreate(BaseModel):
    """
    Esquema para la creación de presupuestos.
    """
    id_usuario: int
    id_categoria: int
    monto_mensual: float
    mes: int
    año: int

class CategoriaCreate(BaseModel):
    """
    Esquema para la creación de categorías.
    """
    nombre: str
    tipo: str

class PagoCreate(BaseModel):
    """
    Esquema para la creación de pagos fijos.
    """
    id_usuario: int
    descripcion: str
    monto: float
    fecha_programada: datetime

class IngresoCreate(BaseModel):
    """
    Esquema para la creación de ingresos.
    """
    id_usuario: int
    monto: float
    descripcion: str


class EgresoCreate(BaseModel):
    """
    Esquema para la creación de egresos.
    """
    id_usuario: int
    monto: float
    descripcion: str


class TransaccionResponse(BaseModel):
    """
    Esquema para la respuesta de transacciones.
    """
    id_transaccion: int
    id_usuario: int
    tipo: str
    monto: float
    descripcion: str
    categoria_id: int
    estado: str

class TransaccionUpdate(BaseModel):
    """
    Esquema para actualizar transacciones.
    """
    id_usuario: int
    monto: float
    descripcion: str

class BudgetResponse(BaseModel):
    """
    Esquema para la respuesta de presupuestos.
    """
    id_presupuesto: int
    id_usuario: int
    id_categoria: int
    monto_mensual: float
    mes: int
    año: int

class CategoriaResponse(BaseModel):
    """
    Esquema para la respuesta de categorías.
    """
    id_categoria: int
    nombre: str
    tipo: str

class PagoResponse(BaseModel):
    """
    Esquema para la respuesta de pagos fijos.
    """
    id_pago: int
    id_usuario: int
    descripcion: str
    monto: float
    fecha_programada: datetime

class UserResponse(BaseModel):
    """
    Esquema para la respuesta de usuarios.
    """
    id_usuario: int
    nombre: str
    correo: str
    telefono: str
    saldo: float

# Dependencia para obtener la sesión de la base de datos
def get_db():
    """
    Obtiene una sesión de la base de datos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para enviar un mensaje SMS utilizando Twilio.
def enviar_sms(destinatario: str, mensaje: str):
    print(f"Enviando SMS a {destinatario} con el mensaje: {mensaje}")
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=mensaje,
            messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
            to=destinatario
        )
        print(f"SMS enviado exitosamente. SID: {message.sid}")
        return {"message": "SMS enviado exitosamente.", "sid": message.sid}
    except Exception as e:
        print(f"Error al enviar SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al enviar SMS: {str(e)}")

# Endpoints de la API

# Usuarios
@app.post("/usuarios/registrar", response_model=UserResponse, tags=["Usuarios"], description="Registrar un nuevo usuario.")
def registrar_usuario(user: UserCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para registrar un nuevo usuario.
    """
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/usuarios/login", tags=["Usuarios"], description="Iniciar sesión de usuario.")
def login_usuario(correo: str, contraseña: str, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para iniciar sesión de usuario.
    """
    usuario = db.query(User).filter(User.correo == correo, User.contraseña_hash == contraseña).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    return {"message": "Inicio de sesión exitoso", "usuario": usuario}


@app.get("/usuarios", response_model=List[UserResponse], tags=["Usuarios"], description="Obtener todos los usuarios.")
def obtener_usuarios(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todos los usuarios registrados.
    """
    usuarios = db.query(User).offset(skip).limit(limit).all()
    return usuarios


@app.get("/usuarios/{id}", response_model=UserCreate, tags=["Usuarios"], description="Obtener un usuario por ID.")
def obtener_usuario(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener un usuario específico por ID.
    """
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return usuario


@app.put("/usuarios/{id}", tags=["Usuarios"], description="Actualizar un usuario por ID.")
def actualizar_usuario(id: int, correo: Optional[str] = None, nueva_contraseña: Optional[str] = None, contraseña_actual: str = None, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para actualizar un usuario específico por ID.
    Valida la contraseña actual antes de realizar cambios.
    """
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Validar la contraseña actual
    if usuario.contraseña_hash != contraseña_actual:
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta.")

    # Actualizar correo y/o contraseña
    if correo:
        usuario.correo = correo
    if nueva_contraseña:
        usuario.contraseña_hash = nueva_contraseña

    db.commit()
    db.refresh(usuario)
    return {"message": "Usuario actualizado exitosamente.", "usuario": usuario}


# Eliminar un usuario por ID
@app.delete("/usuarios/{id}", tags=["Usuarios"], description="Eliminar un usuario por ID.")
def eliminar_usuario(id: int, contraseña: str, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para eliminar un usuario específico por ID.
    Valida la contraseña antes de eliminar el usuario.
    """
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Validar la contraseña
    if usuario.contraseña_hash != contraseña:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta.")

    db.delete(usuario)
    db.commit()
    return {"detail": "Usuario eliminado exitosamente."}


# Ingresos
@app.post("/ingresos/crear", response_model=TransaccionResponse, tags=["Ingresos"], description="Registrar un ingreso.")
def crear_ingreso(transaction: IngresoCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para registrar un ingreso.
    """
    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == transaction.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Verificar si la categoría existe
    categoria = db.query(Categoria).filter(Categoria.nombre == transaction.descripcion).first()
    if not categoria:
        nueva_categoria = Categoria(nombre=transaction.descripcion, tipo="ingreso")
        db.add(nueva_categoria)
        db.commit()
        db.refresh(nueva_categoria)
        categoria = nueva_categoria

    # Convertir transaction.monto a Decimal
    monto_decimal = Decimal(transaction.monto)

    # Crear la transacción
    db_transaction = Transaction(
        id_usuario=transaction.id_usuario,
        tipo="ingreso",
        monto=monto_decimal,
        descripcion=transaction.descripcion,
        categoria_id=categoria.id_categoria,
        estado="completada"
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    # Actualizar el saldo del usuario
    usuario.saldo = usuario.saldo + monto_decimal if usuario.saldo else monto_decimal
    db.commit()

    # Enviar SMS al usuario
    mensaje = f"Has recibido un ingreso de ${transaction.monto:.2f}. Descripción: {transaction.descripcion}. Tu saldo actual es de ${usuario.saldo:.2f}."
    enviar_sms(usuario.telefono, mensaje)

    return db_transaction


# Egresos
@app.post("/egresos/crear", response_model=TransaccionResponse, tags=["Egresos"], description="Registrar un egreso.")
def crear_egreso(transaction: EgresoCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para registrar un egreso.
    """
    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == transaction.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Verificar si el saldo es suficiente
    monto_decimal = Decimal(transaction.monto)  # Convertir monto a Decimal
    if usuario.saldo is None or usuario.saldo < monto_decimal:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para realizar el egreso.")

    # Verificar si la categoría existe
    categoria = db.query(Categoria).filter(Categoria.nombre == transaction.descripcion).first()
    if not categoria:
        nueva_categoria = Categoria(nombre=transaction.descripcion, tipo="egreso")
        db.add(nueva_categoria)
        db.commit()
        db.refresh(nueva_categoria)
        categoria = nueva_categoria

    # Crear la transacción
    db_transaction = Transaction(
        id_usuario=transaction.id_usuario,
        tipo="egreso",
        monto=monto_decimal,
        descripcion=transaction.descripcion,
        categoria_id=categoria.id_categoria,
        estado="completada"
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    # Actualizar el saldo del usuario
    usuario.saldo -= monto_decimal
    db.commit()

    # Enviar SMS al usuario
    mensaje = f"Has realizado un egreso de ${transaction.monto:.2f}. Descripción: {transaction.descripcion}. Tu saldo actual es de ${usuario.saldo:.2f}."
    enviar_sms(usuario.telefono, mensaje)

    # Verificar si el gasto excede el presupuesto
    presupuesto = db.query(Budget).filter(
        Budget.id_usuario == transaction.id_usuario,
        Budget.id_categoria == categoria.id_categoria,
        Budget.mes == datetime.utcnow().month,
        Budget.año == datetime.utcnow().year
    ).first()

    if presupuesto and monto_decimal > presupuesto.monto_mensual:
        mensaje = f"¡Atención! Has excedido tu presupuesto mensual de ${presupuesto.monto_mensual:.2f} para la categoría {categoria.nombre}."
        enviar_sms(usuario.telefono, mensaje)

    return db_transaction


# Transacciones

# Obtener todas las transacciones
@app.get("/transacciones", response_model=List[TransaccionResponse], tags=["Transacciones"], description="Obtener todas las transacciones de todos los usuarios.")
def obtener_transacciones(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todas las transacciones de todos los usuarios.
    """
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
    return transactions


# Obtener transacciones de un usuario específico
@app.get("/transacciones/{id_usuario}", response_model=List[TransaccionResponse], tags=["Transacciones"], description="Obtener todas las transacciones de un usuario específico.")
def obtener_transacciones_usuario(id_usuario: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todas las transacciones de un usuario específico, ordenadas de la más reciente a la más antigua.
    """
    transactions = db.query(Transaction).filter(Transaction.id_usuario == id_usuario).order_by(Transaction.fecha.desc()).all()
    if not transactions:
        raise HTTPException(status_code=404, detail="No se encontraron transacciones para este usuario.")
    return transactions


# Actualizar una transacción por ID
@app.put("/transacciones/{id}", response_model=TransaccionResponse, tags=["Transacciones"], description="Actualizar una transacción por ID.")
def actualizar_transaccion(id: int, transaction: TransaccionUpdate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para actualizar una transacción específica por ID.
    También ajusta el saldo del usuario en función del nuevo monto.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id_transaccion == id).first()
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transacción no encontrada.")

    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == transaction.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Convertir transaction.monto a Decimal
    monto_decimal = Decimal(transaction.monto)

    # Calcular la diferencia entre el monto anterior y el nuevo monto
    diferencia_monto = monto_decimal - db_transaction.monto

    # Ajustar el saldo del usuario según el tipo de transacción
    if db_transaction.tipo == "ingreso":
        usuario.saldo += diferencia_monto
    elif db_transaction.tipo == "egreso":
        usuario.saldo -= diferencia_monto

    # Actualizar los campos de la transacción
    db_transaction.id_usuario = transaction.id_usuario
    db_transaction.monto = monto_decimal
    db_transaction.descripcion = transaction.descripcion

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


# Eliminar una transacción por ID
@app.delete("/transacciones/{id}", tags=["Transacciones"], description="Eliminar una transacción por ID.")
def eliminar_transaccion(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para eliminar una transacción específica por ID.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id_transaccion == id).first()
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transacción no encontrada.")
    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transacción eliminada"}

# Presupuestos
@app.post("/presupuestos/crear", response_model=BudgetResponse, tags=["Presupuestos"], description="Crear un nuevo presupuesto.")
def crear_presupuesto(budget: BudgetCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para crear un nuevo presupuesto.
    """
    db_budget = Budget(**budget.dict())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.get("/presupuestos", response_model=List[BudgetResponse], tags=["Presupuestos"], description="Obtener todos los presupuestos.")
def obtener_presupuestos(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todos los presupuestos.
    """
    budgets = db.query(Budget).offset(skip).limit(limit).all()
    return budgets

@app.get("/presupuestos/{id}", response_model=BudgetResponse, tags=["Presupuestos"], description="Obtener un presupuesto por ID.")
def obtener_presupuesto(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener un presupuesto específico por ID.
    """
    budget = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return budget

@app.put("/presupuestos/{id}", response_model=BudgetResponse, tags=["Presupuestos"], description="Actualizar un presupuesto por ID.")
def actualizar_presupuesto(id: int, budget: BudgetCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para actualizar un presupuesto específico por ID.
    """
    db_budget = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if db_budget is None:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    for key, value in budget.dict().items():
        setattr(db_budget, key, value)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.delete("/presupuestos/{id}", tags=["Presupuestos"], description="Eliminar un presupuesto por ID.")
def eliminar_presupuesto(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para eliminar un presupuesto específico por ID.
    """
    db_budget = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if db_budget is None:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    db.delete(db_budget)
    db.commit()
    return {"detail": "Presupuesto eliminado"}


# Categorías
@app.post("/categorias/crear", response_model=CategoriaResponse, tags=["Categorías"], description="Crear una nueva categoría.")
def crear_categoria(categoria: CategoriaCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para crear una nueva categoría.
    """
    db_categoria = Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.get("/categorias", response_model=List[CategoriaResponse], tags=["Categorías"], description="Obtener todas las categorías.")
def obtener_categorias(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todas las categorías.
    """
    categorias = db.query(Categoria).offset(skip).limit(limit).all()
    return categorias

@app.get("/categorias/{id}", response_model=CategoriaResponse, tags=["Categorías"], description="Obtener una categoría por ID.")
def obtener_categoria(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener una categoría específica por ID.
    """
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@app.put("/categorias/{id}", response_model=CategoriaResponse, tags=["Categorías"], description="Actualizar una categoría por ID.")
def actualizar_categoria(id: int, categoria: CategoriaCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para actualizar una categoría específica por ID.
    """
    db_categoria = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    for key, value in categoria.dict().items():
        setattr(db_categoria, key, value)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.delete("/categorias/{id}", tags=["Categorías"], description="Eliminar una categoría por ID.")
def eliminar_categoria(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para eliminar una categoría específica por ID.
    """
    db_categoria = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db.delete(db_categoria)
    db.commit()
    return {"detail": "Categoría eliminada"}

# Pagos fijos
@app.post("/pagos/crear", response_model=PagoResponse, tags=["Pagos"], description="Crear un nuevo pago fijo.")
def crear_pago(pago: PagoCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para crear un nuevo pago fijo.
    Valida si el usuario tiene suficiente presupuesto para cubrir el pago.
    """
    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == pago.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Convertir monto a Decimal
    monto_decimal = Decimal(pago.monto)

    # Verificar si el usuario tiene suficiente saldo
    if usuario.saldo < monto_decimal:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para registrar el pago fijo.")

    # Registrar el pago fijo
    db_pago = Pago(
        id_usuario=pago.id_usuario,
        descripcion=pago.descripcion,
        monto=monto_decimal,
        fecha_programada=pago.fecha_programada
    )
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)

    # Actualizar el saldo del usuario
    usuario.saldo -= monto_decimal
    db.commit()

    return db_pago


@app.get("/pagos", response_model=List[PagoResponse], tags=["Pagos"], description="Obtener todos los pagos fijos.")
def obtener_pagos(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todos los pagos fijos.
    """
    pagos = db.query(Pago).offset(skip).limit(limit).all()
    for pago in pagos:
        dias_restantes = (pago.fecha_programada - datetime.utcnow()).days
        if dias_restantes <= 2 and pago.monto > usuario.saldo:
            mensaje = f"¡Atención! Tu saldo es insuficiente para el pago de {pago.descripcion} programado para {pago.fecha_programada.strftime('%d/%m/%Y')}."
            enviar_sms(usuario.telefono, mensaje)
    return pagos

@app.get("/pagos/{id}", response_model=PagoResponse, tags=["Pagos"], description="Obtener un pago fijo por ID.")
def obtener_pago(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener un pago fijo específico por ID.
    """
    pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago fijo no encontrado.")
    return pago

@app.put("/pagos/{id}", response_model=PagoResponse, tags=["Pagos"], description="Actualizar un pago fijo por ID.")
def actualizar_pago(id: int, pago: PagoCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para actualizar un pago fijo específico por ID.
    """
    db_pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago fijo no encontrado.")
    
    # Actualizar los campos del pago
    for key, value in pago.dict().items():
        setattr(db_pago, key, value)
    db.commit()
    db.refresh(db_pago)
    return db_pago

@app.delete("/pagos/{id}", tags=["Pagos"], description="Eliminar un pago fijo por ID.")
def eliminar_pago(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para eliminar un pago fijo específico por ID.
    """
    db_pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago fijo no encontrado.")
    db.delete(db_pago)
    db.commit()
    return {"detail": "Pago fijo eliminado"}


# Notificaciones
@app.post("/notificaciones/enviar", tags=["Notificaciones"], description="Enviar notificaciones por SMS.")
def enviar_notificacion(notificacion: dict):
    """
    Endpoint para enviar notificaciones por SMS.
    """
    destinatario = notificacion.get("destinatario")
    mensaje = notificacion.get("mensaje")

    if not destinatario or not mensaje:
        raise HTTPException(status_code=400, detail="Destinatario y mensaje son requeridos.")

    resultado = enviar_sms(destinatario, mensaje)
    return resultado