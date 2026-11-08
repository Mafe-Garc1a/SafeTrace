import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.crud import inspecciones as crud_inspecciones
from app.router.dependencies import obtener_inmueble_autorizado


@pytest.fixture
def asignado(monkeypatch):
    monkeypatch.setattr(crud_inspecciones, "perito_asignado_a_inmueble", lambda *_: True)


def test_rol_nuevo_con_permiso_y_asignacion_ve_el_inmueble(db, inmueble, asignado):
    permiso = {"rol": "INSPECTOR_EXTERNO", "modulo": "inspecciones", "seleccionar": True}
    db["permisos"].insert_one(permiso)
    usuario = {"_id": ObjectId(), "rol": "INSPECTOR_EXTERNO"}

    assert obtener_inmueble_autorizado(db, inmueble["id"], usuario)["_id"] == ObjectId(inmueble["id"])


def test_asignado_sin_permiso_de_inspecciones_no_ve_el_inmueble(db, inmueble, asignado):
    # Un perito que cambió de rol conserva su asignación, pero pierde el acceso
    usuario = {"_id": ObjectId(), "rol": "PROPIETARIO"}

    with pytest.raises(HTTPException) as error:
        obtener_inmueble_autorizado(db, inmueble["id"], usuario)
    assert error.value.status_code == 403
