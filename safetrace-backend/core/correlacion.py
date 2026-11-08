"""Correlación de peticiones: cada una lleva un ID que aparece en sus logs, su respuesta y sus errores."""

import re
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.errores import respuesta_error
from core.registro import obtener_logger, request_id

ENCABEZADO = "X-Request-ID"
# El ID recibido llega a los logs: solo se acepta si no puede inyectar texto en ellos
ID_VALIDO = re.compile(r"[A-Za-z0-9_-]{8,64}")

log = obtener_logger("api")


class MiddlewareCorrelacion:
    """Asigna el ID y responde los errores no previstos.

    Debe registrarse antes que CORSMiddleware para quedar dentro de él: un manejador de `Exception`
    corre fuera de todos los middlewares y sus respuestas 500 saldrían sin encabezados de CORS.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        recibido = Headers(scope=scope).get(ENCABEZADO, "")
        valor = recibido if ID_VALIDO.fullmatch(recibido) else uuid4().hex
        token = request_id.set(valor)
        respuesta_iniciada = False

        async def enviar(mensaje: Message) -> None:
            nonlocal respuesta_iniciada
            if mensaje["type"] == "http.response.start":
                respuesta_iniciada = True
                MutableHeaders(scope=mensaje)[ENCABEZADO] = valor
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        except Exception as exc:
            log.error("Error no previsto: %s", type(exc).__name__, exc_info=exc)
            if respuesta_iniciada:
                raise
            await respuesta_error(500, "Error interno del servidor", "ERROR_INTERNO")(scope, receive, enviar)
        finally:
            request_id.reset(token)
