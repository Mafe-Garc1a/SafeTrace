"""Logs de la aplicación sin datos personales (RNF-20).

Este módulo centraliza la configuración de logging y proporciona funciones auxiliares
para asegurar que ningún registro exponga Información Personalmente Identificable (PII)
como nombres completos, documentos de identidad, correos electrónicos o números telefónicos,
en estricto cumplimiento del requerimiento no funcional RNF-20.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Conjunto de claves sensibles sujetas a filtrado o anonimización estricta (RNF-20)
CAMPOS_PII_SENSIBLES: frozenset[str] = frozenset({
    "nombre",
    "nombre_completo",
    "documento",
    "numero_documento",
    "numero",
    "correo",
    "email",
    "telefono",
    "celular",
    "contrasena",
    "password",
    "contrasena_hash",
    "token",
    "token_hash",
    "matricula_profesional",
})


def obtener_logger(nombre: str) -> logging.Logger:
    """Retorna un logger configurado para el componente solicitado."""
    return logging.getLogger(nombre)


def enmascarar_dato(valor: Any, visible_chars: int = 2) -> str:
    """Enmascara un dato textual sensible preservando longitud mínima para depuración sin revelar PII (RNF-20)."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    if len(texto) <= visible_chars:
        return "***"
    return f"{texto[:visible_chars]}***{texto[-1] if len(texto) > visible_chars + 1 else ''}"


def sanitizar_pii(datos: Any) -> Any:
    """Recorre estructuras de datos y elimina o redacta campos con información personal (RNF-20).

    Preserva identificadores de sistema (IDs, usuario_id, timestamps, estados)
    y enmascara o sustituye valores de contacto, identidad civil o credenciales.
    """
    if isinstance(datos, Mapping):
        limpio: dict[str, Any] = {}
        for clave, val in datos.items():
            clave_lower = str(clave).lower()
            if clave_lower in CAMPOS_PII_SENSIBLES:
                limpio[clave] = "[PROTEGIDO_RNF20]"
            elif isinstance(val, (Mapping, list, tuple, set)):
                limpio[clave] = sanitizar_pii(val)
            else:
                limpio[clave] = val
        return limpio
    elif isinstance(datos, (list, tuple, set)):
        return [sanitizar_pii(item) for item in datos]
    return datos


def registrar_evento_seguro(
    logger: logging.Logger,
    evento: str,
    contexto: dict[str, Any] | None = None,
    nivel: str = "info",
) -> None:
    """Emite una línea de log estructurada con el contexto completamente sanitizado de PII (RNF-20)."""
    ctx_limpio = sanitizar_pii(contexto) if contexto else {}
    mensaje = f"{evento} | contexto={ctx_limpio}"
    metodo_log = getattr(logger, nivel.lower(), logger.info)
    metodo_log(mensaje)
