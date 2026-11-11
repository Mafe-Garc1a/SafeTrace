"""Proveedor de archivos compatible con S3: firma, rutas, subida, lectura y descarga (RF-14, RF-24 a RF-26)."""

from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from core import almacenamiento
from core.config import settings
from tests.conftest import iniciar_sesion, registrar

HASH = "a" * 64


@pytest.fixture
def proveedor(monkeypatch):
    """Proveedor configurado como MinIO local; no hace llamadas de red salvo `descargar`."""
    for nombre, valor in {
        "proveedor_archivos_url": "http://localhost:9000",
        "archivos_bucket": "safetrace",
        "archivos_access_key": "minio",
        "archivos_secret_key": "minio-secreto",
        "archivos_region": "us-east-1",
    }.items():
        monkeypatch.setattr(settings, nombre, valor)


def _foto(ruta: str) -> dict:
    return {"tipo_archivo": "FOTO", "zona_id": "MURO_SALA", "archivo": {"ruta": ruta, "hash_sha256": HASH}}


def _evento(cliente, inmueble_id: str, cabecera: dict) -> str:
    evento = {"tipo": "DANO", "fecha_evento": "2026-08-10T18:00:00Z", "descripcion": "Fisura en el muro"}
    return cliente.post(f"/inmuebles/{inmueble_id}/eventos", json=evento, headers=cabecera).json()["id"]


def _autorizar(cliente, inmueble_id: str, cabecera: dict, **cambios):
    solicitud = {
        "inmueble_id": inmueble_id,
        "nombre_archivo": "muro.JPG",
        "tipo_contenido": "image/jpeg",
        "tamano_bytes": 2_000_000,
        **cambios,
    }
    return cliente.post("/archivos/autorizacion", json=solicitud, headers=cabecera)


# --- Firma y rutas -------------------------------------------------------------------


def test_firma_coincide_con_el_ejemplo_oficial_de_aws():
    # Ejemplo "Authenticating Requests: Using Query Parameters" de la documentación de Amazon S3
    url = almacenamiento.url_prefirmada(
        "GET",
        "https://examplebucket.s3.amazonaws.com",
        "/test.txt",
        region="us-east-1",
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        segundos=86400,
        momento=datetime(2013, 5, 24, tzinfo=UTC),
    )
    firma = parse_qs(urlsplit(url).query)["X-Amz-Signature"][0]
    assert firma == "aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404"


@pytest.mark.parametrize(
    ("ruta", "valida"),
    [
        ("inmuebles/abc/2026/08/10180000000000.jpg", True),
        ("inmuebles/otro/2026/08/1.jpg", False),
        ("inmuebles/abc/../otro/1.jpg", False),
        ("inmuebles/abc//1.jpg", False),
        ("inmuebles/abc/1", False),
    ],
)
def test_ruta_valida_solo_dentro_del_prefijo(ruta, valida):
    assert almacenamiento.ruta_valida(ruta, "inmuebles/abc/") is valida


# --- Subida ----------------------------------------------------------------------------


def test_sin_proveedor_la_autorizacion_responde_501(cliente, propietario, inmueble):
    r = _autorizar(cliente, inmueble["id"], propietario)
    assert r.status_code == 501 and r.json()["codigo"] == "NO_IMPLEMENTADO"


def test_archivo_demasiado_grande_se_rechaza(cliente, propietario, inmueble, proveedor):
    r = _autorizar(cliente, inmueble["id"], propietario, tamano_bytes=50 * 1024 * 1024)
    assert r.status_code == 400


def test_autorizacion_firma_tipo_y_tamano(cliente, propietario, inmueble, proveedor):
    r = _autorizar(cliente, inmueble["id"], propietario)
    assert r.status_code == 200, r.text
    datos = r.json()
    # La extensión sale del tipo de contenido, no del nombre enviado
    assert datos["ruta"].startswith(f"inmuebles/{inmueble['id']}/") and datos["ruta"].endswith(".jpg")
    assert datos["metodo"] == "PUT" and datos["encabezados"] == {"Content-Type": "image/jpeg"}
    url = urlsplit(datos["url_subida"])
    assert url.netloc == "localhost:9000" and url.path == f"/safetrace/{datos['ruta']}"
    assert parse_qs(url.query)["X-Amz-SignedHeaders"] == ["content-length;content-type;host"]


def test_otro_propietario_no_puede_pedir_autorizacion(cliente, inmueble, proveedor):
    registrar(cliente, "otro@correo.com")
    r = _autorizar(cliente, inmueble["id"], iniciar_sesion(cliente, "otro@correo.com"))
    assert r.status_code == 403


# --- Registro y lectura de evidencias ---------------------------------------------------


def test_evidencia_con_ruta_de_otro_inmueble_se_rechaza(cliente, propietario, inmueble):
    evento_id = _evento(cliente, inmueble["id"], propietario)
    foto = _foto("inmuebles/507f1f77bcf86cd799439011/2026/08/1.jpg")
    r = cliente.post(
        f"/inmuebles/{inmueble['id']}/evidencias", json={**foto, "evento_id": evento_id}, headers=propietario
    )
    assert r.status_code == 400 and r.json()["codigo"] == "RUTA_ARCHIVO_INVALIDA"


def test_revision_con_ruta_ajena_no_guarda_nada(cliente, db, propietario, inmueble):
    revision = {
        "observaciones": "Revisión semestral",
        "hubo_cambios": False,
        "solicitara_inspeccion": False,
        "fotos": [_foto("inmuebles/507f1f77bcf86cd799439011/2026/08/1.jpg")],
    }
    r = cliente.post(f"/inmuebles/{inmueble['id']}/revisiones", json=revision, headers=propietario)
    assert r.status_code == 400 and db["revisiones"].count_documents({}) == 0


def test_url_de_lectura_de_una_evidencia(cliente, propietario, inmueble, proveedor):
    ruta = _autorizar(cliente, inmueble["id"], propietario).json()["ruta"]
    evento_id = _evento(cliente, inmueble["id"], propietario)
    evidencia = cliente.post(
        f"/inmuebles/{inmueble['id']}/evidencias", json={**_foto(ruta), "evento_id": evento_id}, headers=propietario
    ).json()

    r = cliente.get(f"/evidencias/{evidencia['id']}/archivo", headers=propietario)
    assert r.status_code == 200, r.text
    url = urlsplit(r.json()["url"])
    assert url.path == f"/safetrace/{ruta}" and parse_qs(url.query)["X-Amz-SignedHeaders"] == ["host"]
    assert r.json()["expira_en"]

    registrar(cliente, "otro@correo.com")
    ajeno = cliente.get(f"/evidencias/{evidencia['id']}/archivo", headers=iniciar_sesion(cliente, "otro@correo.com"))
    assert ajeno.status_code == 403
    assert cliente.get("/evidencias/507f1f77bcf86cd799439011/archivo", headers=propietario).status_code == 404


def test_lectura_sin_proveedor_responde_501(cliente, propietario, inmueble):
    evento_id = _evento(cliente, inmueble["id"], propietario)
    foto = _foto(f"inmuebles/{inmueble['id']}/2026/08/1.jpg")
    evidencia = cliente.post(
        f"/inmuebles/{inmueble['id']}/evidencias", json={**foto, "evento_id": evento_id}, headers=propietario
    ).json()
    assert cliente.get(f"/evidencias/{evidencia['id']}/archivo", headers=propietario).status_code == 501


# --- Documentos del perito ---------------------------------------------------------------


def _perito_con_documento(cliente) -> tuple[dict, str]:
    registrar(cliente, "perito@correo.com", rol="PERITO")
    cabecera = iniciar_sesion(cliente, "perito@correo.com")
    perfil = {
        "documento": {"tipo": "CC", "numero": "1098765432"},
        "profesion": "Ingeniero civil",
        "matricula_profesional": "MP-102938475",
    }
    perito_id = cliente.post("/peritos/perfil", json=perfil, headers=cabecera).json()["id"]
    return cabecera, perito_id


def test_documentos_del_perito(cliente, admin, proveedor):
    cabecera, perito_id = _perito_con_documento(cliente)

    r = cliente.post(
        "/peritos/archivos/autorizacion?nombre_archivo=matricula.pdf&tamano_bytes=300000", headers=cabecera
    )
    assert r.status_code == 200, r.text
    ruta = r.json()["ruta"]
    assert ruta.startswith(f"peritos/{perito_id}/") and ruta.endswith(".pdf")

    ajena = {"documentos": [{"tipo": "MATRICULA", "archivo": {"ruta": "peritos/otro/1.pdf", "hash_sha256": HASH}}]}
    assert cliente.post("/peritos/documentos", json=ajena, headers=cabecera).status_code == 400

    propia = {"documentos": [{"tipo": "MATRICULA", "archivo": {"ruta": ruta, "hash_sha256": HASH}}]}
    assert cliente.post("/peritos/documentos", json=propia, headers=cabecera).status_code == 200

    mio = cliente.get("/peritos/documentos/DOC-1/archivo", headers=cabecera)
    assert mio.status_code == 200 and urlsplit(mio.json()["url"]).path == f"/safetrace/{ruta}"
    revision = cliente.get(f"/admin/peritos/{perito_id}/documentos/DOC-1/archivo", headers=admin)
    assert revision.status_code == 200
    assert cliente.get("/peritos/documentos/DOC-9/archivo", headers=cabecera).status_code == 404
    # Un propietario no revisa documentos de peritos
    registrar(cliente, "ana@correo.com")
    ana = iniciar_sesion(cliente, "ana@correo.com")
    assert cliente.get(f"/admin/peritos/{perito_id}/documentos/DOC-1/archivo", headers=ana).status_code == 403


# --- Enlace público ----------------------------------------------------------------------


def test_enlace_publico_entrega_url_y_no_la_ruta(cliente, propietario, inmueble, proveedor):
    ruta = f"inmuebles/{inmueble['id']}/2026/08/1.jpg"
    evento_id = _evento(cliente, inmueble["id"], propietario)
    cliente.post(
        f"/inmuebles/{inmueble['id']}/evidencias", json={**_foto(ruta), "evento_id": evento_id}, headers=propietario
    )
    enlace = cliente.post(
        f"/inmuebles/{inmueble['id']}/enlaces", json={"campos_compartidos": ["FOTOS"]}, headers=propietario
    ).json()
    foto = cliente.get(f"/publico/{enlace['codigo']}").json()["fotos"][0]
    assert "ruta" not in foto and urlsplit(foto["url"]).path == f"/safetrace/{ruta}"


def test_enlace_publico_sin_proveedor_sigue_funcionando(cliente, propietario, inmueble):
    evento_id = _evento(cliente, inmueble["id"], propietario)
    foto = _foto(f"inmuebles/{inmueble['id']}/2026/08/1.jpg")
    cliente.post(f"/inmuebles/{inmueble['id']}/evidencias", json={**foto, "evento_id": evento_id}, headers=propietario)
    enlace = cliente.post(
        f"/inmuebles/{inmueble['id']}/enlaces", json={"campos_compartidos": ["FOTOS"]}, headers=propietario
    ).json()
    r = cliente.get(f"/publico/{enlace['codigo']}")
    assert r.status_code == 200 and r.json()["fotos"][0]["url"] is None


# --- Descarga del trabajador ---------------------------------------------------------------


def test_descargar_usa_url_firmada_y_tiempo_maximo(monkeypatch, proveedor):
    pedidas = []

    def responder(peticion: httpx.Request) -> httpx.Response:
        pedidas.append(peticion)
        return httpx.Response(200, content=b"imagen")

    cliente_real = httpx.Client
    monkeypatch.setattr(
        almacenamiento.httpx,
        "Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(responder), timeout=timeout),
    )
    assert almacenamiento.descargar("inmuebles/abc/1.jpg") == b"imagen"
    assert pedidas[0].url.path == "/safetrace/inmuebles/abc/1.jpg"
    assert "X-Amz-Signature" in str(pedidas[0].url)


def test_descargar_falla_si_el_proveedor_responde_error(monkeypatch, proveedor):
    cliente_real = httpx.Client
    monkeypatch.setattr(
        almacenamiento.httpx,
        "Client",
        lambda timeout: cliente_real(transport=httpx.MockTransport(lambda _: httpx.Response(403)), timeout=timeout),
    )
    with pytest.raises(httpx.HTTPStatusError):
        almacenamiento.descargar("inmuebles/abc/1.jpg")
