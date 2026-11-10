# El X-Request-ID recibido se valida

**Fecha:** 2026-11-06

**Decisión:** Se conserva el `X-Request-ID` recibido solo si tiene de 8 a 64 letras, números, `-` o `_`. Si no, se genera uno nuevo. Cada tarea guarda el ID de la petición que la creó.

**Motivo:** El ID llega a los logs: sin validarlo, un cliente podría inyectar texto en ellos. Guardarlo en la tarea permite seguir un caso de la API al trabajador.
