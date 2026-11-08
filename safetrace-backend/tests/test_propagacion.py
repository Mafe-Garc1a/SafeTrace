from types import SimpleNamespace

import pytest

from app.crud import notificaciones as crud_notificaciones
from core.database import a_object_id
from core.errores import IdentificadorInvalido
from core.registro import request_id
from trabajador import main as trabajador

ID = "peticion-original-1"


def test_la_tarea_guarda_el_id_de_la_peticion_y_el_trabajador_lo_usa(db, monkeypatch):
    vistos = []
    monkeypatch.setitem(
        trabajador.EJECUTORES, "PRUEBA", SimpleNamespace(ejecutar=lambda *_: vistos.append(request_id.get()))
    )
    token = request_id.set(ID)
    crud_notificaciones.encolar_tarea(db, "PRUEBA", {})
    request_id.reset(token)

    tarea = crud_notificaciones.tomar_tarea(db, "prueba")
    assert tarea["request_id"] == ID
    with trabajador.con_request_id(tarea):
        trabajador.ejecutar(db, tarea)

    assert vistos == [ID]  # visto dentro del hilo de la tarea
    assert request_id.get() == "-"


def test_tarea_antigua_sin_request_id_no_falla():
    with trabajador.con_request_id({}):
        assert request_id.get() == "-"


def test_identificador_invalido_no_depende_de_http():
    with pytest.raises(IdentificadorInvalido):
        a_object_id("no-es-un-id")


def test_identificador_invalido_conserva_la_respuesta_400(cliente, propietario):
    r = cliente.get("/inmuebles/no-es-un-id", headers=propietario)
    assert r.status_code == 400
    assert r.json()["codigo"] == "SOLICITUD_INVALIDA"
    assert r.json()["detail"] == "Identificador inválido: no-es-un-id"
