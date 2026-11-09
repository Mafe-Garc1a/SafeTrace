"""Controlador API REST para el Módulo B: Peritos.

TRAZABILIDAD ERS v2:
- RF-13: Registro del perfil profesional del perito (POST /peritos/perfil).
- RF-14: Carga de documentos de acreditación y matrícula (POST /peritos/documentos).
- RF-15: Aprobación y rechazo administrativo de credenciales (POST /admin/peritos/{id}/validacion).
- RF-16: Auditoría formal de validación registrando validador, fecha y documentos revisados.
- RN-01: Exclusividad operativa para peritos en estado 'VALIDADO'.
- RN-03: Integridad de la cadena documental probatoria e inmutabilidad de dictámenes.
- RNF-15: Inhabilitación automática para inspeccionar en estados pendientes, vencidos o con inconsistencias.
- RNF-20: Anonimización de datos sensibles en el procesamiento y registro de logs.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.database import Database

from app.crud import peritos as crud_peritos
from app.router.dependencies import (
    get_current_user,
    requiere_permiso,
    requiere_servicio_n8n,
)
from app.schemas.peritos import (
    DocumentosPeritoCreate,
    InconsistenciaPeritoCreate,
    PerfilPeritoCreate,
    PeritoMiEstadoOut,
    PeritoOut,
    ValidacionPeritoCreate,
)
from core.database import a_object_id, get_db, serializar
from core.paginacion import Pagina

router = APIRouter()

modulo_perfil = "perfil_perito"
modulo_validacion = "validacion_peritos"


@router.post(
    "/peritos/perfil",
    response_model=PeritoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar perfil profesional del perito",
    description="Permite registrar nombre, documento, profesión, especialidad y matrícula (RF-13).",
)
def registrar_perfil(
    perfil: PerfilPeritoCreate,
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_perfil, "insertar")),
):
    """Crea el expediente profesional del perito con estado inicial REGISTRADO (RF-13)."""
    try:
        creado = crud_peritos.registrar_perfil(db, usuario["_id"], perfil, usuario)
        return serializar(creado)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None


@router.post(
    "/peritos/documentos",
    response_model=PeritoOut,
    summary="Cargar soportes de matrícula y formación",
    description="Permite al perito adjuntar documentos probatorios y transiciona a PENDIENTE_VALIDACION (RF-14).",
)
def cargar_documentos(
    documentos: DocumentosPeritoCreate,
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_perfil, "actualizar")),
):
    """Adjunta soportes y solicita validación de credenciales (RF-14, RNF-15)."""
    try:
        actualizado = crud_peritos.agregar_documentos(db, usuario["_id"], documentos, usuario)
        return serializar(actualizado)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.get(
    "/peritos/mi-estado",
    response_model=PeritoMiEstadoOut,
    summary="Consultar estado de credenciales del perito autenticado",
    description="Devuelve el estado de habilitación para inspecciones y resumen documental (RNF-15).",
)
def consultar_mi_estado(
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(get_current_user),
):
    """Retorna si el perito cuenta con habilitación efectiva para inspeccionar según RNF-15."""
    perito = crud_peritos.obtener_por_usuario(db, usuario["_id"])
    if not perito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de perito no registrado. Registre su perfil primero.",
        )

    habilitado = crud_peritos.perito_habilitado_para_inspeccionar(db, perito["_id"])
    ult_val = perito["validaciones"][-1] if perito.get("validaciones") else None

    return {
        "perito_id": str(perito["_id"]),
        "estado_credencial": perito.get("estado_credencial", "REGISTRADO"),
        "habilitado_para_inspeccionar": habilitado,
        "matricula_profesional": perito.get("matricula_profesional", ""),
        "total_documentos": len(perito.get("documentos", [])),
        "ultima_validacion": ult_val,
    }


@router.get(
    "/admin/peritos",
    summary="Listar peritos para gestión y validación",
    description="Permite al administrador consultar peritos filtrando por estado de credencial (RF-15).",
)
def listar_peritos_admin(
    estado: str | None = Query(default=None, description="Filtrar por estado_credencial"),
    pagina: Pagina = Depends(),
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_validacion, "seleccionar")),
):
    """Consulta paginada de expedientes de peritos para evaluación administrativa."""
    datos, total = crud_peritos.listar_peritos(
        db,
        estado_credencial=estado,
        saltar=pagina.saltar,
        limite=pagina.tamano,
    )
    return pagina.respuesta(serializar(datos), total)


@router.post(
    "/admin/peritos/{id}/validacion",
    response_model=PeritoOut,
    summary="Validar (aprobar o rechazar) credenciales de un perito",
    description="Registra la decisión administrativa con trazabilidad inmutable de documentos revisados (RF-15, RF-16).",
)
def validar_credencial(
    id: str,
    validacion: ValidacionPeritoCreate,
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_validacion, "actualizar")),
):
    """Aprobación o rechazo administrativo de credenciales de un perito (RF-15, RF-16)."""
    try:
        actualizado = crud_peritos.validar_credencial(db, id, validacion, usuario)
        return serializar(actualizado)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.post(
    "/admin/peritos/{id}/inconsistencia",
    response_model=PeritoOut,
    summary="Marcar inconsistencia en credenciales de un perito",
    description="Inhabilita al perito para realizar inspecciones debido a anomalías detectadas (RNF-15).",
)
def reportar_inconsistencia(
    id: str,
    datos: InconsistenciaPeritoCreate,
    db: Database = Depends(get_db),
    usuario: dict[str, Any] = Depends(requiere_permiso(modulo_validacion, "actualizar")),
):
    """Marca la credencial como INCONSISTENTE y suspende la habilitación operativa (RNF-15)."""
    try:
        actualizado = crud_peritos.marcar_inconsistencia(db, id, datos.motivo, usuario)
        return serializar(actualizado)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.post(
    "/interno/peritos/vencimientos",
    summary="Proceso automático de verificación de vencimientos de matrícula",
    description="Invocado diariamente por n8n para marcar como VENCIDO a peritos caducados (RNF-15).",
)
def ejecutar_vencimientos_peritos(
    db: Database = Depends(get_db),
    _: None = Depends(requiere_servicio_n8n),
):
    """Tarea desatendida de control de caducidad de matrículas profesionales (RNF-15)."""
    actualizados = crud_peritos.marcar_vencimientos(db)
    return {
        "estado": "ok",
        "credenciales_vencidas_actualizadas": actualizados,
    }
