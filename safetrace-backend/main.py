"""Punto de entrada de la API: crea FastAPI y registra los routers.

Ejecutar en local:  uvicorn main:app --reload
Documentación interactiva: http://localhost:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError
from starlette.exceptions import HTTPException

from app.router import (
    auditoria,
    auth,
    bitacora,
    configuracion,
    enlaces,
    estados,
    ia_indice,
    inmuebles,
    inspecciones,
    modulos,
    notificaciones,
    peritos,
    permisos,
    revisiones,
    roles,
    sismos,
    usuarios,
)
from core.config import settings
from core.correlacion import ENCABEZADO, MiddlewareCorrelacion
from core.errores import CODIGOS_HTTP, ErrorNegocio, respuesta_error
from core.registro import obtener_logger

log = obtener_logger("api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
)

# Incluir en el objeto app los routers
app.include_router(auth.router, prefix="/auth", tags=["Acceso"])
app.include_router(usuarios.router, tags=["Usuarios"])
app.include_router(auditoria.router, tags=["Auditoría"])
app.include_router(configuracion.router, tags=["Configuración"])
app.include_router(roles.router, tags=["Roles"])
app.include_router(modulos.router, tags=["Módulos"])
app.include_router(permisos.router, tags=["Permisos"])
app.include_router(peritos.router, tags=["Peritos"])
app.include_router(inmuebles.router, tags=["Inmuebles"])
app.include_router(bitacora.router, tags=["Bitácora y evidencias"])
app.include_router(revisiones.router, tags=["Revisión del propietario"])
app.include_router(sismos.router, tags=["Sismos"])
app.include_router(estados.router, tags=["Estados del inmueble"])
app.include_router(inspecciones.router, tags=["Inspecciones y constancias"])
app.include_router(enlaces.router, tags=["Enlace público"])
app.include_router(ia_indice.router, tags=["IA e índice de priorización"])
app.include_router(notificaciones.router, tags=["Notificaciones y procesos"])

# El último middleware registrado es el más externo: la correlación debe quedar dentro de CORS
app.add_middleware(MiddlewareCorrelacion)

# Configuración de CORS para permitir todas las solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir solicitudes desde cualquier origen
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Permitir estos métodos HTTP
    allow_headers=["*"],  # Permitir cualquier encabezado en las solicitudes
    expose_headers=[ENCABEZADO],  # El frontend puede leer el ID para reportar un error
)


# Errores comunes: se responden igual en todos los routers y sin filtrar detalles internos
@app.exception_handler(HTTPException)
def error_http(_: Request, exc: HTTPException):
    return respuesta_error(exc.status_code, exc.detail, CODIGOS_HTTP.get(exc.status_code, "ERROR_HTTP"), exc.headers)


@app.exception_handler(RequestValidationError)
def error_validacion(_: Request, exc: RequestValidationError):
    # Sin `input`: devolvería lo que envió el usuario, incluidas contraseñas
    errores = [{"campo": ".".join(str(parte) for parte in e["loc"][1:]), "mensaje": e["msg"]} for e in exc.errors()]
    return respuesta_error(422, "Datos inválidos", "VALIDACION", errores=errores)


@app.exception_handler(ErrorNegocio)
def error_negocio(_: Request, exc: ErrorNegocio):
    return respuesta_error(exc.status, str(exc), exc.codigo)


@app.exception_handler(PyMongoError)
def error_base_datos(_: Request, exc: PyMongoError):
    log.error("Error de base de datos: %s", type(exc).__name__)
    return respuesta_error(500, "Error de base de datos", "ERROR_BASE_DATOS")


@app.get("/", tags=["Sistema"])
def read_root():
    return {"message": "ok", "proyecto": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}


@app.get("/salud", tags=["Sistema"])
def salud():
    return {"estado": "ok"}
