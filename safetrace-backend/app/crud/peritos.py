"""Capa de acceso a datos y reglas de negocio para Módulo B: Peritos (RF-13 a RF-16, RNF-15, RNF-20).

Implementa la persistencia en MongoDB y las validaciones de negocio correspondientes a:
- RF-13: Registro del expediente profesional del perito.
- RF-14: Incorporación de documentación probatoria de formación y matrícula.
- RF-15: Proceso administrativo de validación (aprobación/rechazo) de credenciales.
- RF-16: Registro de trazabilidad de validaciones (actor validador, fecha y documentos revisados).
- RN-01: Exclusividad de asignación a peritos habilitados con credenciales validadas.
- RN-03: Integridad de la cadena documental e inmutabilidad de dictámenes previos.
- RNF-15: Inhabilitación automática de peritos en estados pendientes, vencidos o con inconsistencias.
- RNF-20: Anonimización de datos personales en logs del sistema.
"""

from __future__ import annotations

import uuid
from typing import Any

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.schemas.peritos import (
    DocumentosPeritoCreate,
    PerfilPeritoCreate,
    ValidacionPeritoCreate,
)
from core.database import a_object_id
from core.fechas import ahora
from core.registro import obtener_logger, registrar_evento_seguro, sanitizar_pii

log = obtener_logger("crud.peritos")

COLECCION_PERITOS = "peritos"

# Estados válidos de la credencial profesional (RNF-15)
ESTADO_REGISTRADO = "REGISTRADO"
ESTADO_PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"
ESTADO_VALIDADO = "VALIDADO"
ESTADO_RECHAZADO = "RECHAZADO"
ESTADO_VENCIDO = "VENCIDO"
ESTADO_INCONSISTENTE = "INCONSISTENTE"


def sanitizar_log_perito(perito: dict[str, Any] | None) -> dict[str, Any]:
    """Extrae una versión anonimizada de los datos del perito para telemetría y logs (RNF-20).

    Oculta nombre, tipo/número de documento civil, correo y teléfono, preservando
    identificadores de entidad, timestamps y estados de ciclo de vida.
    """
    if not perito:
        return {}
    return {
        "perito_id": str(perito.get("_id", perito.get("id", ""))),
        "usuario_id": str(perito.get("usuario_id", "")),
        "estado_credencial": perito.get("estado_credencial"),
        "profesion": perito.get("profesion"),
        "especialidad": perito.get("especialidad"),
        "total_documentos": len(perito.get("documentos", [])),
        "total_validaciones": len(perito.get("validaciones", [])),
        "pii_protegida": True,
    }


def perito_habilitado_para_inspeccionar(db: Database, perito_id: str | ObjectId) -> bool:
    """Verifica si un perito cumple los requisitos normativos para ejecutar inspecciones (RNF-15, RN-01).

    Regla RNF-15: No se habilita para inspeccionar a peritos con credenciales
    pendientes de validación, vencidas, rechazadas o con inconsistencias activas.
    Solo el estado 'VALIDADO' otorga habilitación operativa.
    """
    doc = db[COLECCION_PERITOS].find_one({"_id": a_object_id(perito_id)})
    if not doc:
        return False

    estado = doc.get("estado_credencial")
    if estado != ESTADO_VALIDADO:
        return False

    # Verificar si tiene fecha de vencimiento y si ya expiró
    vigencia = doc.get("vigente_hasta")
    if vigencia and vigencia < ahora():
        return False

    # Verificar que no posea inconsistencias registradas no subsanadas
    if doc.get("motivo_inconsistencia") and estado != ESTADO_VALIDADO:
        return False

    return True


def obtener_por_usuario(db: Database, usuario_id: str | ObjectId) -> dict[str, Any] | None:
    """Obtiene el expediente de perito asociado a una cuenta de usuario."""
    uid = a_object_id(usuario_id)
    doc = db[COLECCION_PERITOS].find_one({"usuario_id": uid})
    if not doc and isinstance(usuario_id, str):
        doc = db[COLECCION_PERITOS].find_one({"usuario_id": usuario_id})
    return doc


def obtener_por_id(db: Database, perito_id: str | ObjectId) -> dict[str, Any] | None:
    """Obtiene un perito por su ObjectId identificador primario."""
    return db[COLECCION_PERITOS].find_one({"_id": a_object_id(perito_id)})


def registrar_perfil(
    db: Database,
    usuario_id: str | ObjectId,
    perfil: PerfilPeritoCreate,
    usuario_actor: dict[str, Any],
) -> dict[str, Any]:
    """Registra el perfil profesional inicial del perito (RF-13).

    Asigna el estado inicial 'REGISTRADO' a la espera de adjuntar soportes (RF-14).
    """
    uid = a_object_id(usuario_id)
    existente = obtener_por_usuario(db, uid)
    if existente:
        raise ValueError("PERFIL_DUPLICADO: El usuario ya posee un perfil de perito registrado")

    doc = {
        "usuario_id": uid,
        "documento": perfil.documento.model_dump(),
        "profesion": perfil.profesion.strip(),
        "especialidad": perfil.especialidad.strip(),
        "matricula_profesional": perfil.matricula_profesional.strip(),
        "estado_credencial": ESTADO_REGISTRADO,
        "documentos": [],
        "validaciones": [],
        "creado_en": ahora(),
        "actualizado_en": ahora(),
    }

    try:
        resultado = db[COLECCION_PERITOS].insert_one(doc)
        doc["_id"] = resultado.inserted_id
    except DuplicateKeyError as e:
        raise ValueError("PERFIL_DUPLICADO: La matrícula profesional o usuario ya se encuentra registrado") from e

    registrar_evento_seguro(
        log,
        "PERITO_PERFIL_REGISTRADO",
        sanitizar_log_perito(doc),
        nivel="info",
    )
    return doc


def agregar_documentos(
    db: Database,
    usuario_id: str | ObjectId,
    datos: DocumentosPeritoCreate,
    usuario_actor: dict[str, Any],
) -> dict[str, Any]:
    """Incorpora documentos de soporte probatorio y transiciona el estado a 'PENDIENTE_VALIDACION' (RF-14, RNF-15)."""
    uid = a_object_id(usuario_id)
    perito = obtener_por_usuario(db, uid)
    if not perito:
        raise LookupError("Expediente de perito no encontrado para este usuario")

    nuevos_docs: list[dict[str, Any]] = []
    momento = ahora()
    for d in datos.documentos:
        doc_dict = d.model_dump()
        doc_dict["id"] = doc_dict.get("id") or f"DOC-{uuid.uuid4().hex[:8].upper()}"
        doc_dict["subido_en"] = momento
        nuevos_docs.append(doc_dict)

    # Regla: Al adjuntar documentos para acreditar credenciales, transiciona a PENDIENTE_VALIDACION
    actualizado = db[COLECCION_PERITOS].find_one_and_update(
        {"_id": perito["_id"]},
        {
            "$push": {"documentos": {"$each": nuevos_docs}},
            "$set": {
                "estado_credencial": ESTADO_PENDIENTE_VALIDACION,
                "actualizado_en": momento,
            },
        },
        return_document=True,
    )

    registrar_evento_seguro(
        log,
        "PERITO_DOCUMENTOS_CARGADOS",
        {
            "perito_id": str(perito["_id"]),
            "documentos_nuevos": len(nuevos_docs),
            "nuevo_estado": ESTADO_PENDIENTE_VALIDACION,
        },
        nivel="info",
    )
    return actualizado


def validar_credencial(
    db: Database,
    perito_id: str | ObjectId,
    validacion: ValidacionPeritoCreate,
    usuario_validador: dict[str, Any],
) -> dict[str, Any]:
    """Aprobación o rechazo administrativo de credenciales de un perito (RF-15, RF-16).

    Registra la auditoría estricta de quién validó, en qué fecha y qué documentos cotejó.
    """
    pid = a_object_id(perito_id)
    perito = obtener_por_id(db, pid)
    if not perito:
        raise LookupError("Expediente de perito no encontrado")

    decision = validacion.decision.upper()
    nuevo_estado = ESTADO_VALIDADO if decision == "APROBADO" else ESTADO_RECHAZADO
    momento = ahora()

    registro_auditoria_validacion = {
        "validador_id": str(usuario_validador["_id"]),
        "fecha": momento,
        "decision": decision,
        "documentos_revisados": validacion.documentos_revisados or [],
        "motivo": validacion.motivo.strip() if validacion.motivo else None,
    }

    actualizaciones: dict[str, Any] = {
        "estado_credencial": nuevo_estado,
        "actualizado_en": momento,
    }
    if decision == "APROBADO":
        # Limpia cualquier señalamiento previo de inconsistencia si fue subsanado y aprobado
        actualizaciones["motivo_inconsistencia"] = None

    actualizado = db[COLECCION_PERITOS].find_one_and_update(
        {"_id": pid},
        {
            "$push": {"validaciones": registro_auditoria_validacion},
            "$set": actualizaciones,
        },
        return_document=True,
    )

    registrar_evento_seguro(
        log,
        "PERITO_CREDENCIAL_VALIDADA",
        {
            "perito_id": str(pid),
            "validador_id": str(usuario_validador["_id"]),
            "decision": decision,
            "documentos_revisados_total": len(validacion.documentos_revisados or []),
        },
        nivel="info",
    )
    return actualizado


def marcar_inconsistencia(
    db: Database,
    perito_id: str | ObjectId,
    motivo: str,
    usuario_actor: dict[str, Any],
) -> dict[str, Any]:
    """Registra una inconsistencia detectada en las credenciales del perito, inhabilitándolo (RNF-15)."""
    pid = a_object_id(perito_id)
    perito = obtener_por_id(db, pid)
    if not perito:
        raise LookupError("Expediente de perito no encontrado")

    momento = ahora()
    actualizado = db[COLECCION_PERITOS].find_one_and_update(
        {"_id": pid},
        {
            "$set": {
                "estado_credencial": ESTADO_INCONSISTENTE,
                "motivo_inconsistencia": motivo.strip(),
                "actualizado_en": momento,
            }
        },
        return_document=True,
    )

    registrar_evento_seguro(
        log,
        "PERITO_INCONSISTENCIA_MARCADA",
        {
            "perito_id": str(pid),
            "actor_id": str(usuario_actor["_id"]),
            "nuevo_estado": ESTADO_INCONSISTENTE,
        },
        nivel="warning",
    )
    return actualizado


def marcar_vencimientos(db: Database) -> int:
    """Proceso periódico que identifica credenciales profesionales caducadas y las marca 'VENCIDO' (RNF-15)."""
    momento = ahora()
    filtro = {
        "vigente_hasta": {"$lt": momento, "$ne": None},
        "estado_credencial": {"$nin": [ESTADO_VENCIDO, ESTADO_RECHAZADO]},
    }
    resultado = db[COLECCION_PERITOS].update_many(
        filtro,
        {
            "$set": {
                "estado_credencial": ESTADO_VENCIDO,
                "actualizado_en": momento,
            }
        },
    )

    if resultado.modified_count > 0:
        registrar_evento_seguro(
            log,
            "PERITOS_VENCIMIENTOS_ACTUALIZADOS",
            {"cantidad_vencidos": resultado.modified_count},
            nivel="info",
        )
    return resultado.modified_count


def listar_peritos(
    db: Database,
    estado_credencial: str | None = None,
    saltar: int = 0,
    limite: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Lista peritos para gestión administrativa con paginación defensiva."""
    filtro: dict[str, Any] = {}
    if estado_credencial:
        filtro["estado_credencial"] = estado_credencial.strip().upper()

    total = db[COLECCION_PERITOS].count_documents(filtro)
    cursor = db[COLECCION_PERITOS].find(filtro).skip(saltar).limit(limite).sort("creado_en", -1)
    return list(cursor), total
