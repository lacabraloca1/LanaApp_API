from decimal import Decimal
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import cast, Date, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
import calendar

from app.database import SessionLocal
from app.models.pago_model import PagoFijo
from app.models.user_model import User
from app.models.transaction_model import Transaction
from app.models.budget_model import Budget
from app.models.categoria_model import Categoria
from app.utils.notificaciones import enviar_correo
from app.utils.sms import enviar_sms

# ===== Helper: sumar meses sin dependencias externas =====
def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last_day))

def _avisar(user: User, asunto: str, mensaje: str):
    try:
        enviar_correo(user.correo, asunto, mensaje)
    except Exception as e:
        print(f"[Correo] Error notificando a {user.correo}: {e}")
    try:
        if getattr(user, "telefono", None):
            enviar_sms(user.telefono, f"{asunto}: {mensaje}")
    except Exception as e:
        print(f"[SMS] Error notificando a {user.telefono}: {e}")

# ===== Aviso 2 días antes (presupuesto y saldo) =====
def verificar_pagos_pendientes():
    db: Session = SessionLocal()
    try:
        try:
            from app.routes.presupuestos_routes import obtener_presupuesto_disponible
        except Exception:
            obtener_presupuesto_disponible = None

        hoy = datetime.utcnow().date()
        objetivo = hoy + timedelta(days=2)

        pagos = db.query(PagoFijo).filter(
            PagoFijo.activo == True,
            cast(PagoFijo.proxima_ejecucion, Date) == objetivo
        ).all()

        for pago in pagos:
            usuario = db.query(User).filter(User.id_usuario == pago.id_usuario).first()
            if not usuario:
                continue

            if obtener_presupuesto_disponible and pago.categoria_id:
                disponible = obtener_presupuesto_disponible(db, pago.id_usuario, pago.categoria_id, datetime.utcnow())
                if disponible < float(pago.monto):
                    _avisar(
                        usuario,
                        "⚠ Presupuesto insuficiente (aviso previo)",
                        f"En 2 días se programó '{pago.descripcion}' por ${pago.monto}, "
                        f"pero no hay presupuesto suficiente en la categoría."
                    )

            if (usuario.saldo or Decimal("0.00")) < pago.monto:
                _avisar(
                    usuario,
                    "⚠ Saldo insuficiente (aviso previo)",
                    f"En 2 días se programó '{pago.descripcion}' por ${pago.monto}, "
                    f"pero tu saldo actual no alcanza."
                )
    finally:
        db.close()

# ===== Ejecutar pagos del día (con reprogramación recurrente) =====
def ejecutar_pagos_fijos():
    db: Session = SessionLocal()
    try:
        hoy = datetime.utcnow().date()

        pagos = db.query(PagoFijo).filter(
            PagoFijo.activo == True,
            cast(PagoFijo.proxima_ejecucion, Date) <= hoy  
        ).all()

        try:
            from app.routes.presupuestos_routes import obtener_presupuesto_disponible
        except Exception:
            obtener_presupuesto_disponible = None

        for pago in pagos:
            usuario = db.query(User).filter(User.id_usuario == pago.id_usuario).first()
            if not usuario:
                continue

            if obtener_presupuesto_disponible and pago.categoria_id:
                disponible = obtener_presupuesto_disponible(db, pago.id_usuario, pago.categoria_id, datetime.utcnow())
            else:
                disponible = float('inf')

            if disponible < float(pago.monto):
                _avisar(
                    usuario,
                    "🚫 Pago no ejecutado (presupuesto insuficiente)",
                    f"No se ejecutó '{pago.descripcion}' por ${pago.monto} por falta de presupuesto."
                )
                if pago.periodicidad == 'weekly':
                    pago.proxima_ejecucion = pago.proxima_ejecucion + timedelta(weeks=1)
                elif pago.periodicidad == 'monthly':
                    pago.proxima_ejecucion = add_months(pago.proxima_ejecucion, 1)
                else:
                    pago.activo = False
                db.commit()
                continue

            if (usuario.saldo or Decimal("0.00")) < pago.monto:
                _avisar(
                    usuario,
                    "🚫 Pago no ejecutado (saldo insuficiente)",
                    f"No se ejecutó '{pago.descripcion}' por ${pago.monto} por saldo insuficiente."
                )
                if pago.periodicidad == 'weekly':
                    pago.proxima_ejecucion = pago.proxima_ejecucion + timedelta(weeks=1)
                elif pago.periodicidad == 'monthly':
                    pago.proxima_ejecucion = add_months(pago.proxima_ejecucion, 1)
                else:
                    pago.activo = False
                db.commit()
                continue

            tx = Transaction(
                id_usuario=pago.id_usuario,
                tipo="egreso",
                monto=pago.monto,
                descripcion=f"Pago fijo: {pago.descripcion}",
                categoria_id=pago.categoria_id,
                estado="completada",
                fecha=datetime.utcnow()
            )
            db.add(tx)
            usuario.saldo -= pago.monto
            db.commit()

            _avisar(
                usuario,
                "💸 Pago fijo ejecutado",
                f"Se ejecutó '{pago.descripcion}' por ${pago.monto}."
            )

            if pago.periodicidad == 'weekly':
                pago.proxima_ejecucion = pago.proxima_ejecucion + timedelta(weeks=1)
            elif pago.periodicidad == 'monthly':
                pago.proxima_ejecucion = add_months(pago.proxima_ejecucion, 1)
            else:
                pago.activo = False
            db.commit()
    finally:
        db.close()

# ===== Cron diario global para presupuestos (80% y 100%) =====
def verificar_presupuestos_global():
    """
    Recorre todos los usuarios y sus presupuestos del mes actual.
    Envía alerta por correo/SMS cuando el gasto por categoría supera 80% o 100%.
    """
    db: Session = SessionLocal()
    try:
        hoy = datetime.utcnow()
        mes, anio = hoy.month, hoy.year

        usuarios = db.query(User).all()
        for usuario in usuarios:
            presupuestos = db.query(Budget).filter(
                Budget.id_usuario == usuario.id_usuario,
                Budget.mes == mes,
                Budget.año == anio
            ).all()

            for p in presupuestos:
                total_gastado = (
                    db.query(func.sum(Transaction.monto))
                    .filter(
                        Transaction.id_usuario == usuario.id_usuario,
                        Transaction.categoria_id == p.id_categoria,
                        Transaction.tipo == "egreso",
                        func.extract("month", Transaction.fecha) == mes,
                        func.extract("year", Transaction.fecha) == anio
                    ).scalar()
                    or 0
                )

                if p.monto_mensual and p.monto_mensual > 0:
                    porcentaje = float(total_gastado) / float(p.monto_mensual) * 100.0
                else:
                    porcentaje = 0.0

                if porcentaje >= 80:
                    nombre_cat = db.query(Categoria.nombre).filter(Categoria.id_categoria == p.id_categoria).scalar() or "Sin categoría"
                    nivel = "excedido" if porcentaje >= 100 else "alto (80%)"
                    _avisar(
                        usuario,
                        "⚠ Alerta de Presupuesto",
                        f"Categoría '{nombre_cat}': llevas ${float(total_gastado):.2f} "
                        f"({porcentaje:.1f}% de ${float(p.monto_mensual):.2f}). Nivel: {nivel}."
                    )
    finally:
        db.close()

# ===== Inicializar scheduler =====
def iniciar_cron_jobs():
    scheduler = BackgroundScheduler()
    scheduler.add_job(verificar_pagos_pendientes, CronTrigger(minute="*/1"))
    scheduler.add_job(ejecutar_pagos_fijos,     CronTrigger(minute="*/1"))
    scheduler.add_job(verificar_presupuestos_global, CronTrigger(hour=9, minute=0))
    scheduler.start()