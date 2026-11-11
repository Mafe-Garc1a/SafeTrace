"""Proveedor de archivos compatible con S3: Cloudflare R2, AWS S3 o MinIO en local.

- El navegador sube el archivo directo con una URL firmada (PUT); la API nunca recibe el archivo.
- El navegador y el enlace público ven los archivos con una URL firmada de lectura (GET) que vence.
- El trabajador descarga las fotos para la IA.

La base de datos solo guarda la ruta y la huella SHA-256 de cada archivo.
Las URL se firman con AWS Signature V4 sin librerías extra; la descarga usa `httpx` con tiempo máximo.
Sin configuración, las funciones lanzan NotImplementedError (la API responde 501) y el resto sigue (RNF-24).
"""

import hashlib
import hmac
import re
from datetime import datetime, timedelta
from urllib.parse import quote, urlsplit

import httpx

from core.circuito import Circuito
from core.config import settings
from core.fechas import ahora

circuito = Circuito("archivos")

ALGORITMO = "AWS4-HMAC-SHA256"
_RUTA_VALIDA = re.compile(r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-]+)*\.[a-z0-9]{2,5}$")


def configurado() -> bool:
    return all(
        (
            settings.proveedor_archivos_url,
            settings.archivos_bucket,
            settings.archivos_access_key,
            settings.archivos_secret_key,
        )
    )


def _exigir_configuracion() -> None:
    if not configurado():
        raise NotImplementedError(
            "Proveedor de archivos sin configurar (PROVEEDOR_ARCHIVOS_URL, ARCHIVOS_BUCKET y claves)"
        )


# --- Rutas ------------------------------------------------------------------------


def prefijo_inmueble(inmueble_id) -> str:
    return f"inmuebles/{inmueble_id}/"


def prefijo_perito(perito_id) -> str:
    return f"peritos/{perito_id}/"


def ruta_valida(ruta: str, prefijo: str) -> bool:
    """La ruta la generó la API para ese dueño: evita registrar o leer archivos de otro inmueble o perito."""
    return ruta.startswith(prefijo) and bool(_RUTA_VALIDA.match(ruta))


# --- Firma AWS Signature V4 (URL prefirmada) ----------------------------------------


def _hmac(clave: bytes, texto: str) -> bytes:
    return hmac.new(clave, texto.encode(), hashlib.sha256).digest()


def _codificar(texto: str, seguro: str = "-_.~") -> str:
    return quote(texto, safe=seguro)


def url_prefirmada(
    metodo: str,
    url_base: str,
    camino: str,
    *,
    region: str,
    access_key: str,
    secret_key: str,
    segundos: int,
    momento: datetime,
    encabezados: dict[str, str] | None = None,
) -> str:
    """URL firmada con Signature V4 en la consulta. El cliente debe enviar los `encabezados` firmados tal cual."""
    base = urlsplit(url_base)
    host = base.netloc
    camino_canonico = _codificar(base.path.rstrip("/") + camino, "/-_.~")
    fecha = momento.strftime("%Y%m%d")
    marca = momento.strftime("%Y%m%dT%H%M%SZ")
    alcance = f"{fecha}/{region}/s3/aws4_request"

    firmados = {"host": host, **{k.lower(): str(v).strip() for k, v in (encabezados or {}).items()}}
    nombres = ";".join(sorted(firmados))
    parametros = {
        "X-Amz-Algorithm": ALGORITMO,
        "X-Amz-Credential": f"{access_key}/{alcance}",
        "X-Amz-Date": marca,
        "X-Amz-Expires": str(segundos),
        "X-Amz-SignedHeaders": nombres,
    }
    consulta = "&".join(f"{_codificar(k)}={_codificar(v)}" for k, v in sorted(parametros.items()))
    solicitud_canonica = "\n".join(
        [
            metodo,
            camino_canonico,
            consulta,
            "".join(f"{k}:{firmados[k]}\n" for k in sorted(firmados)),
            nombres,
            "UNSIGNED-PAYLOAD",
        ]
    )
    texto_a_firmar = "\n".join([ALGORITMO, marca, alcance, hashlib.sha256(solicitud_canonica.encode()).hexdigest()])
    clave = _hmac(_hmac(_hmac(_hmac(f"AWS4{secret_key}".encode(), fecha), region), "s3"), "aws4_request")
    firma = hmac.new(clave, texto_a_firmar.encode(), hashlib.sha256).hexdigest()
    return f"{base.scheme}://{host}{camino_canonico}?{consulta}&X-Amz-Signature={firma}"


def _url_objeto(metodo: str, ruta: str, segundos: int, momento: datetime, encabezados: dict | None = None) -> str:
    """URL con estilo de ruta (endpoint/bucket/ruta): funciona igual en R2, S3 y MinIO."""
    return url_prefirmada(
        metodo,
        settings.proveedor_archivos_url,
        f"/{settings.archivos_bucket}/{ruta}",
        region=settings.archivos_region,
        access_key=settings.archivos_access_key,
        secret_key=settings.archivos_secret_key,
        segundos=segundos,
        momento=momento,
        encabezados=encabezados,
    )


# --- Operaciones -------------------------------------------------------------------


def autorizacion_subida(ruta: str, tipo_contenido: str, tamano_bytes: int) -> dict:
    """URL para que el navegador suba el archivo con PUT.

    El tipo y el tamaño quedan firmados: el proveedor rechaza otro tipo de archivo o un tamaño distinto
    al declarado. El navegador pone `Content-Length` solo; debe enviar `Content-Type` igual al de `encabezados`.
    """
    _exigir_configuracion()
    momento = ahora()
    segundos = settings.archivos_segundos_subida
    url = _url_objeto(
        "PUT",
        ruta,
        segundos,
        momento,
        {"content-type": tipo_contenido, "content-length": str(tamano_bytes)},
    )
    return {
        "url_subida": url,
        "metodo": "PUT",
        "encabezados": {"Content-Type": tipo_contenido},
        "expira_en": momento + timedelta(seconds=segundos),
    }


def url_lectura(ruta: str) -> dict:
    """URL temporal para ver o descargar el archivo desde el navegador: {url, expira_en}."""
    _exigir_configuracion()
    momento = ahora()
    segundos = settings.archivos_segundos_lectura
    return {"url": _url_objeto("GET", ruta, segundos, momento), "expira_en": momento + timedelta(seconds=segundos)}


def descargar(ruta: str) -> bytes:
    """Descarga el archivo para el trabajador. Usar con `circuito.llamar` (RNF-24)."""
    _exigir_configuracion()
    url = _url_objeto("GET", ruta, 300, ahora())
    with httpx.Client(timeout=settings.archivos_segundos_timeout) as cliente:
        respuesta = cliente.get(url)
        respuesta.raise_for_status()
        return respuesta.content
