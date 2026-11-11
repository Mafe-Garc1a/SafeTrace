"""Índice de priorización calculado al marcar inmuebles por un sismo (RF-66 a RF-68, RNF-24, RNF-37)."""

import pytest

from app.crud import ia_indice as crud_ia_indice
from tests.conftest import N8N, iniciar_sesion, registrar
from tests.test_flujo_sismo import SISMO


def test_sismo_relevante_calcula_el_indice_con_sus_modelos(cliente, db, propietario, inmueble):
    cliente.post("/interno/sismos", json=SISMO, headers=N8N)

    indice = cliente.get(f"/inmuebles/{inmueble['id']}/indice", headers=propietario).json()
    assert 0 <= indice["valor"] <= 100
    assert indice["formula_version"] == "v2-edo"
    assert indice["aviso"].startswith("Índice orientativo")
    assert indice["variables"]["periodo_s"] == 0.5  # 5 pisos
    assert indice["variables"]["profundidad_km"] == SISMO["profundidad_km"]
    assert indice["pesos"] == db["configuracion"].find_one({"_id": "parametros_indice"})["pesos"]
    assert sum(indice["aportes"].values()) == pytest.approx(indice["valor"], abs=0.05)

    # El índice no cambia el estado: el 2 lo puso el marcado por sismo (RNF-37)
    assert db["inmuebles"].find_one()["estado"]["codigo"] == 2

    modelos = cliente.get(f"/inmuebles/{inmueble['id']}/indice/modelos", headers=propietario).json()
    assert modelos["aviso"] == indice["aviso"]
    assert modelos["vibracion_libre"]["puntos"][0] == {"t": 0, "x": 1}
    assert modelos["resonancia"]["parametros"]["factor_resonancia"] == indice["variables"]["factor_resonancia"]
    assert (
        modelos["atenuacion"]["parametros"]["distancia_hipocentral_km"]
        == (indice["variables"]["distancia_hipocentral_km"])
    )


def test_modelos_sin_indice_y_de_otro_propietario(cliente, propietario, inmueble):
    assert cliente.get(f"/inmuebles/{inmueble['id']}/indice/modelos", headers=propietario).status_code == 404
    cliente.post("/interno/sismos", json=SISMO, headers=N8N)
    registrar(cliente, "otro@correo.com")
    otro = iniciar_sesion(cliente, "otro@correo.com")
    assert cliente.get(f"/inmuebles/{inmueble['id']}/indice/modelos", headers=otro).status_code == 403


def test_si_el_indice_falla_el_marcado_sigue(cliente, db, inmueble, monkeypatch):
    def falla(*_):
        raise ValueError("pesos mal configurados")

    monkeypatch.setattr(crud_ia_indice, "calcular_indice", falla)
    r = cliente.post("/interno/sismos", json=SISMO, headers=N8N).json()
    assert r["sismo"]["inmuebles_marcados"] == 1
    assert db["inmuebles"].find_one()["estado"]["codigo"] == 2
    assert db["notificaciones"].count_documents({"tipo": "INMUEBLE_MARCADO_POR_SISMO"}) == 1
    assert db["indices_priorizacion"].count_documents({}) == 0
