# Una tarea colgada cierra el trabajador

**Fecha:** 2026-11-06

**Decisión:** Una tarea que supera `SEGUNDOS_MAXIMOS_TAREA` se registra como fallo y el proceso termina. El trabajador necesita quien lo reinicie.

**Motivo:** Un hilo de Python no se puede detener. Si el proceso siguiera, la tarea podría terminar mientras otro trabajador la reintenta y, por ejemplo, enviar un correo dos veces.
