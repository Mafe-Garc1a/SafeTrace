"""Esquemas Pydantic para el Módulo B: Peritos (RF-13 a RF-16, RNF-15, RNF-20).

Define los contratos de datos para:
- RF-13: Registro del perfil profesional (nombre completo, documento, profesión, especialidad, matrícula).
- RF-14: Carga y acreditación de documentos de soporte de formación y matrícula.
- RF-15: Validación administrativa de credenciales (aprobación/rechazo).
- RF-16: Auditoría de validación (quién validó, cuándo y qué documentos revisó).
- RNF-15: Estados de credencial (REGISTRADO, PENDIENTE_VALIDACION, VALIDADO, RECHAZADO, VENCIDO, INCONSISTENTE).
- RNF-20: Protección pasiva de PII y saneamiento de entradas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DocumentoIdentidad(BaseModel):
    """Documento de identificación civil del perito (RF-13)."""

    tipo: str = Field(..., description="Tipo de documento (ej. CC, CE, PASAPORTE)")
    numero: str = Field(..., description="Número de documento de identidad")

    @field_validator("tipo", "numero")
    @classmethod
    def normalizar_texto(cls, v: str) -> str:
        return v.strip().upper() if v else v


class ArchivoSoporte(BaseModel):
    """Referencia del archivo almacenado con integridad verificable (RF-14)."""

    ruta: str = Field(..., description="Ruta de almacenamiento del documento")
    hash_sha256: str = Field(..., description="Hash SHA-256 para verificación de integridad documental")

    @field_validator("ruta", "hash_sha256")
    @classmethod
    def normalizar_archivo(cls, v: str) -> str:
        return v.strip() if v else v


class DocumentoSoporte(BaseModel):
    """Documento probatorio aportado por el perito (RF-14)."""

    id: str | None = Field(default=None, description="Identificador único del documento")
    tipo: str = Field(
        ...,
        description="Tipo de soporte (ej. MATRICULA, TITULO_PREGRADO, TITULO_POSGRADO, CERTIFICADO_VIGENCIA)",
    )
    archivo: ArchivoSoporte
    subido_en: datetime | None = Field(default=None, description="Fecha y hora de carga en UTC")

    @field_validator("tipo")
    @classmethod
    def normalizar_tipo(cls, v: str) -> str:
        return v.strip().upper() if v else v


class RegistroValidacion(BaseModel):
    """Trazabilidad formal de una decisión administrativa sobre las credenciales (RF-16)."""

    validador_id: str = Field(..., description="ID del administrador general que emitió el dictamen")
    fecha: datetime = Field(..., description="Fecha y hora de la revisión en UTC")
    decision: Literal["APROBADO", "RECHAZADO"] = Field(..., description="Dictamen de validación")
    documentos_revisados: list[str] = Field(
        default_factory=list,
        description="Lista de identificadores o códigos de documentos revisados",
    )
    motivo: str | None = Field(default=None, description="Observaciones o motivación técnica de la decisión")


class PerfilPeritoCreate(BaseModel):
    """Cuerpo de solicitud para registro inicial del perfil profesional del perito (RF-13)."""

    documento: DocumentoIdentidad
    profesion: str = Field(..., min_length=3, description="Profesión acreditada (ej. Ingeniero Civil, Arquitecto)")
    especialidad: str = Field(..., min_length=3, description="Especialidad técnica (ej. Estructuras, Geotecnia)")
    matricula_profesional: str = Field(..., min_length=3, description="Número de tarjeta o matrícula profesional oficial")

    @field_validator("profesion", "especialidad", "matricula_profesional")
    @classmethod
    def limpiar_espacios(cls, v: str) -> str:
        return v.strip() if v else v


class DocumentosPeritoCreate(BaseModel):
    """Cuerpo de solicitud para adjuntar soportes de matrícula y formación académica (RF-14)."""

    documentos: list[DocumentoSoporte] = Field(
        ...,
        min_length=1,
        description="Colección de soportes que respaldan la idoneidad profesional",
    )


class ValidacionPeritoCreate(BaseModel):
    """Cuerpo de solicitud para que el Administrador General apruebe o rechace credenciales (RF-15, RF-16)."""

    decision: Literal["APROBADO", "RECHAZADO"] = Field(..., description="Resolución administrativa")
    documentos_revisados: list[str] = Field(
        default_factory=list,
        description="Lista de documentos cotejados durante el proceso de verificación (RF-16)",
    )
    motivo: str | None = Field(default=None, description="Motivación de la resolución")

    @field_validator("decision")
    @classmethod
    def normalizar_decision(cls, v: str) -> str:
        return v.strip().upper() if v else v


class InconsistenciaPeritoCreate(BaseModel):
    """Cuerpo de solicitud para señalar inconsistencias en las credenciales (RNF-15)."""

    motivo: str = Field(..., min_length=5, description="Descripción técnica de la inconsistencia detectada")

    @field_validator("motivo")
    @classmethod
    def limpiar_motivo(cls, v: str) -> str:
        return v.strip() if v else v


class PeritoOut(BaseModel):
    """Representación pública/estándar del perito y estado de sus credenciales (RF-13, RF-15, RNF-15)."""

    id: str = Field(..., description="Identificador del expediente de perito")
    usuario_id: str = Field(..., description="Identificador de la cuenta de usuario asociada")
    documento: DocumentoIdentidad
    profesion: str
    especialidad: str
    matricula_profesional: str
    estado_credencial: Literal[
        "REGISTRADO",
        "PENDIENTE_VALIDACION",
        "VALIDADO",
        "RECHAZADO",
        "VENCIDO",
        "INCONSISTENTE",
    ] = Field(..., description="Estado normativo de habilitación (RNF-15)")
    documentos: list[dict[str, Any]] = Field(default_factory=list, description="Documentación de respaldo adjunta")
    validaciones: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historial inmutable de auditoría de validaciones (RF-16)",
    )
    creado_en: datetime
    actualizado_en: datetime | None = None
    motivo_inconsistencia: str | None = None
    vigente_hasta: datetime | None = None


class PeritoMiEstadoOut(BaseModel):
    """Resumen de consulta para el perito autenticado sobre su habilitación técnica (RNF-15)."""

    perito_id: str
    estado_credencial: str
    habilitado_para_inspeccionar: bool = Field(
        ...,
        description="Indica si cuenta con habilitación efectiva para realizar inspecciones (RNF-15, RN-01)",
    )
    matricula_profesional: str
    total_documentos: int
    ultima_validacion: dict[str, Any] | None = None

