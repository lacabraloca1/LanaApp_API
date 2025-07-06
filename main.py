from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from decimal import Decimal

# Configuración de la base de datos MySQL en Railway
DATABASE_URL = "mysql+pymysql://root:tzZfIAImhPszeqmloPtScAZShsGsaQWi@switchback.proxy.rlwy.net:37527/lana_app"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="LanaApp API",
    description="""
    Desarrollado por:
    - José Armando Mauricio Acevedo
    - Victor Olvera Olvera  
    - Perla Moreno Hurtado
    - Carlos Hernández Méndez
    """,
    version="1.0.0"
)

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
    saldo = Column(Numeric(10, 2), default=0)

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
    contraseña: str  # Cambiado de contraseña_hash a contraseña

class UserUpdate(BaseModel):
    """
    Esquema para la actualización de usuarios (modo admin).
    """
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    nueva_contraseña: Optional[str] = None

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
    fecha_registro: datetime
    # Removido pin_seguridad y contraseña_hash

class EstadisticasResponse(BaseModel):
    """
    Esquema para la respuesta de estadísticas del usuario.
    """
    id_usuario: int
    nombre: str
    saldo_actual: float
    total_ingresos: float
    total_egresos: float
    total_pagos_fijos: float
    porcentaje_disponible: float
    porcentaje_comprometido_pagos: float
    ingresos_por_categoria: List[dict]
    egresos_por_categoria: List[dict]
    pagos_fijos_detalle: List[dict]

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

# Función para registrar notificaciones (reemplaza el envío de SMS)
def registrar_notificacion(destinatario: str, mensaje: str):
    """
    Registra una notificación en la consola (reemplaza el envío de SMS).
    """
    print(f"[NOTIFICACIÓN] Para {destinatario}: {mensaje}")
    return {"message": "Notificación registrada exitosamente.", "destinatario": destinatario}

# Endpoints de la API

# Redirige automáticamente a la documentación de Swagger.
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Usuarios
@app.post("/usuarios/registrar", response_model=UserResponse, tags=["Usuarios"], description="Registrar un nuevo usuario. Ejemplo: {\"nombre\": \"Juan Pérez\", \"correo\": \"juan@gmail.com\", \"telefono\": \"4428378528\", \"contraseña\": \"mipassword123\"}")
def registrar_usuario(user: UserCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para registrar un nuevo usuario.
    """
    # Crear el usuario mapeando 'contraseña' a 'contraseña_hash'
    db_user = User(
        nombre=user.nombre,
        correo=user.correo,
        telefono=user.telefono,
        contraseña_hash=user.contraseña  # Mapear contraseña a contraseña_hash
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/usuarios/login", tags=["Usuarios"], description="Iniciar sesión de usuario. Ejemplo: correo=juan@gmail.com, contraseña=mipassword123")
def login_usuario(correo: str, contraseña: str, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para iniciar sesión de usuario.
    """
    usuario = db.query(User).filter(User.correo == correo, User.contraseña_hash == contraseña).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    
    # Crear respuesta personalizada sin pin_seguridad y contraseña_hash
    usuario_response = {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "telefono": usuario.telefono,
        "saldo": float(usuario.saldo),
        "fecha_registro": usuario.fecha_registro
    }
    
    return {"message": "Inicio de sesión exitoso", "usuario": usuario_response}

@app.get("/usuarios", response_model=List[UserResponse], tags=["Usuarios"], description="Obtener todos los usuarios registrados. No requiere parámetros, solo presiona Execute.")
def obtener_usuarios(db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todos los usuarios registrados.
    """
    usuarios = db.query(User).all()
    return usuarios

@app.get("/usuarios/{id}", response_model=UserResponse, tags=["Usuarios"], description="Obtener un usuario por ID. Ejemplo: usar id=1 para obtener el usuario con ID 1.")
def obtener_usuario(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener un usuario específico por ID.
    """
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return usuario

@app.put("/usuarios/{id}", tags=["Usuarios"], description="Actualizar un usuario por ID. Ejemplo: id=1, {\"nombre\": \"Nuevo Nombre\", \"correo\": \"nuevo@gmail.com\", \"telefono\": \"4428378999\", \"nueva_contraseña\": \"nuevapass123\"}")
def actualizar_usuario(id: int, user_update: UserUpdate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para actualizar un usuario específico por ID (modo admin).
    Permite actualizar nombre, correo, teléfono y/o contraseña sin validación de contraseña.
    """
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Actualizar solo los campos que se proporcionaron
    if user_update.nombre is not None:
        usuario.nombre = user_update.nombre
    
    if user_update.correo is not None:
        # Verificar que el nuevo correo no esté ya en uso por otro usuario
        correo_existente = db.query(User).filter(User.correo == user_update.correo, User.id_usuario != id).first()
        if correo_existente:
            raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso por otro usuario.")
        usuario.correo = user_update.correo
    
    if user_update.telefono is not None:
        # Verificar que el nuevo teléfono no esté ya en uso por otro usuario
        telefono_existente = db.query(User).filter(User.telefono == user_update.telefono, User.id_usuario != id).first()
        if telefono_existente:
            raise HTTPException(status_code=400, detail="El número de teléfono ya está en uso por otro usuario.")
        usuario.telefono = user_update.telefono
    
    if user_update.nueva_contraseña is not None:
        usuario.contraseña_hash = user_update.nueva_contraseña

    db.commit()
    db.refresh(usuario)
    
    # Crear respuesta sin datos sensibles
    usuario_response = {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "telefono": usuario.telefono,
        "saldo": float(usuario.saldo),
        "fecha_registro": usuario.fecha_registro
    }
    
    return {"message": "Usuario actualizado exitosamente.", "usuario": usuario_response}

@app.delete("/usuarios/{id}", tags=["Usuarios"], description="Eliminar un usuario por ID. Ejemplo: usar id=1 para eliminar el usuario con ID 1. Elimina también todas sus transacciones, presupuestos y pagos.")
def eliminar_usuario(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para eliminar un usuario específico por ID (modo admin).
    No requiere validación de contraseña.
    """
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    try:
        # Eliminar todas las transacciones del usuario
        db.query(Transaction).filter(Transaction.id_usuario == id).delete()
        
        # Eliminar todos los presupuestos del usuario
        db.query(Budget).filter(Budget.id_usuario == id).delete()
        
        # Eliminar todos los pagos fijos del usuario
        db.query(Pago).filter(Pago.id_usuario == id).delete()
        
        # Ahora eliminar el usuario
        db.delete(usuario)
        db.commit()
        
        return {"detail": "Usuario eliminado exitosamente."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")

# Ingresos
@app.post("/ingresos/crear", response_model=TransaccionResponse, tags=["Ingresos"], description="Registrar un ingreso. Ejemplo: {\"id_usuario\": 1, \"monto\": 1000.50, \"descripcion\": \"Pago de nómina\"}")
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

    # Registrar notificación
    mensaje = f"Has recibido un ingreso de ${transaction.monto:.2f}. Descripción: {transaction.descripcion}. Tu saldo actual es de ${usuario.saldo:.2f}."
    registrar_notificacion(usuario.telefono, mensaje)

    return db_transaction

# Egresos
@app.post("/egresos/crear", response_model=TransaccionResponse, tags=["Egresos"], description="Registrar un egreso. Ejemplo: {\"id_usuario\": 1, \"monto\": 250.75, \"descripcion\": \"Compra de supermercado\"}")
def crear_egreso(transaction: EgresoCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para registrar un egreso.
    """
    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == transaction.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Verificar si el saldo es suficiente
    monto_decimal = Decimal(transaction.monto)
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

    # Registrar notificación
    mensaje = f"Has realizado un egreso de ${transaction.monto:.2f}. Descripción: {transaction.descripcion}. Tu saldo actual es de ${usuario.saldo:.2f}."
    registrar_notificacion(usuario.telefono, mensaje)

    # Verificar si el gasto excede el presupuesto
    presupuesto = db.query(Budget).filter(
        Budget.id_usuario == transaction.id_usuario,
        Budget.id_categoria == categoria.id_categoria,
        Budget.mes == datetime.utcnow().month,
        Budget.año == datetime.utcnow().year
    ).first()

    if presupuesto and monto_decimal > presupuesto.monto_mensual:
        mensaje_presupuesto = f"¡Atención! Has excedido tu presupuesto mensual de ${presupuesto.monto_mensual:.2f} para la categoría {categoria.nombre}."
        registrar_notificacion(usuario.telefono, mensaje_presupuesto)

    return db_transaction

# Transacciones
@app.get("/transacciones", response_model=List[TransaccionResponse], tags=["Transacciones"], description="Obtener todas las transacciones. Ejemplo: skip=0, limit=10 para ver las primeras 10 transacciones.")
def obtener_transacciones(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todas las transacciones de todos los usuarios.
    """
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
    return transactions

@app.get("/transacciones/{id_usuario}", response_model=List[TransaccionResponse], tags=["Transacciones"], description="Obtener transacciones de un usuario específico. Ejemplo: usar id_usuario=1 para ver todas las transacciones del usuario con ID 1.")
def obtener_transacciones_usuario(id_usuario: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todas las transacciones de un usuario específico, ordenadas de la más reciente a la más antigua.
    """
    transactions = db.query(Transaction).filter(Transaction.id_usuario == id_usuario).order_by(Transaction.fecha.desc()).all()
    if not transactions:
        raise HTTPException(status_code=404, detail="No se encontraron transacciones para este usuario.")
    return transactions

@app.put("/transacciones/{id}", response_model=TransaccionResponse, tags=["Transacciones"], description="Actualizar una transacción por ID. Ejemplo: id=1, {\"id_usuario\": 1, \"monto\": 1500.0, \"descripcion\": \"Pago actualizado\"}")
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

@app.delete("/transacciones/{id}", tags=["Transacciones"], description="Eliminar una transacción por ID. Ejemplo: usar id=1 para eliminar la transacción con ID 1.")
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
@app.post("/presupuestos/crear", response_model=BudgetResponse, tags=["Presupuestos"], description="Crear un nuevo presupuesto. Ejemplo: {\"id_usuario\": 1, \"id_categoria\": 1, \"monto_mensual\": 3000.0, \"mes\": 7, \"año\": 2025}")
def crear_presupuesto(budget: BudgetCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para crear un nuevo presupuesto.
    """
    db_budget = Budget(**budget.dict())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.get("/presupuestos", response_model=List[BudgetResponse], tags=["Presupuestos"], description="Obtener todos los presupuestos. Ejemplo: skip=0, limit=10 para ver los primeros 10 presupuestos.")
def obtener_presupuestos(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todos los presupuestos.
    """
    budgets = db.query(Budget).offset(skip).limit(limit).all()
    return budgets

@app.get("/presupuestos/{id}", response_model=BudgetResponse, tags=["Presupuestos"], description="Obtener un presupuesto por ID. Ejemplo: usar id=1 para obtener el presupuesto con ID 1.")
def obtener_presupuesto(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener un presupuesto específico por ID.
    """
    budget = db.query(Budget).filter(Budget.id_presupuesto == id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return budget

@app.put("/presupuestos/{id}", response_model=BudgetResponse, tags=["Presupuestos"], description="Actualizar un presupuesto por ID. Ejemplo: id=1, {\"id_usuario\": 1, \"id_categoria\": 1, \"monto_mensual\": 3500.0, \"mes\": 7, \"año\": 2025}")
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

@app.delete("/presupuestos/{id}", tags=["Presupuestos"], description="Eliminar un presupuesto por ID. Ejemplo: usar id=1 para eliminar el presupuesto con ID 1.")
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
@app.post("/categorias/crear", response_model=CategoriaResponse, tags=["Categorías"], description="Crear una nueva categoría. Ejemplo: {\"nombre\": \"Alimentación\", \"tipo\": \"egreso\"} o {\"nombre\": \"Salario\", \"tipo\": \"ingreso\"}")
def crear_categoria(categoria: CategoriaCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para crear una nueva categoría.
    """
    db_categoria = Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@app.get("/categorias", response_model=List[CategoriaResponse], tags=["Categorías"], description="Obtener todas las categorías. Ejemplo: skip=0, limit=10 para ver las primeras 10 categorías.")
def obtener_categorias(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todas las categorías.
    """
    categorias = db.query(Categoria).offset(skip).limit(limit).all()
    return categorias

@app.get("/categorias/{id}", response_model=CategoriaResponse, tags=["Categorías"], description="Obtener una categoría por ID. Ejemplo: usar id=1 para obtener la categoría con ID 1.")
def obtener_categoria(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener una categoría específica por ID.
    """
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@app.put("/categorias/{id}", response_model=CategoriaResponse, tags=["Categorías"], description="Actualizar una categoría por ID. Ejemplo: id=1, {\"nombre\": \"Comida Rápida\", \"tipo\": \"egreso\"}")
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

@app.delete("/categorias/{id}", tags=["Categorías"], description="Eliminar una categoría por ID. Ejemplo: usar id=1 para eliminar la categoría con ID 1.")
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
@app.post("/pagos/crear", response_model=PagoResponse, tags=["Pagos"], description="Crear un nuevo pago fijo. Ejemplo: {\"id_usuario\": 1, \"descripcion\": \"Renta mensual\", \"monto\": 8000.0, \"fecha_programada\": \"2025-07-15T00:00:00\"}")
def crear_pago(pago: PagoCreate, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para crear un nuevo pago fijo.
    """
    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == pago.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Convertir monto a Decimal
    monto_decimal = Decimal(pago.monto)

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

    return db_pago

@app.get("/pagos", response_model=List[PagoResponse], tags=["Pagos"], description="Obtener todos los pagos fijos. Ejemplo: skip=0, limit=10 para ver los primeros 10 pagos fijos.")
def obtener_pagos(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener todos los pagos fijos.
    """
    pagos = db.query(Pago).offset(skip).limit(limit).all()
    return pagos

@app.get("/pagos/{id}", response_model=PagoResponse, tags=["Pagos"], description="Obtener un pago fijo por ID. Ejemplo: usar id=1 para obtener el pago fijo con ID 1.")
def obtener_pago(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener un pago fijo específico por ID.
    """
    pago = db.query(Pago).filter(Pago.id_pago == id).first()
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago fijo no encontrado.")
    return pago

@app.put("/pagos/{id}", response_model=PagoResponse, tags=["Pagos"], description="Actualizar un pago fijo por ID. Ejemplo: id=1, {\"id_usuario\": 1, \"descripcion\": \"Renta actualizada\", \"monto\": 8500.0, \"fecha_programada\": \"2025-07-15T00:00:00\"}")
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

@app.delete("/pagos/{id}", tags=["Pagos"], description="Eliminar un pago fijo por ID. Ejemplo: usar id=1 para eliminar el pago fijo con ID 1.")
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

@app.get("/usuarios/{id}/estadisticas", response_model=EstadisticasResponse, tags=["Estadísticas"], description="Obtener estadísticas detalladas de un usuario. Ejemplo: usar id=1 para ver estadísticas del usuario con ID 1. Incluye porcentajes de ingresos, egresos y pagos fijos.")
def obtener_estadisticas_usuario(id: int, db: SessionLocal = Depends(get_db)):
    """
    Endpoint para obtener estadísticas detalladas de un usuario específico por ID.
    Incluye porcentajes de distribución de ingresos, egresos y pagos fijos.
    """
    # Verificar si el usuario existe
    usuario = db.query(User).filter(User.id_usuario == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Obtener saldo actual
    saldo_actual = float(usuario.saldo) if usuario.saldo else 0.0

    # Calcular total de ingresos
    total_ingresos = db.query(func.sum(Transaction.monto)).filter(
        Transaction.id_usuario == id,
        Transaction.tipo == "ingreso"
    ).scalar() or 0.0
    total_ingresos = float(total_ingresos)

    # Calcular total de egresos
    total_egresos = db.query(func.sum(Transaction.monto)).filter(
        Transaction.id_usuario == id,
        Transaction.tipo == "egreso"
    ).scalar() or 0.0
    total_egresos = float(total_egresos)

    # Calcular total de pagos fijos
    total_pagos_fijos = db.query(func.sum(Pago.monto)).filter(
        Pago.id_usuario == id
    ).scalar() or 0.0
    total_pagos_fijos = float(total_pagos_fijos)

    # Calcular porcentajes basados en el saldo actual
    if saldo_actual > 0:
        porcentaje_comprometido_pagos = (total_pagos_fijos / saldo_actual) * 100
        porcentaje_disponible = 100 - porcentaje_comprometido_pagos
    else:
        porcentaje_comprometido_pagos = 0.0
        porcentaje_disponible = 0.0

    # Obtener ingresos por categoría con porcentajes
    ingresos_por_categoria = []
    if total_ingresos > 0:
        ingresos_query = db.query(
            Categoria.nombre,
            func.sum(Transaction.monto).label('total')
        ).join(
            Transaction, Transaction.categoria_id == Categoria.id_categoria
        ).filter(
            Transaction.id_usuario == id,
            Transaction.tipo == "ingreso"
        ).group_by(Categoria.nombre).all()

        for categoria, monto in ingresos_query:
            porcentaje = (float(monto) / total_ingresos) * 100
            ingresos_por_categoria.append({
                "categoria": categoria,
                "monto": float(monto),
                "porcentaje": round(porcentaje, 2)
            })

    # Obtener egresos por categoría with porcentajes
    egresos_por_categoria = []
    if total_egresos > 0:
        egresos_query = db.query(
            Categoria.nombre,
            func.sum(Transaction.monto).label('total')
        ).join(
            Transaction, Transaction.categoria_id == Categoria.id_categoria
        ).filter(
            Transaction.id_usuario == id,
            Transaction.tipo == "egreso"
        ).group_by(Categoria.nombre).all()

        for categoria, monto in egresos_query:
            porcentaje = (float(monto) / total_egresos) * 100
            egresos_por_categoria.append({
                "categoria": categoria,
                "monto": float(monto),
                "porcentaje": round(porcentaje, 2)
            })

    # Obtener detalle de pagos fijos con porcentajes individuales
    pagos_fijos_detalle = []
    pagos_fijos = db.query(Pago).filter(Pago.id_usuario == id).all()
    
    for pago in pagos_fijos:
        if saldo_actual > 0:
            porcentaje_individual = (float(pago.monto) / saldo_actual) * 100
        else:
            porcentaje_individual = 0.0
            
        pagos_fijos_detalle.append({
            "id_pago": pago.id_pago,
            "descripcion": pago.descripcion,
            "monto": float(pago.monto),
            "porcentaje_del_saldo": round(porcentaje_individual, 2),
            "fecha_programada": pago.fecha_programada
        })

    # Crear respuesta
    estadisticas = {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "saldo_actual": saldo_actual,
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "total_pagos_fijos": total_pagos_fijos,
        "porcentaje_disponible": round(porcentaje_disponible, 2),
        "porcentaje_comprometido_pagos": round(porcentaje_comprometido_pagos, 2),
        "ingresos_por_categoria": ingresos_por_categoria,
        "egresos_por_categoria": egresos_por_categoria,
        "pagos_fijos_detalle": pagos_fijos_detalle
    }

    return estadisticas
