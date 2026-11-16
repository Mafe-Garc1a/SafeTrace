import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Carga datos de la API y expone {datos, cargando, error, recargar}.
 * `funcion` se vuelve a ejecutar cuando cambian las dependencias.
 */
export function useCarga(funcion, dependencias = []) {
  const [estado, setEstado] = useState({ datos: null, cargando: true, error: null });
  const vigente = useRef(0);

  const recargar = useCallback(async () => {
    const turno = ++vigente.current;
    setEstado((e) => ({ ...e, cargando: true, error: null }));
    try {
      const datos = await funcion();
      if (turno === vigente.current) setEstado({ datos, cargando: false, error: null });
    } catch (error) {
      if (turno === vigente.current) setEstado({ datos: null, cargando: false, error });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencias);

  useEffect(() => {
    recargar();
  }, [recargar]);

  return { ...estado, recargar, setDatos: (datos) => setEstado((e) => ({ ...e, datos })) };
}

/** Ejecuta una acción (guardar, firmar...) y expone {ejecutar, enviando, error}. */
export function useAccion(funcion) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);
  const ejecutar = useCallback(
    async (...args) => {
      setEnviando(true);
      setError(null);
      try {
        return await funcion(...args);
      } catch (e) {
        setError(e);
        throw e;
      } finally {
        setEnviando(false);
      }
    },
    [funcion],
  );
  return { ejecutar, enviando, error, setError };
}
