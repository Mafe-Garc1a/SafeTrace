"""Esquemas Pydantic para el Módulo J: Análisis de IA e Índice de Priorización (RF-62 a RF-68, RNF-25, RNF-36, RNF-37).

Define los contratos para:
- RF-62 / RF-63: Resultados de comparación automática de fotografías mediante IA.
- RF-64: Estados de ciclo de vida del análisis (PENDIENTE, PROCESANDO, COMPLETADO, FALLIDO).
- RF-65: Rotulación normativa obligatoria con la leyenda «Análisis automático mediante IA», fecha y fotos.
- RF-66 / RF-67: Índice de priorización post-sismo y desglose de las 7 variables constitutivas.
- RF-68 / RNF-36 / RNF-37: Disclaimers de no vulnerabilidad y salvaguarda de no mutación del estado del inmueble.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# Leyenda estándar exigida por RF-65
LEYENDA_OFICIAL_IA = "Análisis automático mediante IA"

# Aviso orientativo exigido por RF-68, RNF-36 y RNF-37
AVISO_ORIENTATIVO_INDICE = (
    "El índice de priorización es una estimación orientativa calculada automáticamente por el sistema; "
    "no constituye una evaluación técnica profesional ni representa una medida definitiva de vulnerabilidad estructural. "
    "Ningún resultado de IA ni índice de priorización modifica por sí solo el estado oficial del inmueble (RF-68, RNF-36, RNF-37)."
)

# Nombres canónicos de las variables del índice según RF-67
VARIABLES_INDICE_PRIORIZACION: tuple[str, ...] = (
    "anio_construccion",
    "sistema_constructivo",
    "numero_pisos",
    "magnitud_sismo",
    "distancia_sismo_km",
    "antecedentes_danos_mantenimiento",
    "fecha_ultima_revision",
)


class FotografiasComparadas(BaseModel):
    """Par de fotografías cotejadas durante el análisis (RF-65)."""

    evidencia_anterior_id: str = Field(..., description="ID de la evidencia fotográfica previa (línea base)")
    evidencia_nueva_id: str = Field(..., description="ID de la evidencia fotográfica reciente post-evento")


class ResultadoComparacionIA(BaseModel):
    """Diagnóstico visual generado por el modelo de visión artificial (RF-62, RF-63)."""

    cambio_detectado: bool = Field(..., description="Indica si se observaron anomalías o cambios morfológicos")
    confianza: float = Field(..., ge=0.0, le=1.0, description="Nivel de certeza estadística del algoritmo (0 a 1)")
    descripcion: str = Field(..., description="Resumen descriptivo de los cambios visuales detectados")
    diferencias_visuales: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Listado de regiones o anomalías observadas (fisuras, desprendimientos, etc.)",
    )


class AnalisisIAOut(BaseModel):
    """Representación formal de un análisis de visión artificial con rotulado obligatorio (RF-64, RF-65)."""

    id: str = Field(..., description="Identificador único del análisis de IA")
    inmueble_id: str = Field(..., description="Identificador del inmueble asociado")
    zona_id: str | None = Field(default=None, description="Identificador de la zona inspeccionada")
    clave_par: str = Field(..., description="Hash unívoco del par de fotografías para idempotencia (RNF-25)")
    estado: Literal["PENDIENTE", "PROCESANDO", "COMPLETADO", "FALLIDO"] = Field(
        ...,
        description="Estado actual del procesamiento asíncrono (RF-64)",
    )
    fotografias_comparadas: FotografiasComparadas = Field(
        ...,
        description="Referencias explícitas de las dos imágenes comparadas (RF-65)",
    )
    leyenda: str = Field(
        default=LEYENDA_OFICIAL_IA,
        description="Leyenda mandatoria exigida por la norma ERS v2 (RF-65)",
    )
    fecha: datetime = Field(..., description="Fecha de realización o registro del análisis en UTC (RF-65)")
    resultado: ResultadoComparacionIA | None = Field(
        default=None,
        description="Diagnóstico técnico de IA disponible cuando el estado es COMPLETADO (RF-63)",
    )
    error_detalle: str | None = Field(
        default=None,
        description="Descripción técnica del fallo en caso de estado FALLIDO (RF-64)",
    )
    intentos: int = Field(default=0, description="Contador de ejecuciones/reintentos del análisis")
    creado_en: datetime
    actualizado_en: datetime | None = None


class VariablesIndiceOut(BaseModel):
    """Desglose explícito de las variables que componen el índice de priorización (RF-67)."""

    anio_construccion: int | None = Field(
        default=None,
        description="Año de construcción de la estructura (antigüedad vs código sismorresistente)",
    )
    sistema_constructivo: str | None = Field(
        default=None,
        description="Sistema estructural del inmueble (ej. PÓRTICOS_CONCRETO, MAMPOSTERIA_CONFINADA)",
    )
    numero_pisos: int | None = Field(
        default=None,
        description="Número de niveles o pisos sobre rasante",
    )
    magnitud_sismo: float | None = Field(
        default=None,
        description="Magnitud en escala de momento (Mw) o Richter del evento telúrico",
    )
    distancia_sismo_km: float | None = Field(
        default=None,
        description="Distancia en kilómetros entre el epicentro y el inmueble",
    )
    antecedentes_danos_mantenimiento: str | None = Field(
        default=None,
        description="Resumen de eventos previos de daño o intervenciones de mantenimiento registradas",
    )
    fecha_ultima_revision: datetime | str | None = Field(
        default=None,
        description="Fecha en que se llevó a cabo la última revisión o inspección técnica",
    )


class IndicePriorizacionOut(BaseModel):
    """Índice cuantitativo de priorización de revisión con disclaimers éticos y legales (RF-66, RF-67, RF-68)."""

    id: str | None = Field(default=None, description="Identificador del cálculo del índice")
    inmueble_id: str = Field(..., description="Identificador del inmueble priorizado")
    sismo_id: str = Field(..., description="Identificador del evento sísmico desencadenante")
    valor: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Valor numérico normalizado de priorización de revisión (0 a 100) (RF-66)",
    )
    nivel_prioridad: Literal["BAJA", "MEDIA", "ALTA", "URGENTE"] = Field(
        ...,
        description="Categorización de orden de atención sugerida",
    )
    variables: VariablesIndiceOut = Field(
        ...,
        description="Variables constitutivas del índice para total transparencia (RF-67)",
    )
    leyenda_ia: str = Field(
        default=LEYENDA_OFICIAL_IA,
        description="Rotulado de trazabilidad algorítmica (RF-65)",
    )
    aviso_orientativo: str = Field(
        default=AVISO_ORIENTATIVO_INDICE,
        description="Advertencia legal y técnica mandatoria (RF-68, RNF-36, RNF-37)",
    )
    es_evaluacion_profesional: bool = Field(
        default=False,
        description="Garantía de que no reemplaza el dictamen de un perito humano calificado (RF-68)",
    )
    es_medida_vulnerabilidad: bool = Field(
        default=False,
        description="Garantía de que no constituye cálculo formal de vulnerabilidad estructural (RNF-36)",
    )
    cambia_estado_inmueble: bool = Field(
        default=False,
        description="Salvaguarda de que el índice jamás muta de forma autónoma el estado del inmueble (RNF-37, RN-09)",
    )
    calculado_en: datetime = Field(..., description="Timestamp UTC del cálculo")


class ReintentoAnalisisOut(BaseModel):
    """Respuesta a la solicitud de reintento de un análisis pendiente o fallido (RF-64)."""

    mensaje: str
    analisis_id: str
    estado: Literal["PENDIENTE", "PROCESANDO"]
    tarea_id: str | None = None


class PriorizacionSismoItem(BaseModel):
    """Elemento individual del tablero administrativo de triage de inmuebles tras un sismo (RF-66, RF-67)."""

    inmueble_id: str
    direccion: str | None = None
    ciudad: str | None = None
    valor_indice: float
    nivel_prioridad: str
    distancia_sismo_km: float | None = None
    variables: VariablesIndiceOut
    aviso_orientativo: str = AVISO_ORIENTATIVO_INDICE
