# Errores de negocio con atributos de clase

**Fecha:** 2026-11-05

**Decisión:** Cada excepción hereda de `ErrorNegocio` y define `status`, `codigo` y `mensaje` como atributos de clase. La evaluación proponía recibirlos en el constructor.

**Motivo:** Los `raise` existentes no cambian.
