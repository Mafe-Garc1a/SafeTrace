# JWT_SECRET obligatorio en todos los entornos

**Fecha:** 2026-11-05

**Decisión:** La aplicación no arranca si falta `JWT_SECRET`, en ningún entorno. La evaluación proponía exigirlo solo fuera de local.

**Motivo:** `ENTORNO` vale `local` por defecto: un servidor sin esa variable arrancaría sin secreto.
