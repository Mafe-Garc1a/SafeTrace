import pytest
from bson import ObjectId

from app.crud import inspecciones as crud_inspecciones
from app.crud import peritos as crud_peritos


def test_asignar_una_solicitud_que_cambio_no_notifica_ni_audita(db, monkeypatch):
    monkeypatch.setattr(crud_peritos, "perito_habilitado", lambda *_: True)
    solicitud_id = db["solicitudes_inspeccion"].insert_one({"estado": "FIRMADA"}).inserted_id
    leida_antes = {"_id": solicitud_id, "estado": "SOLICITADA"}  # otro administrador la cambió después

    with pytest.raises(crud_inspecciones.ReglaInspeccion):
        crud_inspecciones.asignar_perito(db, leida_antes, ObjectId(), ObjectId(), {"id": ObjectId()})

    assert db["notificaciones"].count_documents({}) == 0
    assert db["auditoria"].count_documents({"accion": "ASIGNAR_PERITO"}) == 0


def test_firmar_sin_solicitud_no_guarda_la_firma(db, monkeypatch):
    monkeypatch.setattr(crud_inspecciones, "_verificar_autor", lambda *_: {})
    inspeccion = {"solicitud_id": ObjectId(), "firma": {"firmada": False}, "constancia": None}
    inspeccion["_id"] = db["inspecciones"].insert_one(inspeccion).inserted_id

    with pytest.raises(crud_inspecciones.ReglaInspeccion):
        crud_inspecciones.firmar(db, inspeccion, 6, {"_id": ObjectId()})

    assert db["inspecciones"].find_one({"_id": inspeccion["_id"]})["firma"]["firmada"] is False
