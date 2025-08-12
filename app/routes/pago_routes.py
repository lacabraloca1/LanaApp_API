from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date
from datetime import datetime, timedelta, date
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
import calendar
from app.database import get_db
from app.models.pago_model import PagoFijo
from app.models.user_model import User
from app.models.budget_model import Budget
from app.models.transaction_model import Transaction
from app.utils.notificaciones import enviar_correo

router = APIRouter(tags=["Pagos"])

# ===== Helpers =====
def add_months(d: date, months: int) -> date:
    """Suma meses a una fecha sin dependencias externas, ajustando fin de mes."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last_day))

# ────── Esquemas ──────
class PagoCrear(BaseModel):
    id_usuario: int
    descripcion: str
    monto: float = Field(gt=0)
    fecha_programada: datetime
    categoria_id: Optional[int] = None
    periodicidad: str = Field(default="none", pattern="^(none|weekly|monthly)$")

class PagoActualizar(BaseModel):
    descripcion: str
    monto: float = Field(gt=0)
    fecha_programada: datetime
    categoria_id: Optional[int] = None
    periodicidad: str = Field(default="none", pattern="^(none|weekly|monthly)$")

class PagoRespuesta(BaseModel):
    id_pago: int
    id_usuario: int
    descripcion: str
    monto: float
    fecha_programada: datetime
    categoria_id: Optional[int] = None
    periodicidad: str
    proxima_ejecucion: date
    activo: bool

    class Config:
        orm_mode = True

# ────── Crear ──────
@router.post("/pagos", response_model=PagoRespuesta)
def crear_pago(data: PagoCrear, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id_usuario == data.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    nuevo = PagoFijo(
        id_usuario=data.id_usuario,
        descripcion=data.descripcion,
        monto=Decimal(data.monto),
        fecha_programada=data.fecha_programada,
        categoria_id=data.categoria_id,
        periodicidad=data.periodicidad,
        proxima_ejecucion=data.fecha_programada.date(),
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ────── Obtener todos ──────
@router.get("/pagos", response_model=List[PagoRespuesta])
def listar_pagos(
    id_usuario: int = Query(...),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return (
        db.query(PagoFijo)
        .filter(PagoFijo.id_usuario == id_usuario)
        .offset(skip)
        .limit(limit)
        .all()
    )

# ────── Ejecutar pagos programados ──────
@router.post("/pagos/ejecutar")
def ejecutar_pagos_automaticos(db: Session = Depends(get_db)):
    hoy = datetime.utcnow().date()

    pagos = db.query(PagoFijo).filter(
        PagoFijo.activo == True,
        cast(PagoFijo.proxima_ejecucion, Date) <= hoy
    ).all()

    ejecutados = 0
    omitidos_presupuesto = 0
    omitidos_saldo = 0

    # Import local para evitar dependencias circulares
    try:
        from app.routes.presupuestos_routes import obtener_presupuesto_disponible
    except Exception:
        obtener_presupuesto_disponible = None

    for pago in pagos:
        usuario = db.query(User).filter(User.id_usuario == pago.id_usuario).first()
        if not usuario:
            continue

        # 1) Verifica presupuesto por categoría (si aplica)
        if obtener_presupuesto_disponible and pago.categoria_id:
            disponible = obtener_presupuesto_disponible(db, pago.id_usuario, pago.categoria_id, datetime.utcnow())
            if disponible < float(pago.monto):
                enviar_correo(
                    destinatario=usuario.correo,
                    asunto="⚠ Presupuesto insuficiente para pago programado",
                    mensaje=f"Tu pago '{pago.descripcion}' de ${pago.monto} excede el presupuesto de la categoría."
                )
                omitidos_presupuesto += 1
                # Reprogramar según periodicidad
                if pago.periodicidad == "weekly":
                    pago.proxima_ejecucion = pago.proxima_ejecucion + timedelta(weeks=1)
                elif pago.periodicidad == "monthly":
                    pago.proxima_ejecucion = add_months(pago.proxima_ejecucion, 1)
                else:
                    pago.activo = False
                db.commit()
                continue

        # 2) Verifica saldo
        if (usuario.saldo or Decimal("0.00")) < pago.monto:
            enviar_correo(
                destinatario=usuario.correo,
                asunto="❗ Pago no ejecutado por saldo insuficiente",
                mensaje=f"Hola {usuario.nombre}, tu pago '{pago.descripcion}' no se realizó por saldo insuficiente."
            )
            omitidos_saldo += 1
            if pago.periodicidad == "weekly":
                pago.proxima_ejecucion = pago.proxima_ejecucion + timedelta(weeks=1)
            elif pago.periodicidad == "monthly":
                pago.proxima_ejecucion = add_months(pago.proxima_ejecucion, 1)
            else:
                pago.activo = False
            db.commit()
            continue

        # 3) Ejecutar pago: registrar transacción + descontar saldo
        usuario.saldo -= pago.monto
        nueva_tx = Transaction(
            id_usuario=pago.id_usuario,
            tipo="egreso",
            monto=pago.monto,
            descripcion=f"Pago fijo: {pago.descripcion}",
            categoria_id=pago.categoria_id,
            estado="completada"
        )
        db.add(nueva_tx)
        db.commit()

        # 4) Reprogramar siguiente ejecución
        if pago.periodicidad == "weekly":
            pago.proxima_ejecucion = pago.proxima_ejecucion + timedelta(weeks=1)
        elif pago.periodicidad == "monthly":
            pago.proxima_ejecucion = add_months(pago.proxima_ejecucion, 1)
        else:
            pago.activo = False
        db.commit()

        enviar_correo(
            destinatario=usuario.correo,
            asunto="💸 Pago programado ejecutado",
            mensaje=f"Tu pago de ${pago.monto} ('{pago.descripcion}') se ejecutó con éxito."
        )
        ejecutados += 1

    return {
        "mensaje": "Pagos procesados",
        "ejecutados": ejecutados,
        "omitidos_por_presupuesto": omitidos_presupuesto,
        "omitidos_por_saldo": omitidos_saldo
    }

# ────── Obtener uno ──────
@router.get("/pagos/{id_pago}", response_model=PagoRespuesta)
def obtener_pago(id_pago: int, db: Session = Depends(get_db)):
    pago = db.query(PagoFijo).filter(PagoFijo.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    return pago

# ────── Actualizar ──────
@router.put("/pagos/{id_pago}", response_model=PagoRespuesta)
def actualizar_pago(id_pago: int, data: PagoActualizar, db: Session = Depends(get_db)):
    pago = db.query(PagoFijo).filter(PagoFijo.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")

    # (opcional) validar categoría
    if data.categoria_id:
        from app.models.categoria_model import Categoria
        if not db.query(Categoria).filter(Categoria.id_categoria == data.categoria_id).first():
            raise HTTPException(status_code=404, detail="Categoría no encontrada.")

    pago.descripcion = data.descripcion
    pago.monto = Decimal(data.monto)
    pago.fecha_programada = data.fecha_programada
    pago.categoria_id = data.categoria_id
    pago.periodicidad = data.periodicidad
    pago.proxima_ejecucion = data.fecha_programada.date()
    db.commit()
    db.refresh(pago)
    return pago

# ────── Eliminar ──────
@router.delete("/pagos/{id_pago}")
def eliminar_pago(id_pago: int, db: Session = Depends(get_db)):
    pago = db.query(PagoFijo).filter(PagoFijo.id_pago == id_pago).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    db.delete(pago)
    db.commit()
    return {"mensaje": "Pago eliminado correctamente"}
