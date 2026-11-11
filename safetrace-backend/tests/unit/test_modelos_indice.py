"""Ecuaciones e índice de priorización, con el ejemplo del documento de modelos matemáticos."""

import math
from datetime import UTC, datetime, timedelta

import pytest

from app.crud.configuracion import POR_DEFECTO_INDICE
from app.crud.ia_indice import calcular
from core import modelos_indice as m

MOMENTO = datetime(2026, 11, 6, tzinfo=UTC)

# Ejemplo del documento: 8 pisos, pórticos de concreto, 1998, M 6,1 a 32,4 km y 120 km de profundidad
EJEMPLO = {
    "anio_construccion": 1998,
    "sistema_constructivo": "PORTICOS_CONCRETO",
    "numero_pisos": 8,
    "magnitud": 6.1,
    "distancia_km": 32.4,
    "profundidad_km": 120.0,
    "antecedentes_danos": 1,
    "antecedentes_mantenimiento": 3,
    "fecha_ultima_revision": MOMENTO - timedelta(days=m.DIAS_POR_MES),
}


def test_resonancia_con_r_igual_a_1_y_zeta_5_por_ciento_da_10():
    assert m.factor_resonancia(1, 0.05) == pytest.approx(10)


def test_vibracion_libre_empieza_en_1_y_se_apaga():
    assert m.respuesta_libre(0.8, 0.05, 0) == pytest.approx(1)
    assert abs(m.respuesta_libre(0.8, 0.05, 8)) < 0.1


def test_crecimiento_de_fisura():
    assert m.tasa_crecimiento(0.30, 0.50, 6) == pytest.approx(math.log(0.5 / 0.3) / 6)
    with pytest.raises(ValueError):
        m.tasa_crecimiento(0, 0.5, 6)


def test_valores_del_ejemplo_del_documento():
    omega_n, _ = m.frecuencias(m.periodo_natural(8), 0.05)
    assert m.periodo_natural(8) == pytest.approx(0.8)
    assert omega_n == pytest.approx(7.85, abs=0.01)
    assert m.factor_resonancia(0.8 / 0.6, 0.05) == pytest.approx(1.27, abs=0.01)
    assert m.distancia_hipocentral(32.4, 120) == pytest.approx(124.3, abs=0.05)

    resultado = calcular(EJEMPLO, POR_DEFECTO_INDICE, MOMENTO)
    assert resultado["valor"] == pytest.approx(27.5, abs=0.05)
    assert resultado["variables"]["factor_resonancia"] == pytest.approx(1.267, abs=0.001)
    assert resultado["variables_normalizadas"]["tiempo_sin_revision"] == pytest.approx(1 / 24, abs=1e-4)


def test_indice_siempre_entre_0_y_100():
    peor = {
        **EJEMPLO,
        "anio_construccion": 1850,
        "sistema_constructivo": "MAMPOSTERIA_NO_REFORZADA",
        "numero_pisos": 6,  # T = 0,6 s = Tₛ: resonancia
        "magnitud": 9.5,
        "distancia_km": 0,
        "profundidad_km": 0,  # R = 0 no debe dividir por cero
        "antecedentes_danos": 20,
        "antecedentes_mantenimiento": 0,
        "fecha_ultima_revision": None,
    }
    mejor = {
        **EJEMPLO,
        "anio_construccion": 2030,  # año futuro: la antigüedad no queda negativa
        "sistema_constructivo": "ESTRUCTURA_METALICA",
        "numero_pisos": 30,
        "magnitud": 4.0,  # bajo 5: x₄ no queda negativa
        "distancia_km": 500,
        "antecedentes_danos": 0,
        "antecedentes_mantenimiento": 10,
        "fecha_ultima_revision": MOMENTO,
    }
    assert calcular(peor, POR_DEFECTO_INDICE, MOMENTO)["valor"] == pytest.approx(100)  # todas las xᵢ en 1
    for variables in (peor, mejor):
        resultado = calcular(variables, POR_DEFECTO_INDICE, MOMENTO)
        assert 0 <= resultado["valor"] <= 100
        assert all(0 <= x <= 1 for x in resultado["variables_normalizadas"].values())


def test_pesos_se_normalizan_y_se_validan():
    x = dict.fromkeys(POR_DEFECTO_INDICE["pesos"], 1.0)
    assert m.indice(x, dict.fromkeys(x, 3))[0] == pytest.approx(100)  # no suman 1: se dividen por su suma
    negativo = {**dict.fromkeys(x, 0.2), "magnitud": -0.4}
    incompleto = {"magnitud": 1}
    for pesos in (negativo, incompleto):
        with pytest.raises(ValueError):
            m.indice(x, pesos)


def test_curvas_de_las_graficas():
    vibracion = m.curva_vibracion(0.8, 0.05)
    assert vibracion[0] == {"t": 0, "x": 1}
    resonancia = m.curva_resonancia(0.05)
    assert max(p["factor"] for p in resonancia) == pytest.approx(10, abs=0.1)
    atenuacion = m.curva_atenuacion(120, 100)
    assert atenuacion[0]["distancia_hipocentral_km"] == 120
    assert atenuacion[-1]["amplitud_relativa"] < atenuacion[0]["amplitud_relativa"]
