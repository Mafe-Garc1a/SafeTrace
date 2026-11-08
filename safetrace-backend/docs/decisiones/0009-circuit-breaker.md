# Circuit breaker por proveedor y por proceso

**Fecha:** 2026-11-06

**Decisión:** Tras `FALLOS_MAXIMOS_PROVEEDOR` fallos seguidos, el proveedor no se llama durante `SEGUNDOS_CIRCUITO_ABIERTO`. Las tareas se posponen sin gastar intentos. `NotImplementedError` no cuenta como fallo. El estado vive en cada proceso.

**Motivo:** Si gastaran intentos, una caída del proveedor dejaría las tareas `FALLIDA` aunque el problema no fuera suyo. Un proveedor sin integrar no es una caída: la tarea debe fallar normalmente.
