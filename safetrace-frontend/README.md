# SafeTrace · Frontend

Aplicación web (React 18 + Vite + React Router) para propietarios, peritos y administradores.

## Arrancar

```bash
npm install
copy .env.example .env      # VITE_API_URL=http://localhost:8000
npm run dev                 # http://localhost:5173
```

El backend debe estar encendido (`python -m uvicorn main:app --reload` desde `safetrace-backend`).

## Modo demostración

Sin backend ni base de datos: en la pantalla de ingreso, botones «o explore sin backend».
Acceso directo para presentaciones:

```
http://localhost:5173/ingresar?demo=PROPIETARIO
http://localhost:5173/ingresar?demo=PERITO&ir=/perito/solicitudes
http://localhost:5173/ingresar?demo=ADMINISTRADOR_GENERAL&ir=/admin/priorizacion
http://localhost:5173/ingresar?demo=SUPERADMIN&ir=/admin/permisos
```

Los datos viven en memoria (`src/api/demo.js`) y vuelven al estado inicial al recargar.

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/api/` | Cliente HTTP (token, errores del backend), sesión y modo demostración |
| `src/context/` | Sesión, permisos del rol y cierre por inactividad (RNF-11) |
| `src/components/` | UI básica, layout con menú por permisos, estado por etapas, archivos, QR, gráficas |
| `src/pages/` | Acceso, páginas públicas, inicio, inmuebles (ficha con pestañas), perito y administración |
| `src/lib/` | Formatos y catálogos, subida directa de archivos con SHA-256, hooks de carga |

El menú se arma con `GET /auth/yo/permisos`, no con el nombre del rol.

## Reglas de interfaz que cumple

- Azul, blanco y gris claro; rojo/naranja solo para alertas o daños; verde solo para «completado» o «constancia verificada».
- El estado del inmueble se muestra como etapa 1–5 del proceso, sin semáforo, y nunca usa «seguro», «inseguro» ni «habitable».
- Cada dato indica su origen: registro del usuario, «Análisis automático mediante IA» o evaluación firmada de un perito.
- El índice siempre va con sus variables y el aviso «orientativo, no es una evaluación profesional».
- El enlace público y la verificación por QR no muestran el estado ni datos personales.

## Pendiente de servicios externos

- **Fotos y documentos:** requieren el proveedor S3/R2/MinIO configurado en el backend; sin él, la API responde 501 y la interfaz lo explica.
