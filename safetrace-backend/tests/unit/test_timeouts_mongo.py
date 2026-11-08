from core.config import settings
from core.database import cliente


def test_cliente_mongo_tiene_timeouts():
    opciones = cliente.options.pool_options
    assert opciones.connect_timeout == settings.mongo_connect_timeout_ms / 1000
    assert opciones.socket_timeout == settings.mongo_socket_timeout_ms / 1000
    assert opciones.wait_queue_timeout == settings.mongo_wait_queue_timeout_ms / 1000
