# Los errores no previstos se responden en el middleware

**Fecha:** 2026-11-06

**Decisión:** `MiddlewareCorrelacion` captura las excepciones no previstas y se registra antes que `CORSMiddleware`, para quedar dentro de él. No se usa `@app.exception_handler(Exception)`.

**Motivo:** Ese manejador corre fuera de los middlewares, y sus respuestas 500 salían sin encabezados de CORS.
