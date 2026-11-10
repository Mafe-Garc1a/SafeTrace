import logging

from core.database import get_db
from core.registro import obtener_logger
from main import app

ID = "prueba-correlacion-1"


def test_genera_un_id_si_no_llega(cliente):
    assert len(cliente.get("/salud").headers["X-Request-ID"]) == 32


def test_conserva_el_id_recibido(cliente):
    r = cliente.get("/salud", headers={"X-Request-ID": ID})
    assert r.headers["X-Request-ID"] == ID


def test_rechaza_un_id_que_podria_alterar_los_logs(cliente):
    r = cliente.get("/salud", headers={"X-Request-ID": "corto; falso log"})
    assert len(r.headers["X-Request-ID"]) == 32


def test_el_error_lleva_el_mismo_id_que_el_encabezado(cliente):
    r = cliente.get("/no-existe", headers={"X-Request-ID": ID})
    assert r.status_code == 404
    assert r.json()["request_id"] == ID
    assert r.headers["X-Request-ID"] == ID


def test_error_no_previsto_responde_500_con_cors_e_id(cliente, caplog):
    def fallar():
        raise RuntimeError("detalle interno")

    app.dependency_overrides[get_db] = fallar
    encabezados = {"Origin": "http://localhost:3000", "X-Request-ID": ID, "Authorization": "Bearer token"}
    with caplog.at_level(logging.ERROR, logger="api"):
        r = cliente.get("/zonas", headers=encabezados)

    assert r.status_code == 500
    assert r.json() == {"detail": "Error interno del servidor", "codigo": "ERROR_INTERNO", "request_id": ID}
    assert r.headers["X-Request-ID"] == ID
    assert "access-control-allow-origin" in r.headers
    assert "X-Request-ID" in r.headers["access-control-expose-headers"]
    assert any(registro.request_id == ID for registro in caplog.records)


def test_fuera_de_una_peticion_el_log_usa_guion(caplog):
    with caplog.at_level(logging.INFO, logger="api"):
        obtener_logger("api").info("sin peticion")
    assert caplog.records[-1].request_id == "-"
