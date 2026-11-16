/**
 * Cliente HTTP del backend de SafeTrace.
 *
 * - Agrega el token de la sesión en cada petición.
 * - Convierte el formato único de error del backend ({detail, codigo, request_id, errores}) en ErrorApi.
 * - En modo demostración responde con datos de ejemplo, sin tocar el backend.
 */
import { leerSesion } from './sesion';
import { responderDemo, modoDemo } from './demo';
import { ErrorApi } from './errores';

export { ErrorApi };

export const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

/** Mensaje para mostrar al usuario, con los campos inválidos si los hay. */
export function mensajeError(error) {
  if (!error) return '';
  if (error instanceof ErrorApi) {
    if (error.errores.length) {
      return `${error.message}: ${error.errores.map((e) => `${e.campo || 'dato'} — ${e.mensaje}`).join('; ')}`;
    }
    if (error.estado === 501) return `${error.message}. Esta función necesita un servicio externo que aún no está configurado.`;
    return error.message;
  }
  if (error.name === 'TypeError') return 'No hay conexión con el servidor. Revise que el backend esté encendido.';
  return error.message ?? 'Error inesperado';
}

// El contexto de sesión escucha este evento para cerrar la sesión cuando el backend responde 401
export const EVENTO_SESION_VENCIDA = 'safetrace:sesion-vencida';

export async function api(ruta, { metodo = 'GET', cuerpo, consulta, formulario, sinToken = false } = {}) {
  let url = ruta;
  if (consulta) {
    const params = new URLSearchParams();
    Object.entries(consulta).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') params.append(k, v);
    });
    const texto = params.toString();
    if (texto) url += `?${texto}`;
  }

  if (modoDemo()) return responderDemo(metodo, url, cuerpo ?? formulario);

  const encabezados = {};
  let body;
  if (formulario) {
    encabezados['Content-Type'] = 'application/x-www-form-urlencoded';
    body = new URLSearchParams(formulario).toString();
  } else if (cuerpo !== undefined) {
    encabezados['Content-Type'] = 'application/json';
    body = JSON.stringify(cuerpo);
  }
  const sesion = leerSesion();
  if (!sinToken && sesion?.token) encabezados.Authorization = `Bearer ${sesion.token}`;

  const respuesta = await fetch(`${API_URL}${url}`, { method: metodo, headers: encabezados, body });
  if (respuesta.status === 204) return null;

  let datos = null;
  const texto = await respuesta.text();
  try {
    datos = texto ? JSON.parse(texto) : null;
  } catch {
    datos = { detail: texto };
  }

  if (!respuesta.ok) {
    if (respuesta.status === 401 && !sinToken && sesion?.token) {
      window.dispatchEvent(new CustomEvent(EVENTO_SESION_VENCIDA));
    }
    throw new ErrorApi({ estado: respuesta.status, ...(datos ?? {}) });
  }
  return datos;
}

export const get = (ruta, consulta) => api(ruta, { consulta });
export const post = (ruta, cuerpo) => api(ruta, { metodo: 'POST', cuerpo });
export const put = (ruta, cuerpo) => api(ruta, { metodo: 'PUT', cuerpo });
export const patch = (ruta, cuerpo) => api(ruta, { metodo: 'PATCH', cuerpo });
export const del = (ruta) => api(ruta, { metodo: 'DELETE' });
