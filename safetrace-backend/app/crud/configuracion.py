"""Acceso a datos de A · Cuentas: configuración de sismos (RF-11, RF-12).

Colecciones de las que es dueño: configuracion. Es un solo documento con _id fijo.
"""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.crud import auditoria
from core.fechas import ahora

ID_PARAMETROS = "parametros_sismo"
POR_DEFECTO = {"magnitud_minima": 5.0, "radio_afectacion_km": 200}

# Parámetros del índice de priorización (RF-67). Todos son provisionales: los pesos se ajustan
# con las calificaciones de un perito (mínimos cuadrados con pesos no negativos) y Tₛ debe salir
# de la microzonificación sísmica de Pereira. Cada cambio debe subir `formula_version`.
ID_PARAMETROS_INDICE = "parametros_indice"
POR_DEFECTO_INDICE = {
    "formula_version": "v2-edo",
    "zeta": 0.05,  # amortiguamiento típico supuesto
    "periodo_suelo_s": 0.6,  # Tₛ de referencia
    "pesos": {
        "antiguedad": 0.10,
        "sistema_constructivo": 0.15,
        "resonancia": 0.15,
        "magnitud": 0.15,
        "cercania_foco": 0.20,
        "antecedentes_danos": 0.10,
        "falta_mantenimiento": 0.10,
        "tiempo_sin_revision": 0.05,
    },
    # 1 = más vulnerable para priorizar. Solo MNR = 1 y pórticos = 0,4 vienen del documento; el resto es propuesta
    "valores_sistema_constructivo": {
        "MAMPOSTERIA_NO_REFORZADA": 1.0,
        "TAPIA_ADOBE": 1.0,
        "BAHAREQUE": 0.8,
        "OTRO": 0.7,
        "MAMPOSTERIA_CONFINADA": 0.6,
        "MAMPOSTERIA_REFORZADA": 0.5,
        "MADERA": 0.5,
        "PORTICOS_CONCRETO": 0.4,
        "MUROS_CONCRETO": 0.3,
        "ESTRUCTURA_METALICA": 0.3,
    },
}


def obtener_configuracion_sismos(db: Database) -> dict:
    """Magnitud mínima y radio vigentes. Lo usa F."""
    return db["configuracion"].find_one({"_id": ID_PARAMETROS}) or {"_id": ID_PARAMETROS, **POR_DEFECTO}


def obtener_parametros_indice(db: Database) -> dict:
    """Pesos y parámetros vigentes del índice. Lo usa J. Lo que falte en la base se toma por defecto."""
    guardado = db["configuracion"].find_one({"_id": ID_PARAMETROS_INDICE}) or {}
    return {k: guardado.get(k, valor) for k, valor in POR_DEFECTO_INDICE.items()}


def actualizar_configuracion_sismos(db: Database, magnitud_minima: float, radio_afectacion_km: float, actor: dict):
    """Cada cambio queda en auditoría con el valor anterior y el nuevo."""
    anterior = obtener_configuracion_sismos(db)
    nuevo = db["configuracion"].find_one_and_update(
        {"_id": ID_PARAMETROS},
        {
            "$set": {
                "magnitud_minima": magnitud_minima,
                "radio_afectacion_km": radio_afectacion_km,
                "actualizado_por": actor["id"],
                "actualizado_en": ahora(),
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    auditoria.registrar(
        db,
        "configuracion",
        ID_PARAMETROS,
        "ACTUALIZAR_CONFIGURACION",
        actor,
        {
            "anterior": {k: anterior.get(k) for k in POR_DEFECTO},
            "nuevo": {"magnitud_minima": magnitud_minima, "radio_afectacion_km": radio_afectacion_km},
        },
    )
    return nuevo
