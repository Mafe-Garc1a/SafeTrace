# Formato único de error

**Fecha:** 2026-11-05

**Decisión:** Todos los errores responden `detail`, `codigo` y `request_id`. El 422 agrega `errores` y nunca devuelve `input`.

**Motivo:** `errores` indica qué campo falló. Sin `input`, la respuesta no repite lo que envió el usuario, incluidas las contraseñas.
