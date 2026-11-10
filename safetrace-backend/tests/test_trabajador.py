import threading
from types import SimpleNamespace

import pytest

from app.crud import notificaciones as crud_notificaciones
from core.circuito import ProveedorNoDisponible
from core.config import settings
from trabajador import main as trabajador


def tomar(db, monkeypatch, ejecutor) -> dict:
    monkeypatch.setitem(trabajador.EJECUTORES, "PRUEBA", ejecutor)
    crud_notificaciones.encolar_tarea(db, "PRUEBA", {})
    return crud_notificaciones.tomar_tarea(db, "prueba")


def test_tarea_correcta_queda_completada(db, monkeypatch):
    tarea = tomar(db, monkeypatch, SimpleNamespace(ejecutar=lambda *_: None))
    trabajador.ejecutar(db, tarea)
    assert db["tareas"].find_one({"_id": tarea["_id"]})["estado"] == "COMPLETADA"


def test_error_de_la_tarea_gasta_un_intento(db, monkeypatch):
    def fallar(*_):
        raise ValueError("fallo")

    tarea = tomar(db, monkeypatch, SimpleNamespace(ejecutar=fallar))
    trabajador.ejecutar(db, tarea)
    guardada = db["tareas"].find_one({"_id": tarea["_id"]})
    assert (guardada["estado"], guardada["intentos"]) == ("PENDIENTE", 1)
    assert "ValueError" in guardada["error"]


def test_proveedor_no_disponible_pospone_sin_gastar_intento(db, monkeypatch):
    avisos = []

    def rechazar(*_):
        raise ProveedorNoDisponible("correo", 30)

    ejecutor = SimpleNamespace(ejecutar=rechazar, al_fallar=lambda _db, _tarea, definitiva: avisos.append(definitiva))
    tarea = tomar(db, monkeypatch, ejecutor)
    trabajador.ejecutar(db, tarea)

    guardada = db["tareas"].find_one({"_id": tarea["_id"]})
    assert (guardada["estado"], guardada["intentos"]) == ("PENDIENTE", 0)
    assert guardada["disponible_desde"] > tarea["tomada_en"]
    assert avisos == [False]


def test_tarea_colgada_registra_el_fallo_y_cierra_el_proceso(db, monkeypatch):
    liberar = threading.Event()
    tarea = tomar(db, monkeypatch, SimpleNamespace(ejecutar=lambda *_: liberar.wait(5)))
    monkeypatch.setattr(settings, "segundos_maximos_tarea", 0.05, raising=False)

    def salir(codigo):
        raise SystemExit(codigo)

    monkeypatch.setattr(trabajador.os, "_exit", salir)
    with pytest.raises(SystemExit):
        trabajador.ejecutar(db, tarea)
    liberar.set()

    guardada = db["tareas"].find_one({"_id": tarea["_id"]})
    assert guardada["estado"] == "PENDIENTE"
    assert "tiempo máximo" in guardada["error"]
