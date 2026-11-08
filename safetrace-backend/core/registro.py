"""Logs de la aplicación sin datos personales (RNF-20)."""

import logging
from contextvars import ContextVar

# ID de la petición en curso; "-" fuera de una petición (arranque, trabajador)
request_id: ContextVar[str] = ContextVar("request_id", default="-")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s")

_crear_registro = logging.getLogRecordFactory()


def _registro_con_request_id(*args, **kwargs) -> logging.LogRecord:
    # En la fábrica y no en un filtro: los filtros de un logger no aplican a los registros de sus hijos
    registro = _crear_registro(*args, **kwargs)
    registro.request_id = request_id.get()
    return registro


logging.setLogRecordFactory(_registro_con_request_id)


def obtener_logger(nombre: str) -> logging.Logger:
    return logging.getLogger(nombre)
