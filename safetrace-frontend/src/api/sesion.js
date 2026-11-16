/**
 * Sesión guardada en sessionStorage: se borra al cerrar la pestaña.
 * Forma: { token, usuario, minutos }  (minutos = minutos de inactividad permitidos, RNF-11)
 */
const CLAVE = 'safetrace.sesion';

export function leerSesion() {
  try {
    const texto = sessionStorage.getItem(CLAVE);
    return texto ? JSON.parse(texto) : null;
  } catch {
    return null;
  }
}

export function guardarSesion(sesion) {
  try {
    sessionStorage.setItem(CLAVE, JSON.stringify(sesion));
  } catch {
    /* almacenamiento bloqueado: la sesión vive solo en memoria */
  }
}

export function borrarSesion() {
  try {
    sessionStorage.removeItem(CLAVE);
  } catch {
    /* nada que borrar */
  }
}
