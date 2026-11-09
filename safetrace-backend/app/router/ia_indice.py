"""Controlador API REST para el Módulo J: Análisis de IA e Índice de Priorización (RF-62 a RF-68).

Expone los endpoints para:
- RF-62 / RF-63: Consulta de análisis de comparación de fotos por IA.
- RF-64: Manejo de estados (PENDIENTE, PROCESANDO, COMPLETADO, FALLIDO) y reintento.
- RF-65: Rotulado obligatorio con leyenda «Análisis automático mediante IA», fecha y fotografías comparadas.
- RF-66: Índice de priorización post-sismo para inmuebles dentro del radio de afectación.
- RF-67: Desglose de las 7 variables del cálculo del índice.
- RF-68 / RNF-36 / RNF-37: Disclaimers éticos y legales (no es vulnerabilidad, no altera estados).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.database import Database

from app.crud import ia_indice as crud_ia_indice
from app.router.dependencies import (
    get_current_user,
    obtener_inmueble_autorizado,
    requiere_permiso,
)
from app.schemas.ia_indice import (
    AVISO_ORIENTATIVO_INDICE,
    LEYENDA_OFICIAL_IA,
    AnalisisIAOut,
    IndicePriorizacionOut,
    ReintentoAnalisisOut,
)
from core.database import a_object_id, get_db, serializar
from core.paginacion import Pagina

router = APIRouter()

modulo_analisis = "analisis_ia"
modulo_priorizacion = "priorizacion"


@router.get(
    "/inmuebles/{id}/analisis-ia",
    response_model=list[AnalisisIAOut],
    summary="Listar análisis de IA de un inmueble",
    description="Devuelve el historial de comparaciones fotográficas rotuladas con leyenda oficial y fechas (RF-64, RF-65).",
)
def listar_analisis_inmueble(
    id: str,
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(get_current_user),
):
    """Consulta los análisis de visión artificial asociados a un inmueble autorizado (RF-64, RF-65)."""
    inmueble = obtener_inmueble_autorizado(db, id, usuario)
    analisis = crud_ia_indice.obtener_analisis_por_inmueble(db, inmueble["_id"])
    return serializar(analisis)


@router.post(
    "/analisis-ia/{id}/reintento",
    response_model=ReintentoAnalisisOut,
    summary="Reintentar procesamiento de un análisis de IA",
    description="Permite reintentar un análisis en estado pendiente o fallido encolando una nueva tarea (RF-64).",
)
def reintentar_analisis(
    id: str,
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_analisis, "actualizar")),
):
    """Programa un nuevo intento de comparación de fotografías en segundo plano (RF-64)."""
    try:
        resultado = crud_ia_indice.reintentar_analisis(db, id, usuario)
        return resultado
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.get(
    "/inmuebles/{id}/indice",
    response_model=IndicePriorizacionOut,
    summary="Consultar índice de priorización de revisión",
    description="Calcula o retorna el índice tras un sismo con sus 7 variables y disclaimers éticos (RF-66, RF-67, RF-68).",
)
def consultar_indice_inmueble(
    id: str,
    sismo_id: str | None = Query(default=None, description="ID del sismo causante (opcional)"),
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(get_current_user),
):
    """Obtiene el índice de priorización de revisión con desglose de variables y disclaimers (RF-66, RF-67, RF-68)."""
    inmueble = obtener_inmueble_autorizado(db, id, usuario)

    # Si se suministró sismo_id explícito o se busca el más reciente
    doc_indice = crud_ia_indice.obtener_indice_por_inmueble(db, inmueble["_id"], sismo_id)
    if not doc_indice:
        # Si no existe cálculo previo y se envió sismo_id, se calcula al vuelo
        if sismo_id:
            try:
                doc_indice = crud_ia_indice.calcular_indice_priorizacion(db, inmueble["_id"], sismo_id)
            except LookupError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
        else:
            # Buscar último sismo registrado en la base de datos
            ultimo_sismo = db["sismos"].find_one(sort=[("fecha_hora", -1)])
            if ultimo_sismo:
                doc_indice = crud_ia_indice.calcular_indice_priorizacion(
                    db, inmueble["_id"], ultimo_sismo["_id"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No hay sismos registrados ni índice de priorización para este inmueble",
                )

    return serializar(doc_indice)


@router.get(
    "/admin/sismos/{id}/priorizacion",
    summary="Listar inmuebles priorizados tras un sismo",
    description="Tablero para administradores con ordenamiento decreciente de criticidad (RF-66, RF-67).",
)
def listar_priorizacion_sismo(
    id: str,
    pagina: Pagina = Depends(),
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_priorizacion, "seleccionar")),
):
    """Consulta administrativa de inmuebles priorizados tras un evento sísmico (RF-66, RF-67)."""
    datos, total = crud_ia_indice.listar_priorizacion_sismo(
        db,
        id,
        saltar=pagina.saltar,
        limite=pagina.tamano,
    )
    return pagina.respuesta(serializar(datos), total)
