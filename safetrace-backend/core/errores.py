"""Errores comunes de la API. `main.py` los convierte en respuestas HTTP."""

from fastapi.responses import JSONResponse

from core.registro import request_id

# Código estable por estado HTTP: el frontend decide con `codigo`, no con el texto de `detail`
CODIGOS_HTTP = {
    400: "SOLICITUD_INVALIDA",
    401: "NO_AUTENTICADO",
    403: "SIN_PERMISO",
    404: "NO_ENCONTRADO",
    405: "METODO_NO_PERMITIDO",
    409: "CONFLICTO",
    501: "NO_IMPLEMENTADO",
}


class ErrorNegocio(Exception):
    """Regla de negocio rechazada. Cada excepción define su estado HTTP, su código y su mensaje por defecto."""

    status = 409
    codigo = "CONFLICTO"
    mensaje = "La operación no está permitida"

    def __init__(self, mensaje: str | None = None):
        super().__init__(mensaje or self.mensaje)


class IdentificadorInvalido(ErrorNegocio):
    """El id recibido no tiene el formato de MongoDB. Responde 400."""

    status = 400
    codigo = "SOLICITUD_INVALIDA"


class TransicionRechazada(ErrorNegocio):
    """El cambio de estado no está permitido o el estado cambió antes de guardarlo (concurrencia). Responde 409."""

    codigo = "TRANSICION_RECHAZADA"


def respuesta_error(status: int, detail: str, codigo: str, headers: dict | None = None, **extra) -> JSONResponse:
    """Formato único de error; `request_id` permite encontrar la petición en los logs."""
    contenido = {"detail": detail, "codigo": codigo, "request_id": request_id.get(), **extra}
    return JSONResponse(status_code=status, content=contenido, headers=headers)
