# Cola de tareas en MongoDB

**Fecha:** Registrada el 2026-11-06; la decisión es anterior a la auditoría

**Decisión:** Los trabajos lentos, como los correos y la comparación de fotos, se guardan en la colección `tareas` y los ejecuta un proceso aparte (`trabajador/main.py`).

**Motivo:** El usuario debe recibir respuesta en menos de 3 segundos. Usar MongoDB evita operar un servicio más para la cola.
