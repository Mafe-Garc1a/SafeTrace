/**
 * Sesión del usuario: inicio y cierre, permisos del rol y cierre por inactividad (RF-02, RF-03, RNF-11).
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { api, EVENTO_SESION_VENCIDA, get } from '@/api/cliente';
import { activarDemo, desactivarDemo, modoDemo } from '@/api/demo';
import { borrarSesion, guardarSesion, leerSesion } from '@/api/sesion';

const SesionContext = createContext(null);

export function SesionProvider({ children }) {
  const [sesion, setSesion] = useState(() => leerSesion());
  const [aviso, setAviso] = useState('');
  const temporizador = useRef(null);

  const actualizar = useCallback((nueva) => {
    if (nueva) guardarSesion(nueva);
    else borrarSesion();
    setSesion(nueva);
  }, []);

  const cargarPermisos = useCallback(async (base) => {
    const permisos = await get('/auth/yo/permisos');
    const completa = { ...base, permisos };
    actualizar(completa);
    return completa;
  }, [actualizar]);

  const iniciar = useCallback(async (correo, contrasena) => {
    desactivarDemo();
    const r = await api('/auth/sesion', { metodo: 'POST', formulario: { username: correo, password: contrasena }, sinToken: true });
    const base = { token: r.access_token, usuario: r.usuario, minutos: r.minutos_inactividad, permisos: [] };
    guardarSesion(base);
    setAviso('');
    return cargarPermisos(base);
  }, [cargarPermisos]);

  const iniciarDemo = useCallback(async (rol) => {
    activarDemo(rol);
    const r = await api('/auth/sesion', { metodo: 'POST', formulario: { username: rol, password: 'demo' } });
    const base = { token: r.access_token, usuario: r.usuario, minutos: r.minutos_inactividad, permisos: [], demo: true };
    guardarSesion(base);
    setAviso('');
    return cargarPermisos(base);
  }, [cargarPermisos]);

  const cerrar = useCallback(async (motivo = '') => {
    try {
      if (leerSesion()?.token && !modoDemo()) await api('/auth/sesion', { metodo: 'DELETE' });
    } catch {
      /* la sesión ya estaba cerrada en el servidor */
    }
    desactivarDemo();
    actualizar(null);
    setAviso(motivo);
  }, [actualizar]);

  // El backend respondió 401: la sesión venció o se cerró en otro lugar
  useEffect(() => {
    const alVencer = () => {
      desactivarDemo();
      actualizar(null);
      setAviso('Su sesión se cerró. Inicie sesión de nuevo.');
    };
    window.addEventListener(EVENTO_SESION_VENCIDA, alVencer);
    return () => window.removeEventListener(EVENTO_SESION_VENCIDA, alVencer);
  }, [actualizar]);

  // Cierre por inactividad (RNF-11)
  useEffect(() => {
    if (!sesion?.token) return undefined;
    const minutos = sesion.minutos || 30;
    const reiniciar = () => {
      clearTimeout(temporizador.current);
      temporizador.current = setTimeout(() => cerrar('Su sesión se cerró por inactividad.'), minutos * 60000);
    };
    const eventos = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll'];
    eventos.forEach((e) => window.addEventListener(e, reiniciar, { passive: true }));
    reiniciar();
    return () => {
      clearTimeout(temporizador.current);
      eventos.forEach((e) => window.removeEventListener(e, reiniciar));
    };
  }, [sesion?.token, sesion?.minutos, cerrar]);

  // Si la sesión guardada no trae permisos (versión anterior), se piden de nuevo
  useEffect(() => {
    if (sesion?.token && !sesion.permisos) cargarPermisos(sesion).catch(() => {});
  }, [sesion, cargarPermisos]);

  const puede = useCallback(
    (modulo, accion = 'seleccionar') => Boolean(sesion?.permisos?.some((p) => p.modulo === modulo && p[accion])),
    [sesion?.permisos],
  );

  const valor = useMemo(
    () => ({
      sesion,
      usuario: sesion?.usuario ?? null,
      rol: sesion?.usuario?.rol ?? null,
      autenticado: Boolean(sesion?.token),
      demo: Boolean(sesion?.demo),
      aviso,
      setAviso,
      puede,
      iniciar,
      iniciarDemo,
      cerrar,
    }),
    [sesion, aviso, puede, iniciar, iniciarDemo, cerrar],
  );

  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>;
}

export function useSesion() {
  const contexto = useContext(SesionContext);
  if (!contexto) throw new Error('useSesion debe usarse dentro de <SesionProvider>');
  return contexto;
}
