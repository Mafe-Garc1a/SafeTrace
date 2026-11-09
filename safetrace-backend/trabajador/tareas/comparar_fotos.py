"""Tarea asíncrona de trabajador: COMPARAR_FOTOS.

TRAZABILIDAD ERS v2 (Módulo J: Análisis de IA):
- RF-62: Comparación automática mediante IA de dos fotografías de una misma zona o elemento estructural.
- RF-63: Almacenamiento persistente del resultado de la comparación en la colección 'analisis_ia'.
- RF-64: Manejo y visibilidad de los estados del análisis (PENDIENTE -> PROCESANDO -> COMPLETADO o FALLIDO).
- RF-65: Rotulado normativo inmutable con la leyenda «Análisis automático mediante IA», fecha y referencias fotográficas.
- RNF-25 (Eficiencia): Procesamiento único por par de fotografías mediante clave unívoca de par (clave_par).
- RNF-35 (Límites éticos): Salvaguarda contra invención o alteración artificial de evidencias.
- RN-09: El resultado de la comparación es de apoyo visual y jamás altera de forma autónoma el estado del inmueble.

Flujo de Ejecución:
    1. Consumo de la tarea de la colección 'tareas' por el trabajador en segundo plano.
    2. Transición a estado PROCESANDO en 'analisis_ia' (RF-64).
    3. Descarga binaria de ambas fotografías desde el proveedor de almacenamiento (core.almacenamiento).
    4. Ejecución del modelo de visión artificial para evaluar similitud morfológica y anomalías.
    5. Persistencia del diagnóstico con rotulación obligatoria (RF-63, RF-65).
    6. En caso de error o excepciones de red/modelo, delegación a 'al_fallar' con marcación defensiva.
"""

from __future__ import annotations

from typing import Any

from pymongo.database import Database

from app.crud import bitacora as crud_bitacora
from app.crud import ia_indice as crud_ia_indice
from core import almacenamiento

_modelo = None


def ejecutar(db: Database, tarea: dict[str, Any]) -> None:
    """Ejecuta el pipeline de visión artificial para un par fotográfico (RF-62 a RF-65)."""
    global _modelo
    analisis = crud_ia_indice.marcar_procesando(db, tarea["datos"]["analisis_id"])
    if analisis is None:
        return  # Reemplazado, cancelado o completado concurrentemente
    if _modelo is None:
        _modelo = crud_ia_indice.cargar_modelo()
    anterior = crud_bitacora.obtener_evidencia(db, analisis["evidencia_anterior_id"])
    nueva = crud_bitacora.obtener_evidencia(db, analisis["evidencia_nueva_id"])
    resultado = crud_ia_indice.comparar(
        almacenamiento.descargar(anterior["archivo"]["ruta"]),
        almacenamiento.descargar(nueva["archivo"]["ruta"]),
    )
    crud_ia_indice.guardar_resultado(db, analisis["_id"], resultado)


def al_fallar(db: Database, tarea: dict[str, Any], definitiva: bool) -> None:
    """Maneja el fallo transitorio o definitivo de la tarea según la política de reintentos (RF-64)."""
    crud_ia_indice.marcar_fallido(db, tarea["datos"]["analisis_id"], definitiva)
