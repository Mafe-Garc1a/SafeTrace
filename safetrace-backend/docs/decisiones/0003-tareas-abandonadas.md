# Las tareas abandonadas cuentan como fallo

**Fecha:** 2026-11-05

**Decisión:** Una tarea con más de `MINUTOS_TAREA_ATASCADA` en `PROCESANDO` vuelve a `PENDIENTE` o queda `FALLIDA` según `max_intentos`. La evaluación proponía devolverla siempre a `PENDIENTE`.

**Motivo:** Evita repetir sin fin una tarea que tumba al trabajador.
