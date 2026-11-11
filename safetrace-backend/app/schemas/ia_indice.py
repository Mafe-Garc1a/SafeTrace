"""Modelos Pydantic de salida de J · Análisis de IA e índice de priorización (RF-62 a RF-68)."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class ResultadoAnalisis(BaseModel):
    cambio_detectado: bool
    descripcion: str
    confianza: float


class AnalisisOut(BaseModel):
    id: str
    inmueble_id: str
    zona_id: str
    evidencia_anterior_id: str
    evidencia_nueva_id: str
    estado: Literal["PENDIENTE", "PROCESANDO", "COMPLETADO", "FALLIDO", "REEMPLAZADO"]
    tarea_id: str | None = None
    resultado: ResultadoAnalisis | None = None
    leyenda: str  # «Análisis automático mediante IA» (RF-65)
    modelo_version: str
    completado_en: datetime | None = None
    creado_en: datetime


class AnalisisPage(BaseModel):
    pagina: int
    tamano: int
    total: int
    total_paginas: int
    datos: list[AnalisisOut]


class IndiceOut(BaseModel):
    id: str
    inmueble_id: str
    sismo_id: str
    valor: float
    variables: dict[str, Any]  # tal como se usaron, con periodo, F y R (RF-67)
    variables_normalizadas: dict[str, float] | None = None  # xᵢ de 0 a 1
    pesos: dict[str, float] | None = None  # wᵢ usados en este cálculo
    aportes: dict[str, float] | None = None  # 100·wᵢ·xᵢ
    parametros: dict[str, float] | None = None  # ζ y Tₛ usados
    aviso: str  # orientativo, no es evaluación profesional (RF-68)
    formula_version: str
    calculado_en: datetime


class CurvaModelo(BaseModel):
    ecuacion: str
    parametros: dict[str, Any]
    puntos: list[dict[str, float]]


class ModelosIndiceOut(BaseModel):
    """Puntos de las gráficas de la vista del índice. Se calculan al pedirlos, no se guardan."""

    inmueble_id: str
    sismo_id: str
    formula_version: str
    aviso: str  # RF-68
    vibracion_libre: CurvaModelo
    resonancia: CurvaModelo
    atenuacion: CurvaModelo


class IndicePage(BaseModel):
    pagina: int
    tamano: int
    total: int
    total_paginas: int
    datos: list[IndiceOut]
