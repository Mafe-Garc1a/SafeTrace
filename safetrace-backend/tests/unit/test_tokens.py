from datetime import UTC, datetime, timedelta

import jwt

from core.config import settings
from core.security import create_access_token, verify_token


def test_token_valido_devuelve_el_usuario():
    assert verify_token(create_access_token({"sub": "usuario-1"})) == "usuario-1"


def test_token_vencido_no_es_valido():
    vencimiento = datetime.now(tz=UTC) - timedelta(minutes=1)
    token = jwt.encode({"sub": "usuario-1", "exp": vencimiento}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    assert verify_token(token) is None


def test_token_con_otro_secreto_no_es_valido():
    token = jwt.encode({"sub": "usuario-1"}, "otro-secreto-de-prueba-suficientemente-largo", algorithm="HS256")
    assert verify_token(token) is None
