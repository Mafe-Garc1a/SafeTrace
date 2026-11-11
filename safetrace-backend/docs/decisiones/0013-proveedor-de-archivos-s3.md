# Proveedor de archivos compatible con S3

**Fecha:** 2026-11-09

**Decisión:** `core/almacenamiento.py` habla el API de S3, así que sirve con Cloudflare R2, AWS S3 o MinIO en local. Las URL se firman con AWS Signature V4 sin librerías extra, y la descarga del trabajador usa `httpx` con tiempo máximo. La subida es con `PUT` firmado; el tipo y el tamaño del archivo quedan firmados. Para ver un archivo se pide una URL temporal de lectura. Solo se registran rutas que la API generó para ese inmueble o perito.

**Motivo:** El navegador sube y descarga directo del proveedor, sin pasar los archivos por la API (RNF de rendimiento). R2 no acepta formularios `POST`, por eso se usa `PUT`. Sin boto3 la dependencia es menor y la firma se prueba con el ejemplo oficial de AWS. Validar la ruta impide registrar, y luego leer, el archivo de otro inmueble.

## Flujo para el frontend

1. `POST /archivos/autorizacion` con `{inmueble_id, nombre_archivo, tipo_contenido, tamano_bytes}` → `{ruta, url_subida, metodo, encabezados, expira_en}`.
2. `fetch(url_subida, {method: "PUT", headers: encabezados, body: archivo})` antes de `expira_en`. El tamaño enviado debe ser exactamente `tamano_bytes`.
3. Huella en el navegador: `crypto.subtle.digest("SHA-256", await archivo.arrayBuffer())` en hexadecimal.
4. `POST /inmuebles/{id}/evidencias` (o la revisión o inspección) con `archivo: {ruta, hash_sha256}`.
5. Para mostrarla: `GET /evidencias/{id}/archivo` → `{url, expira_en}`; pedir otra al vencer.

Documentos del perito: `POST /peritos/archivos/autorizacion?nombre_archivo=...&tamano_bytes=...` (solo PDF), luego `POST /peritos/documentos`; se ven con `GET /peritos/documentos/{documento_id}/archivo` y el administrador con `GET /admin/peritos/{id}/documentos/{documento_id}/archivo`. El enlace público entrega `url` en cada foto, nunca la ruta.

## Probar en local con MinIO

```powershell
docker run -d --name safetrace-minio -p 9000:9000 -p 9001:9001 `
  -e MINIO_ROOT_USER=minio -e MINIO_ROOT_PASSWORD=minio-secreto minio/minio server /data --console-address :9001
```

Crear el bucket `safetrace` en http://localhost:9001 y poner en `.env`: `PROVEEDOR_ARCHIVOS_URL=http://localhost:9000`, `ARCHIVOS_BUCKET=safetrace`, `ARCHIVOS_ACCESS_KEY=minio`, `ARCHIVOS_SECRET_KEY=minio-secreto`, `ARCHIVOS_REGION=us-east-1`.

En R2 o S3, el bucket debe permitir CORS con `PUT` y `GET` desde el dominio del frontend y el encabezado `Content-Type`.
