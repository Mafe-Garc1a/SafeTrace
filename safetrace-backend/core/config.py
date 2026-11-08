"""Configuración leída de variables de entorno (archivo .env en local)."""

import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# librería en Python que permite cargar variables de entorno desde el archivo .env
load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "SafeTrace"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = "Bitácora de inmuebles, sismos e inspecciones"

    # Entorno de ejecución (local | pruebas | produccion)
    ENTORNO: str = os.getenv("ENTORNO", "local")

    # Configuración de la base de datos (MongoDB Atlas o MongoDB instalado en el equipo)
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "safetrace")

    # Conexiones máximas por proceso; total = (procesos web + trabajadores) × este valor
    mongo_max_pool_size: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "20"))
    
    # Tiempos máximos en milisegundos: conectar, esperar una respuesta y esperar una conexión libre
    mongo_connect_timeout_ms: int = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
    mongo_socket_timeout_ms: int = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "15000"))
    mongo_wait_queue_timeout_ms: int = int(os.getenv("MONGO_WAIT_QUEUE_TIMEOUT_MS", "5000"))

    # Configuración JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    # Duración máxima del token; la sesión además se cierra tras MINUTOS_SESION sin actividad
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # Sesiones: se cierran solas tras 30 minutos sin actividad (RNF-11)
    minutos_sesion: int = int(os.getenv("MINUTOS_SESION", "30"))

    # La sesión solo se renueva en base de datos si pasó este tiempo desde la última renovación
    minutos_renovacion_sesion: int = int(os.getenv("MINUTOS_RENOVACION_SESION", "1"))

    # Una tarea con más de este tiempo en PROCESANDO se considera abandonada por un trabajador caído
    minutos_tarea_atascada: int = int(os.getenv("MINUTOS_TAREA_ATASCADA", "15"))

    # Tiempo máximo de una tarea; debe ser menor que MINUTOS_TAREA_ATASCADA
    segundos_maximos_tarea: int = int(os.getenv("SEGUNDOS_MAXIMOS_TAREA", "300"))

    # Fallos seguidos de un proveedor antes de dejar de llamarlo, y por cuánto tiempo
    fallos_maximos_proveedor: int = int(os.getenv("FALLOS_MAXIMOS_PROVEEDOR", "5"))
    segundos_circuito_abierto: int = int(os.getenv("SEGUNDOS_CIRCUITO_ABIERTO", "60"))

    # n8n entra a /interno/* con esta credencial (encabezado X-Credencial-Servicio)
    credencial_servicio_n8n: str = os.getenv("CREDENCIAL_SERVICIO_N8N", "cambiar")

    # Primer administrador general (lo crea `python -m db.semillas`)
    admin_correo: str = os.getenv("ADMIN_CORREO", "")
    admin_contrasena: str = os.getenv("ADMIN_CONTRASENA", "")

    # Superadministrador: tiene todos los permisos (lo crea `python -m db.semillas`)
    superadmin_correo: str = os.getenv("SUPERADMIN_CORREO", "")
    superadmin_contrasena: str = os.getenv("SUPERADMIN_CONTRASENA", "")

    # Servicios externos
    proveedor_archivos_url: str = os.getenv("PROVEEDOR_ARCHIVOS_URL", "")
    correo_api_key: str = os.getenv("CORREO_API_KEY", "")


settings = Settings()
if not settings.jwt_secret:
    raise RuntimeError("Falta JWT_SECRET en las variables de entorno")
