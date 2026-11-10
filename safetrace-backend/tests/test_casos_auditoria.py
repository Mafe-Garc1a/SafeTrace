"""Casos que el registro de auditoría marcaba sin prueba registrada."""

from datetime import timedelta

from bson import ObjectId

from app.crud import usuarios as crud_usuarios
from core.config import settings
from core.fechas import ahora


def retroceder_actividad(db, minutos: int) -> dict:
    sesion = db["sesiones"].find_one()
    actividad = ahora() - timedelta(minutes=minutos)
    db["sesiones"].update_one({"_id": sesion["_id"]}, {"$set": {"ultima_actividad": actividad}})
    return db["sesiones"].find_one({"_id": sesion["_id"]})


def test_sesion_no_escribe_antes_del_intervalo_de_renovacion(db, propietario):
    sesion = db["sesiones"].find_one()

    vigente = crud_usuarios.obtener_sesion_vigente(db, sesion["token_hash"])

    assert vigente["ultima_actividad"] == sesion["ultima_actividad"]
    assert vigente["expira_en"] == sesion["expira_en"]


def test_sesion_se_renueva_por_30_minutos_y_no_por_30_dias(db, propietario):
    sesion = retroceder_actividad(db, settings.minutos_renovacion_sesion + 1)

    renovada = crud_usuarios.obtener_sesion_vigente(db, sesion["token_hash"])

    assert renovada["ultima_actividad"] > sesion["ultima_actividad"]
    duracion = renovada["expira_en"] - renovada["ultima_actividad"]
    assert duracion == timedelta(minutes=settings.minutos_sesion)


def test_segunda_solicitud_en_curso_responde_409_regla_inspeccion(cliente, propietario, inmueble):
    ruta = f"/inmuebles/{inmueble['id']}/solicitudes-inspeccion"
    datos = {"motivo": "Fisura en el muro"}
    assert cliente.post(ruta, json=datos, headers=propietario).status_code == 201

    r = cliente.post(ruta, json=datos, headers=propietario)

    assert r.status_code == 409
    assert r.json()["codigo"] == "REGLA_INSPECCION"


def test_constancia_sin_perito_registrado_responde_404(cliente, db):
    db["inspecciones"].insert_one(
        {
            "perito_id": ObjectId(),
            "inmueble_id": ObjectId(),
            "firma": {"firmada": True},
            "constancia": {"codigo": "CODIGOPRUEBA"},
        }
    )

    r = cliente.get("/constancias/CODIGOPRUEBA")

    assert r.status_code == 404
    assert r.json()["detail"] == "El perito de esta constancia ya no está registrado"
    assert r.json()["codigo"] == "NO_ENCONTRADO"
