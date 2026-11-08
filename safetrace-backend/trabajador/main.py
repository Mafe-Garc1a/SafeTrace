"""Bucle del trabajador: ejecuta la colección `tareas` (RNF-03).

Ejecutar en otra terminal, junto a la API:  python -m trabajador.main
"""

import os
import socket
import threading
import time
from contextlib import contextmanager
from contextvars import copy_context

from app.crud import notificaciones as crud_notificaciones
from core.circuito import ProveedorNoDisponible
from core.config import settings
from core.database import obtener_db
from core.registro import obtener_logger, request_id
from trabajador.tareas import EJECUTORES

log = obtener_logger("trabajador")
NOMBRE = f"{socket.gethostname()}-{os.getpid()}"
ESPERA_SEGUNDOS = 2


class TiempoAgotado(Exception):
    """La tarea superó SEGUNDOS_MAXIMOS_TAREA."""


def correr_con_limite(funcion, *args) -> None:
    """Ejecuta en un hilo y espera hasta el límite. Un hilo no se puede detener: ver `ejecutar`."""
    errores = []

    def correr():
        try:
            funcion(*args)
        except Exception as e:
            errores.append(e)

    # Un hilo nuevo no hereda el contexto: sin esto, sus logs perderían el request_id
    hilo = threading.Thread(target=copy_context().run, args=(correr,), daemon=True)
    hilo.start()
    hilo.join(settings.segundos_maximos_tarea)
    if hilo.is_alive():
        raise TiempoAgotado
    if errores:
        raise errores[0]


@contextmanager
def con_request_id(tarea: dict):
    """Los logs de la tarea llevan el ID de la petición que la creó."""
    token = request_id.set(tarea.get("request_id", "-"))
    try:
        yield
    finally:
        request_id.reset(token)


def registrar_fallo(db, tarea: dict, error: str, motivo: str) -> None:
    """Devuelve la tarea a PENDIENTE o la deja FALLIDA, y avisa a su ejecutor (RNF-24)."""
    definitiva = crud_notificaciones.fallar_tarea(db, tarea, error)
    log.warning("tarea %s falló (%s); definitiva=%s", tarea["_id"], motivo, definitiva)
    al_fallar = getattr(EJECUTORES.get(tarea["tipo"]), "al_fallar", None)
    if al_fallar:
        al_fallar(db, tarea, definitiva)


def ejecutar(db, tarea: dict) -> None:
    """Ejecuta una tarea; si falla la devuelve a PENDIENTE o la deja FALLIDA (RNF-24)."""
    log.info("tarea %s tipo=%s intento=%s", tarea["_id"], tarea["tipo"], tarea["intentos"])  # sin datos personales
    modulo = EJECUTORES.get(tarea["tipo"])
    try:
        if modulo is None:
            raise NotImplementedError(f"Tipo de tarea sin ejecutor: {tarea['tipo']}")
        correr_con_limite(modulo.ejecutar, db, tarea)
        crud_notificaciones.completar_tarea(db, tarea["_id"])
    except ProveedorNoDisponible as e:
        log.warning("tarea %s pospuesta: %s", tarea["_id"], e)
        crud_notificaciones.posponer_tarea(db, tarea, e.segundos)
        al_fallar = getattr(modulo, "al_fallar", None)
        if al_fallar:
            al_fallar(db, tarea, False)
    except TiempoAgotado:
        registrar_fallo(db, tarea, "Superó el tiempo máximo", "tiempo agotado")
        # El hilo sigue vivo y podría terminar la tarea mientras otro la reintenta: se cierra el proceso
        log.critical("trabajador %s se cierra: tarea %s colgada", NOMBRE, tarea["_id"])
        os._exit(1)
    except Exception as e:
        registrar_fallo(db, tarea, f"{type(e).__name__}: {e}", type(e).__name__)


def recuperar_atascadas(db) -> None:
    """Libera las tareas que un trabajador caído dejó en PROCESANDO."""
    while tarea := crud_notificaciones.tomar_tarea_atascada(db, settings.minutos_tarea_atascada):
        with con_request_id(tarea):
            registrar_fallo(db, tarea, "Abandonada en PROCESANDO", "atascada")


def ciclo():
    db = obtener_db()
    log.info("trabajador %s iniciado", NOMBRE)

    while True:
        recuperar_atascadas(db)
        tarea = crud_notificaciones.tomar_tarea(db, NOMBRE)
        if tarea is None:
            time.sleep(ESPERA_SEGUNDOS)
            continue
        with con_request_id(tarea):
            ejecutar(db, tarea)

if __name__ == "__main__":
    ciclo()
