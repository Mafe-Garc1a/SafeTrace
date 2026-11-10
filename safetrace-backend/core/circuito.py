"""Circuit breaker: tras varios fallos seguidos de un proveedor, deja de llamarlo por un tiempo.

El estado vive en cada proceso: cada trabajador abre su propio circuito.
"""

import time
from collections.abc import Callable

from core.config import settings
from core.registro import obtener_logger

log = obtener_logger("circuito")


class ProveedorNoDisponible(Exception):
    """El circuito está abierto. La tarea se pospone sin gastar un intento."""

    def __init__(self, proveedor: str, segundos: float):
        super().__init__(f"Proveedor {proveedor} no disponible")
        self.segundos = segundos


class Circuito:
    def __init__(self, proveedor: str):
        self.proveedor = proveedor
        self.fallos = 0
        self.abierto_hasta = 0.0

    def llamar(self, funcion: Callable, *args, **kwargs):
        restante = self.abierto_hasta - time.monotonic()
        if restante > 0:
            raise ProveedorNoDisponible(self.proveedor, restante)
        try:
            resultado = funcion(*args, **kwargs)
        except NotImplementedError:
            raise  # proveedor sin integrar: no es una caída y la tarea debe fallar normalmente
        except Exception:
            self.fallos += 1
            # Sin reiniciar `fallos`: al cerrar el tiempo, un solo fallo vuelve a abrir el circuito
            if self.fallos >= settings.fallos_maximos_proveedor:
                self.abierto_hasta = time.monotonic() + settings.segundos_circuito_abierto
                log.warning("circuito abierto proveedor=%s", self.proveedor)
            raise
        self.fallos = 0
        return resultado
