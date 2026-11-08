import pytest

from core.circuito import Circuito, ProveedorNoDisponible
from core.config import settings


def fallar():
    raise ConnectionError("proveedor caído")


def abrir(circuito):
    for _ in range(settings.fallos_maximos_proveedor):
        with pytest.raises(ConnectionError):
            circuito.llamar(fallar)


def test_abre_tras_los_fallos_seguidos_y_no_llama_al_proveedor():
    circuito = Circuito("prueba")
    abrir(circuito)
    llamadas = []
    with pytest.raises(ProveedorNoDisponible):
        circuito.llamar(llamadas.append, 1)
    assert llamadas == []


def test_un_exito_reinicia_los_fallos():
    circuito = Circuito("prueba")
    with pytest.raises(ConnectionError):
        circuito.llamar(fallar)
    assert circuito.llamar(lambda: "ok") == "ok"
    assert circuito.fallos == 0


def test_al_cerrar_el_tiempo_un_fallo_vuelve_a_abrirlo():
    circuito = Circuito("prueba")
    abrir(circuito)
    circuito.abierto_hasta = 0.0
    with pytest.raises(ConnectionError):
        circuito.llamar(fallar)
    with pytest.raises(ProveedorNoDisponible):
        circuito.llamar(fallar)


def test_proveedor_sin_integrar_no_abre_el_circuito():
    def sin_integrar():
        raise NotImplementedError

    circuito = Circuito("prueba")
    for _ in range(settings.fallos_maximos_proveedor + 1):
        with pytest.raises(NotImplementedError):
            circuito.llamar(sin_integrar)
    assert circuito.fallos == 0
