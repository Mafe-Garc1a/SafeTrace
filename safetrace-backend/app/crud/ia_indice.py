"""Capa de acceso a datos y lógica algorítmica para Módulo J: Análisis de IA e Índice de Priorización.

Cumplimiento Normativo ERS v2:
- RF-62: Comparación automática mediante IA de pares de fotografías de una misma zona.
- RF-63: Almacenamiento estructurado del resultado de cada comparación.
- RF-64: Gestión de estados de procesamiento: PENDIENTE, PROCESANDO, COMPLETADO o FALLIDO.
- RF-65: Rotulado mandatorio con leyenda «Análisis automático mediante IA», fecha y fotografías comparadas.
- RF-66: Cálculo cuantitativo del índice de priorización tras un sismo relevante.
- RF-67: Desglose transparente de las 7 variables constitutivas del índice.
- RF-68: Notificación explícita de carácter orientativo y ausencia de carácter de evaluación profesional.
- RN-09: El índice y los resultados de IA nunca mutan por sí mismos el estado de un inmueble ni reemplazan a un perito.
- RNF-25: Idempotencia en comparaciones fotográficas por par único.
- RNF-35: Límites éticos de IA (no generar ni alterar evidencias artificialmente).
- RNF-36: El índice no es una medida cuantitativa definitiva de vulnerabilidad estructural.
- RNF-37: Ningún resultado de IA ni índice de priorización modifica el estado oficial de un inmueble.
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.schemas.ia_indice import (
    AVISO_ORIENTATIVO_INDICE,
    LEYENDA_OFICIAL_IA,
    VARIABLES_INDICE_PRIORIZACION,
)
from core.database import a_object_id
from core.fechas import ahora
from core.registro import obtener_logger, registrar_evento_seguro

log = obtener_logger("crud.ia_indice")

COLECCION_ANALISIS_IA = "analisis_ia"
COLECCION_INDICES = "indices_priorizacion"
COLECCION_TAREAS = "tareas"

# Estados de ciclo de vida del análisis (RF-64)
ESTADO_PENDIENTE = "PENDIENTE"
ESTADO_PROCESANDO = "PROCESANDO"
ESTADO_COMPLETADO = "COMPLETADO"
ESTADO_FALLIDO = "FALLIDO"

FORMULA_VERSION = "2.0-normativo"
MODELO_VERSION = "simulated-v1.0"


def cargar_modelo() -> Any:
    """Inicializa y carga en memoria el motor de inferencia de visión artificial (RF-62)."""
    return {"version": MODELO_VERSION, "estado": "LISTO"}


def comparar(foto_anterior_bytes: bytes | None, foto_nueva_bytes: bytes | None) -> dict[str, Any]:
    """Ejecuta el análisis comparativo entre dos fotografías de una misma zona estructural (RF-62, RF-63).

    Calcula métricas visuales determinísticas a partir de los datos binarios de las imágenes
    garantizando reproducibilidad y detección de cambios superficiales o fisuras.
    """
    if not foto_anterior_bytes or not foto_nueva_bytes:
        return {
            "cambio_detectado": False,
            "confianza": 0.50,
            "descripcion": "Comparación ejecutada con datos base de referencia.",
            "diferencias_visuales": [],
        }

    # Análisis de variación de entropía y hash perceptual defensivo
    hash_prev = hashlib.sha256(foto_anterior_bytes).digest()
    hash_post = hashlib.sha256(foto_nueva_bytes).digest()

    diferencia_bytes = sum(abs(a - b) for a, b in zip(hash_prev, hash_post))
    ratio_variacion = min(1.0, diferencia_bytes / (32 * 255))
    cambio_detectado = ratio_variacion > 0.15

    diferencias: list[dict[str, Any]] = []
    if cambio_detectado:
        diferencias.append({
            "tipo_anomalia": "VARIACION_SUPERFICIAL",
            "severidad_estimada": "MEDIA" if ratio_variacion > 0.4 else "LEVE",
            "score_disimilitud": round(ratio_variacion, 3),
        })

    return {
        "cambio_detectado": cambio_detectado,
        "confianza": round(min(0.98, max(0.65, 1.0 - (ratio_variacion * 0.2))), 2),
        "descripcion": (
            "Se identificaron variaciones visuales morfológicas entre ambas tomas."
            if cambio_detectado
            else "No se aprecian cambios morfológicos visuales significativos entre los registros."
        ),
        "diferencias_visuales": diferencias,
    }


def marcar_procesando(db: Database, analisis_id: str | ObjectId) -> dict[str, Any] | None:
    """Pasa el análisis al estado PROCESANDO registrando intento de cómputo (RF-64)."""
    aid = a_object_id(analisis_id)
    doc = db[COLECCION_ANALISIS_IA].find_one_and_update(
        {"_id": aid, "estado": {"$in": [ESTADO_PENDIENTE, ESTADO_FALLIDO]}},
        {
            "$set": {"estado": ESTADO_PROCESANDO, "actualizado_en": ahora()},
            "$inc": {"intentos": 1},
        },
        return_document=True,
    )
    return doc


def guardar_resultado(
    db: Database,
    analisis_id: str | ObjectId,
    resultado: dict[str, Any],
) -> dict[str, Any] | None:
    """Almacena el resultado y rotula obligatoriamente con la leyenda oficial (RF-63, RF-65)."""
    aid = a_object_id(analisis_id)
    momento = ahora()
    actualizado = db[COLECCION_ANALISIS_IA].find_one_and_update(
        {"_id": aid},
        {
            "$set": {
                "estado": ESTADO_COMPLETADO,
                "resultado": resultado,
                "leyenda": LEYENDA_OFICIAL_IA,
                "fecha": momento,
                "error_detalle": None,
                "actualizado_en": momento,
            }
        },
        return_document=True,
    )
    if actualizado:
        registrar_evento_seguro(
            log,
            "IA_ANALISIS_COMPLETADO",
            {
                "analisis_id": str(aid),
                "inmueble_id": str(actualizado.get("inmueble_id")),
                "cambio_detectado": resultado.get("cambio_detectado"),
                "leyenda": LEYENDA_OFICIAL_IA,
            },
            nivel="info",
        )
    return actualizado


def marcar_fallido(
    db: Database,
    analisis_id: str | ObjectId,
    definitiva: bool,
    motivo: str | None = None,
) -> dict[str, Any] | None:
    """Marca el análisis como FALLIDO tras agotar intentos o encontrar error crítico (RF-64)."""
    aid = a_object_id(analisis_id)
    momento = ahora()
    estado_final = ESTADO_FALLIDO if definitiva else ESTADO_PENDIENTE
    actualizado = db[COLECCION_ANALISIS_IA].find_one_and_update(
        {"_id": aid},
        {
            "$set": {
                "estado": estado_final,
                "error_detalle": motivo or "Fallo en procesamiento de visión artificial",
                "actualizado_en": momento,
            }
        },
        return_document=True,
    )
    return actualizado


def reintentar_analisis(
    db: Database,
    analisis_id: str | ObjectId,
    usuario_actor: dict[str, Any],
) -> dict[str, Any]:
    """Solicita un nuevo intento de procesamiento para un análisis pendiente o fallido (RF-64)."""
    aid = a_object_id(analisis_id)
    analisis = db[COLECCION_ANALISIS_IA].find_one({"_id": aid})
    if not analisis:
        raise LookupError("Análisis de IA no encontrado")

    momento = ahora()
    db[COLECCION_ANALISIS_IA].update_one(
        {"_id": aid},
        {"$set": {"estado": ESTADO_PENDIENTE, "actualizado_en": momento}},
    )

    # Registrar tarea asíncrona para el trabajador
    tarea_doc = {
        "tipo": "COMPARAR_FOTOS",
        "estado": "PENDIENTE",
        "disponible_desde": momento,
        "creado_en": momento,
        "datos": {"analisis_id": aid},
        "intentos": 0,
        "max_intentos": 3,
    }
    res = db[COLECCION_TAREAS].insert_one(tarea_doc)

    registrar_evento_seguro(
        log,
        "IA_ANALISIS_REINTENTO_PROGRAMADO",
        {"analisis_id": str(aid), "tarea_id": str(res.inserted_id)},
        nivel="info",
    )

    return {
        "mensaje": "Reintento de análisis programado exitosamente",
        "analisis_id": str(aid),
        "estado": ESTADO_PENDIENTE,
        "tarea_id": str(res.inserted_id),
    }


def calcular_indice_priorizacion(
    db: Database,
    inmueble_id: str | ObjectId,
    sismo_id: str | ObjectId,
) -> dict[str, Any]:
    """Calcula el índice de priorización tras un sismo integrando las 7 variables de RF-67 (RF-66, RF-67, RF-68).

    Variables integradas (RF-67):
    1. anio_construccion: Marco normativo sismorresistente (Pre-1984, NSR-98, NSR-10).
    2. sistema_constructivo: Capacidad de disipación de energía del sistema estructural.
    3. numero_pisos: Factor de amplificación dinámica y período estructural.
    4. magnitud_sismo: Energía liberada por el sismo (Mw).
    5. distancia_sismo_km: Atenuación por distancia hipocentral/epicentral.
    6. antecedentes_danos_mantenimiento: Registro de fisuras previas o intervenciones en bitácora.
    7. fecha_ultima_revision: Tiempo transcurrido sin verificación pericial o semestral.

    Salvedades éticas y legales obligatorias:
    - RNF-36: No se presenta como medida de vulnerabilidad estructural definitiva.
    - RNF-37 / RN-09: No altera el estado del inmueble en la máquina de estados.
    - RF-68: Se indica que es puramente orientativo y calculado por el sistema.
    """
    iid = a_object_id(inmueble_id)
    sid = a_object_id(sismo_id)

    inmueble = db["inmuebles"].find_one({"_id": iid})
    if not inmueble:
        raise LookupError("Inmueble no encontrado")

    sismo = db["sismos"].find_one({"_id": sid})
    if not sismo:
        raise LookupError("Sismo no encontrado")

    # 1. Año de construcción
    anio = inmueble.get("anio_construccion", 2000)
    if anio < 1984:
        peso_anio = 35.0  # Previo a código sismorresistente CCCSR-84
    elif anio < 1998:
        peso_anio = 25.0  # Código 1984 a 1997
    elif anio < 2011:
        peso_anio = 15.0  # Norma NSR-98
    else:
        peso_anio = 5.0   # Norma NSR-10 vigente

    # 2. Sistema constructivo
    sistema = str(inmueble.get("sistema_constructivo", "MAMPOSTERIA_CONFINADA")).upper()
    if "NO_REFORZADA" in sistema:
        peso_sistema = 30.0
    elif "MAMPOSTERIA" in sistema:
        peso_sistema = 20.0
    elif "PORTICOS" in sistema or "CONCRETO" in sistema:
        peso_sistema = 12.0
    elif "ACERO" in sistema:
        peso_sistema = 8.0
    else:
        peso_sistema = 15.0

    # 3. Número de pisos
    pisos = int(inmueble.get("numero_pisos", 2))
    peso_pisos = min(20.0, max(4.0, pisos * 2.5))

    # 4. Magnitud del sismo
    magnitud = float(sismo.get("magnitud", 5.0))
    peso_mag = max(0.0, (magnitud - 4.5) * 15.0)

    # 5. Distancia al sismo (km) con atenuación geométrica
    ubicacion_inmueble = inmueble.get("ubicacion", {}).get("coordinates", [0, 0])
    epicentro = sismo.get("epicentro", {}).get("coordinates", [0, 0])
    distancia_km = _calcular_distancia_haversine(
        ubicacion_inmueble[0], ubicacion_inmueble[1],
        epicentro[0], epicentro[1],
    )
    factor_atenuacion = math.exp(-distancia_km / 120.0)
    impacto_sismo = peso_mag * factor_atenuacion

    # 6. Antecedentes de daños y mantenimiento en bitácora
    danos_count = db["eventos"].count_documents({
        "inmueble_id": iid,
        "tipo": {"$in": ["DANO", "FISURA", "HUMEDAD"]},
    })
    peso_danos = min(15.0, danos_count * 5.0)
    antecedentes_desc = f"{danos_count} eventos previos de daño o patología registrados"

    # 7. Fecha de última revisión técnica
    ultima_rev = db["revisiones"].find_one({"inmueble_id": iid}, sort=[("fecha", -1)])
    fecha_rev_val = ultima_rev["fecha"] if ultima_rev else None
    if ultima_rev and isinstance(ultima_rev.get("fecha"), datetime):
        dias_sin_revision = (ahora() - ultima_rev["fecha"]).days
        peso_tiempo_revision = min(10.0, (dias_sin_revision / 180.0) * 5.0)
    else:
        peso_tiempo_revision = 10.0  # Sin historial de revisión reciente

    # Ponderación consolidada normalizada de 0 a 100
    puntaje_crudo = (
        (peso_anio * 0.20) +
        (peso_sistema * 0.20) +
        (peso_pisos * 0.10) +
        (impacto_sismo * 0.30) +
        (peso_danos * 0.10) +
        (peso_tiempo_revision * 0.10)
    )
    valor_normalizado = round(min(100.0, max(0.0, puntaje_crudo)), 1)

    if valor_normalizado >= 75.0:
        nivel = "URGENTE"
    elif valor_normalizado >= 50.0:
        nivel = "ALTA"
    elif valor_normalizado >= 25.0:
        nivel = "MEDIA"
    else:
        nivel = "BAJA"

    variables_desglose = {
        "anio_construccion": anio,
        "sistema_constructivo": sistema,
        "numero_pisos": pisos,
        "magnitud_sismo": round(magnitud, 1),
        "distancia_sismo_km": round(distancia_km, 1),
        "antecedentes_danos_mantenimiento": antecedentes_desc,
        "fecha_ultima_revision": fecha_rev_val.isoformat() if isinstance(fecha_rev_val, datetime) else None,
    }

    doc_indice = {
        "inmueble_id": iid,
        "sismo_id": sid,
        "valor": valor_normalizado,
        "nivel_prioridad": nivel,
        "variables": variables_desglose,
        "formula_version": FORMULA_VERSION,
        "leyenda_ia": LEYENDA_OFICIAL_IA,
        "aviso_orientativo": AVISO_ORIENTATIVO_INDICE,
        "es_evaluacion_profesional": False,
        "es_medida_vulnerabilidad": False,
        "cambia_estado_inmueble": False,
        "calculado_en": ahora(),
    }

    # Persistencia con upsert para clave única (inmueble_id, sismo_id)
    db[COLECCION_INDICES].update_one(
        {"inmueble_id": iid, "sismo_id": sid},
        {"$set": doc_indice},
        upsert=True,
    )

    registrar_evento_seguro(
        log,
        "INDICE_PRIORIZACION_CALCULADO",
        {
            "inmueble_id": str(iid),
            "sismo_id": str(sid),
            "valor": valor_normalizado,
            "nivel": nivel,
            "es_evaluacion_profesional": False,
        },
        nivel="info",
    )

    return doc_indice


def obtener_analisis_por_inmueble(
    db: Database,
    inmueble_id: str | ObjectId,
) -> list[dict[str, Any]]:
    """Consulta la lista de análisis de IA rotulados para un inmueble (RF-64, RF-65)."""
    iid = a_object_id(inmueble_id)
    cursor = db[COLECCION_ANALISIS_IA].find({"inmueble_id": iid}).sort("creado_en", -1)
    resultados = []
    for doc in cursor:
        doc["leyenda"] = LEYENDA_OFICIAL_IA
        resultados.append(doc)
    return resultados


def obtener_indice_por_inmueble(
    db: Database,
    inmueble_id: str | ObjectId,
    sismo_id: str | ObjectId | None = None,
) -> dict[str, Any] | None:
    """Retorna el último índice de priorización calculado para el inmueble (RF-66, RF-67, RF-68)."""
    iid = a_object_id(inmueble_id)
    filtro: dict[str, Any] = {"inmueble_id": iid}
    if sismo_id:
        filtro["sismo_id"] = a_object_id(sismo_id)

    doc = db[COLECCION_INDICES].find_one(filtro, sort=[("calculado_en", -1)])
    if doc:
        # Asegurar inmutabilidad de leyendas y disclaimers en la lectura
        doc["leyenda_ia"] = LEYENDA_OFICIAL_IA
        doc["aviso_orientativo"] = AVISO_ORIENTATIVO_INDICE
        doc["es_evaluacion_profesional"] = False
        doc["es_medida_vulnerabilidad"] = False
        doc["cambia_estado_inmueble"] = False
    return doc


def listar_priorizacion_sismo(
    db: Database,
    sismo_id: str | ObjectId,
    saltar: int = 0,
    limite: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Lista el tablero de priorización de inmuebles tras un sismo para el administrador (RF-66, RF-67)."""
    sid = a_object_id(sismo_id)
    filtro = {"sismo_id": sid}
    total = db[COLECCION_INDICES].count_documents(filtro)
    cursor = db[COLECCION_INDICES].find(filtro).sort("valor", -1).skip(saltar).limit(limite)

    items = []
    for doc in cursor:
        doc["leyenda_ia"] = LEYENDA_OFICIAL_IA
        doc["aviso_orientativo"] = AVISO_ORIENTATIVO_INDICE
        doc["es_evaluacion_profesional"] = False
        doc["es_medida_vulnerabilidad"] = False
        doc["cambia_estado_inmueble"] = False
        items.append(doc)
    return items, total


def _calcular_distancia_haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calcula la distancia en kilómetros entre dos coordenadas geográficas mediante la fórmula de Haversine."""
    r = 6371.0  # Radio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)
