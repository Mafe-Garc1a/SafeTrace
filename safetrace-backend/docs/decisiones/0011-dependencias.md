# PyJWT y versiones fijas con pip-tools

**Fecha:** 2026-11-06

**Decisión:** `python-jose` se reemplazó por PyJWT. Las dependencias directas están en los archivos `.in`, y `pip-compile` genera los `.txt` con versiones exactas.

**Motivo:** Lo pidió la evaluación (criterio 5). Con versiones exactas, todos instalan lo mismo y `pip-audit` revisa lo que realmente se usa.
