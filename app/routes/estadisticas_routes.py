from fastapi import APIRouter, Depends, HTTPException , Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict ,Optional
from app.database import get_db
from datetime import datetime, timedelta , date
from app.models.transaction_model import Transaction
from app.models.categoria_model import Categoria

router = APIRouter(tags=["Estadísticas"])


@router.get("/estadisticas/dashboard")
def dashboard_estadisticas(
    id_usuario: int = Query(..., description="ID del usuario"),
    desde: Optional[str] = Query(None, description="YYYY-MM-DD"),
    hasta: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    # 1) Rango por defecto: últimos 30 días (incluyendo hoy)
    if not desde or not hasta:
        fin = datetime.utcnow().date()
        ini = fin - timedelta(days=29)
    else:
        try:
            fin = datetime.strptime(hasta, "%Y-%m-%d").date()
            ini = datetime.strptime(desde, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")

    # 2) Resumen (no depende de categoría)
    ingresos = (
        db.query(func.sum(Transaction.monto))
          .filter(
              Transaction.id_usuario == id_usuario,
              Transaction.tipo == "ingreso",
              func.date(Transaction.fecha).between(ini, fin)
          ).scalar()
    ) or 0
    egresos = (
        db.query(func.sum(Transaction.monto))
          .filter(
              Transaction.id_usuario == id_usuario,
              Transaction.tipo == "egreso",
              func.date(Transaction.fecha).between(ini, fin)
          ).scalar()
    ) or 0

    # 3) Por categoría: usar LEFT OUTER JOIN y COALESCE para incluir transacciones sin categoría
    categoria_col = func.coalesce(Categoria.nombre, "Sin categoría").label("categoria")

    por_cat_ing = (
        db.query(
            categoria_col,
            func.sum(Transaction.monto).label("total")
        )
        .outerjoin(Categoria, Categoria.id_categoria == Transaction.categoria_id)
        .filter(
            Transaction.id_usuario == id_usuario,
            Transaction.tipo == "ingreso",
            func.date(Transaction.fecha).between(ini, fin)
        )
        .group_by(categoria_col)
        .all()
    )

    por_cat_egr = (
        db.query(
            categoria_col,
            func.sum(Transaction.monto).label("total")
        )
        .outerjoin(Categoria, Categoria.id_categoria == Transaction.categoria_id)
        .filter(
            Transaction.id_usuario == id_usuario,
            Transaction.tipo == "egreso",
            func.date(Transaction.fecha).between(ini, fin)
        )
        .group_by(categoria_col)
        .all()
    )

    # 4) Serie diaria (ingresos / egresos por día del rango)
    serie_ing = dict(
        db.query(
            func.date(Transaction.fecha).label("fecha"),
            func.sum(Transaction.monto).label("total")
        )
        .filter(
            Transaction.id_usuario == id_usuario,
            Transaction.tipo == "ingreso",
            func.date(Transaction.fecha).between(ini, fin)
        )
        .group_by(func.date(Transaction.fecha))
        .all()
    )
    serie_egr = dict(
        db.query(
            func.date(Transaction.fecha).label("fecha"),
            func.sum(Transaction.monto).label("total")
        )
        .filter(
            Transaction.id_usuario == id_usuario,
            Transaction.tipo == "egreso",
            func.date(Transaction.fecha).between(ini, fin)
        )
        .group_by(func.date(Transaction.fecha))
        .all()
    )

    # 5) Normalizar serie: un elemento por día aunque no haya movimientos
    dias = []
    cur: date = ini
    while cur <= fin:
        dias.append({
            "fecha": str(cur),
            "ingresos": float(serie_ing.get(cur, 0) or 0),
            "egresos": float(serie_egr.get(cur, 0) or 0),
        })
        cur += timedelta(days=1)

    return {
        "resumen": {
            "ingresos": float(ingresos),
            "egresos": float(egresos),
            "balance": float(ingresos) - float(egresos),
        },
        "por_categoria": {
            "ingresos": [{"categoria": c, "total": float(t)} for c, t in por_cat_ing],
            "egresos":  [{"categoria": c, "total": float(t)} for c, t in por_cat_egr],
        },
        "serie_diaria": dias,
        "rango": {"desde": str(ini), "hasta": str(fin)},
    }
# ────── Obtener resumen de ingresos/egresos por categoría ──────
@router.get("/estadisticas/por-categoria")
def obtener_estadisticas_por_categoria(id_usuario: int, tipo: str, db: Session = Depends(get_db)) -> List[Dict]:
    """
    tipo: 'ingreso' o 'egreso'
    """
    if tipo not in ["ingreso", "egreso"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Usa 'ingreso' o 'egreso'.")

    resultados = (
        db.query(
            Categoria.nombre.label("categoria"),
            func.sum(Transaction.monto).label("total")
        )
        .join(Categoria, Categoria.id_categoria == Transaction.categoria_id)
        .filter(Transaction.id_usuario == id_usuario)
        .filter(Transaction.tipo == tipo)
        .group_by(Categoria.nombre)
        .all()
    )

    return [{"categoria": r.categoria, "total": float(r.total)} for r in resultados]

# ────── Obtener resumen mensual por tipo ──────
@router.get("/estadisticas/mensual")
def obtener_estadisticas_mensual(id_usuario: int, db: Session = Depends(get_db)) -> Dict[str, float]:
    """
    Devuelve el total de ingresos y egresos del mes actual
    """
    from datetime import datetime

    hoy = datetime.utcnow()
    mes = hoy.month
    anio = hoy.year

    ingresos = (
        db.query(func.sum(Transaction.monto))
        .filter(Transaction.id_usuario == id_usuario)
        .filter(Transaction.tipo == "ingreso")
        .filter(func.extract("month", Transaction.fecha) == mes)
        .filter(func.extract("year", Transaction.fecha) == anio)
        .scalar()
    ) or 0

    egresos = (
        db.query(func.sum(Transaction.monto))
        .filter(Transaction.id_usuario == id_usuario)
        .filter(Transaction.tipo == "egreso")
        .filter(func.extract("month", Transaction.fecha) == mes)
        .filter(func.extract("year", Transaction.fecha) == anio)
        .scalar()
    ) or 0

    return {
        "ingresos_mes_actual": float(ingresos),
        "egresos_mes_actual": float(egresos)
    }

@router.get("/estadisticas/anual")
def obtener_estadisticas_anuales(id_usuario: int, anio: int, db: Session = Depends(get_db)) -> Dict[str, List[float]]:
    """
    Devuelve lista con totales mensuales de ingresos y egresos para el año especificado.
    """
    ingresos_mensuales = [0.0] * 12
    egresos_mensuales = [0.0] * 12

    for mes in range(1, 13):
        ingresos = (
            db.query(func.sum(Transaction.monto))
            .filter(Transaction.id_usuario == id_usuario)
            .filter(Transaction.tipo == "ingreso")
            .filter(func.extract("month", Transaction.fecha) == mes)
            .filter(func.extract("year", Transaction.fecha) == anio)
            .scalar()
        ) or 0

        egresos = (
            db.query(func.sum(Transaction.monto))
            .filter(Transaction.id_usuario == id_usuario)
            .filter(Transaction.tipo == "egreso")
            .filter(func.extract("month", Transaction.fecha) == mes)
            .filter(func.extract("year", Transaction.fecha) == anio)
            .scalar()
        ) or 0

        ingresos_mensuales[mes - 1] = float(ingresos)
        egresos_mensuales[mes - 1] = float(egresos)

    return {
        "ingresos_por_mes": ingresos_mensuales,
        "egresos_por_mes": egresos_mensuales
    }