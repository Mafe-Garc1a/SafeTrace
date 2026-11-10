"""Dependencias compartidas por los routers: usuario actual y permisos (RNF-08, RNF-10).

Proporciona las dependencias estándar de FastAPI para resolver el usuario autenticado,
verificación de permisos RBAC por módulo y acción, autorización de llamadas internas n8n
y control de acceso sobre entidades inmobiliarias con arquitectura desacoplada y defensiva.
"""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import Database

from core.config import settings
from core.database import a_object_id, get_db
from core.security import hash_token, verify_token

MODULO_SUPERVISION = "supervision_inmuebles"
MODULO_INSPECCIONES = "inspecciones"
MODULOS_USADOS: set[str] = {MODULO_SUPERVISION, MODULO_INSPECCIONES}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/sesion", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Valida el token JWT, verifica la sesión activa en base de datos y extiende vigencia (RNF-11)."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario_id = verify_token(token)
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sesion = db["sesiones"].find_one({"token_hash": hash_token(token)})
    if sesion is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión cerrada o vencida",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db["usuarios"].find_one({"_id": a_object_id(sesion["usuario_id"])})
    if usuario is None:
        # Intento fallback si usuario_id se guardó como string
        usuario = db["usuarios"].find_one({"_id": sesion["usuario_id"]})
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if not usuario.get("activo", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo. No autorizado")
    return usuario


def requiere_permiso(modulo: str, accion: str):
    """Permite el acceso a la ruta únicamente si el rol del usuario posee la acción sobre el módulo (RNF-08)."""
    MODULOS_USADOS.add(modulo)

    def _verificar(
        usuario: dict[str, Any] = Depends(get_current_user),
        db: Database = Depends(get_db),
    ) -> dict[str, Any]:
        rol = usuario.get("rol")
        if rol == "SUPERADMIN":
            return usuario
        permiso = db["permisos"].find_one({"rol": rol, "modulo": modulo})
        if permiso and accion in permiso.get("acciones", []):
            return usuario
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sin permiso '{accion}' sobre módulo '{modulo}'",
        )

    return _verificar


def requiere_servicio_n8n(x_credencial_servicio: str = Header(...)) -> None:
    """Valida la credencial de servicio compartida para invocaciones internas de n8n."""
    cred_esperada = getattr(
        settings,
        "CREDENCIAL_SERVICIO_N8N",
        getattr(settings, "credencial_servicio_n8n", "credencial-de-prueba"),
    )
    if not secrets.compare_digest(x_credencial_servicio, cred_esperada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de servicio inválida",
        )


def puede_supervisar(db: Database, usuario: dict[str, Any]) -> bool:
    """Indica si el usuario cuenta con atribuciones de supervisión global de inmuebles (RNF-10)."""
    rol = usuario.get("rol")
    if rol in ("SUPERADMIN", "ADMINISTRADOR_GENERAL"):
        return True
    permiso = db["permisos"].find_one({"rol": rol, "modulo": MODULO_SUPERVISION})
    return bool(permiso and "seleccionar" in permiso.get("acciones", []))


def obtener_inmueble_autorizado(
    db: Database,
    inmueble_id: str,
    usuario: dict[str, Any],
    solo_propietario: bool = False,
) -> dict[str, Any]:
    """Obtiene y autoriza el acceso al inmueble consultado (RNF-10)."""
    inmueble_obj = a_object_id(inmueble_id)
    inmueble = db["inmuebles"].find_one({"_id": inmueble_obj})
    if inmueble is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inmueble no encontrado")

    prop_id = inmueble.get("propietario_id")
    if prop_id == usuario.get("_id") or str(prop_id) == str(usuario.get("_id")):
        return inmueble

    if not solo_propietario:
        if puede_supervisar(db, usuario):
            return inmueble
        # Si el usuario es perito con solicitud asignada
        solicitud = db["solicitudes_inspeccion"].find_one({
            "inmueble_id": inmueble["_id"],
            "perito_id": usuario["_id"],
            "estado": {"$in": ["ASIGNADA", "EN_CURSO"]},
        })
        if solicitud:
            return inmueble

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso sobre este inmueble")

