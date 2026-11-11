# Modelos matemáticos del índice de priorización

**Fecha:** 2026-11-10

**Decisión:** El índice se calcula como `I = 100·Σ wᵢ·xᵢ` con las ocho variables de RF-67 llevadas a una escala de 0 a 1, según el documento «SafeTrace: modelos matemáticos del índice de priorización». Dos variables salen de ecuaciones diferenciales: x₃ (resonancia) de la EDO no homogénea de 2.º orden, con T ≈ 0,1·N, y x₅ (cercanía al foco) de la ecuación de onda, con R = √(d² + h²). Las ecuaciones están en `core/modelos_indice.py`, son funciones puras y no usan librerías externas. Pesos, ζ, Tₛ, valores por sistema constructivo y `formula_version` se guardan en `configuracion` (`_id: parametros_indice`). Cada índice guarda los pesos, los parámetros y los aportes con que se calculó. `GET /inmuebles/{id}/indice/modelos` entrega los puntos de las gráficas, que se calculan al pedirlos y no se guardan.

**Motivo:**

- Las funciones están en `core/` y no en `app/crud/` porque no acceden a datos (separación de capas, criterio 6 de la auditoría).
- Sin numpy no hay dependencias nuevas que auditar (criterio 5).
- Guardar pesos y parámetros en cada índice permite explicar un índice antiguo aunque la configuración cambie después.
- Cada xᵢ se limita entre 0 y 1 y los pesos se dividen por su suma. Así el índice queda entre 0 y 100 y R = 0 no divide por cero.
- Si el cálculo falla, `marcar_inmuebles` registra el error y sigue con el inmueble siguiente: el marcado y el aviso no dependen del índice (RNF-24).
- El índice nunca cambia el estado (RNF-37) y lleva siempre el aviso de RF-68.

**Fuera de alcance por ahora:**

- Tendencia de la fisura: `tasa_crecimiento` existe, pero no tiene endpoint porque el modelo de IA todavía no mide el ancho en milímetros.
- Ajuste de pesos: debe hacerse con mínimos cuadrados con pesos no negativos (p. ej. `scipy.optimize.nnls`) y luego normalizarlos a suma 1. `numpy.linalg.lstsq` puede dar pesos negativos. Conviene calificar al menos 20 a 30 inmuebles. Falta un endpoint de administración que cambie los parámetros, suba `formula_version` y deje auditoría, como `PUT /admin/configuracion`.
- Los valores por sistema constructivo, salvo mampostería no reforzada (1) y pórticos de concreto (0,4), son propuestas; Tₛ = 0,6 s debe confirmarse con la microzonificación de Pereira.
