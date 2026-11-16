/**
 * Componentes básicos de la interfaz. Colores: azul, blanco y gris claro.
 * Rojo/naranja solo para alertas o daños; verde solo para «operación completada» o «constancia verificada».
 */
import { useEffect, useId, useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Info, Loader2, X } from 'lucide-react';
import { mensajeError } from '@/api/cliente';

export function Boton({ variante = 'primario', tamano, cargando, icono: Icono, children, className = '', ...props }) {
  return (
    <button
      type="button"
      className={`boton boton-${variante} ${tamano === 'pequeno' ? 'boton-pequeno' : ''} ${className}`}
      disabled={cargando || props.disabled}
      {...props}
    >
      {cargando ? <Loader2 size={16} className="girar" aria-hidden /> : Icono && <Icono size={16} aria-hidden />}
      {children}
    </button>
  );
}

export function Tarjeta({ titulo, accion, children, className = '', icono: Icono, sinRelleno }) {
  return (
    <section className={`tarjeta ${className}`}>
      {(titulo || accion) && (
        <header className="tarjeta-cabecera">
          <h2>
            {Icono && <Icono size={18} aria-hidden />}
            {titulo}
          </h2>
          {accion}
        </header>
      )}
      <div className={sinRelleno ? '' : 'tarjeta-cuerpo'}>{children}</div>
    </section>
  );
}

export function Encabezado({ titulo, descripcion, acciones, volver }) {
  return (
    <div className="encabezado">
      <div>
        {volver}
        <h1>{titulo}</h1>
        {descripcion && <p className="texto-suave">{descripcion}</p>}
      </div>
      {acciones && <div className="encabezado-acciones">{acciones}</div>}
    </div>
  );
}

export function Campo({ etiqueta, ayuda, error, children, requerido }) {
  const id = useId();
  const hijo = typeof children === 'function' ? children(id) : children;
  return (
    <div className={`campo ${error ? 'campo-error' : ''}`}>
      <label htmlFor={id}>
        {etiqueta}
        {requerido && <span className="requerido"> *</span>}
      </label>
      {hijo}
      {ayuda && !error && <small className="texto-suave">{ayuda}</small>}
      {error && <small className="texto-error">{error}</small>}
    </div>
  );
}

export function Entrada({ etiqueta, ayuda, requerido, ...props }) {
  return (
    <Campo etiqueta={etiqueta} ayuda={ayuda} requerido={requerido}>
      {(id) => <input id={id} required={requerido} {...props} />}
    </Campo>
  );
}

export function AreaTexto({ etiqueta, ayuda, requerido, ...props }) {
  return (
    <Campo etiqueta={etiqueta} ayuda={ayuda} requerido={requerido}>
      {(id) => <textarea id={id} rows={4} required={requerido} {...props} />}
    </Campo>
  );
}

export function Selector({ etiqueta, ayuda, opciones, vacio, requerido, ...props }) {
  const lista = Array.isArray(opciones) ? opciones : Object.entries(opciones).map(([valor, texto]) => ({ valor, texto }));
  return (
    <Campo etiqueta={etiqueta} ayuda={ayuda} requerido={requerido}>
      {(id) => (
        <select id={id} required={requerido} {...props}>
          {vacio !== undefined && <option value="">{vacio}</option>}
          {lista.map((o) => (
            <option key={o.valor} value={o.valor}>
              {o.texto}
            </option>
          ))}
        </select>
      )}
    </Campo>
  );
}

export function Casilla({ etiqueta, ...props }) {
  return (
    <label className="casilla">
      <input type="checkbox" {...props} />
      <span>{etiqueta}</span>
    </label>
  );
}

/** Insignia neutra (azul/gris). `tono` exito/alerta solo para lo que dicen las reglas del equipo. */
export function Insignia({ tono = 'neutro', children, icono: Icono }) {
  return (
    <span className={`insignia insignia-${tono}`}>
      {Icono && <Icono size={13} aria-hidden />}
      {children}
    </span>
  );
}

export function Aviso({ tono = 'info', titulo, children, onCerrar }) {
  const Icono = tono === 'exito' ? CheckCircle2 : tono === 'info' ? Info : AlertTriangle;
  return (
    <div className={`aviso aviso-${tono}`} role={tono === 'error' ? 'alert' : 'status'}>
      <Icono size={18} aria-hidden />
      <div>
        {titulo && <strong>{titulo}</strong>}
        {children && <div>{children}</div>}
      </div>
      {onCerrar && (
        <button type="button" className="aviso-cerrar" onClick={onCerrar} aria-label="Cerrar aviso">
          <X size={16} />
        </button>
      )}
    </div>
  );
}

export function ErrorCaja({ error, onReintentar }) {
  if (!error) return null;
  return (
    <Aviso tono="error" titulo="No se pudo completar">
      {mensajeError(error)}
      {error.requestId && <div className="texto-mini">Código de seguimiento: {error.requestId}</div>}
      {onReintentar && (
        <Boton variante="enlace" tamano="pequeno" onClick={onReintentar}>
          Reintentar
        </Boton>
      )}
    </Aviso>
  );
}

export function Cargando({ texto = 'Cargando…' }) {
  return (
    <div className="cargando" role="status">
      <Loader2 size={20} className="girar" aria-hidden />
      {texto}
    </div>
  );
}

export function Vacio({ icono: Icono = Info, titulo, children, accion }) {
  return (
    <div className="vacio">
      <Icono size={28} aria-hidden />
      <strong>{titulo}</strong>
      {children && <p>{children}</p>}
      {accion}
    </div>
  );
}

/** Muestra carga, error o el contenido. */
export function Contenido({ carga, children, vacio }) {
  if (carga.cargando && !carga.datos) return <Cargando />;
  if (carga.error) return <ErrorCaja error={carga.error} onReintentar={carga.recargar} />;
  if (vacio && vacio(carga.datos)) return vacio(carga.datos);
  return children(carga.datos);
}

export function Paginacion({ pagina, totalPaginas, onCambiar }) {
  if (!totalPaginas || totalPaginas <= 1) return null;
  return (
    <nav className="paginacion" aria-label="Paginación">
      <Boton variante="secundario" tamano="pequeno" icono={ChevronLeft} disabled={pagina <= 1} onClick={() => onCambiar(pagina - 1)}>
        Anterior
      </Boton>
      <span>
        Página {pagina} de {totalPaginas}
      </span>
      <Boton variante="secundario" tamano="pequeno" disabled={pagina >= totalPaginas} onClick={() => onCambiar(pagina + 1)}>
        Siguiente
        <ChevronRight size={16} aria-hidden />
      </Boton>
    </nav>
  );
}

export function Modal({ abierto, titulo, onCerrar, children, ancho = 560 }) {
  useEffect(() => {
    if (!abierto) return undefined;
    const alPresionar = (e) => e.key === 'Escape' && onCerrar();
    window.addEventListener('keydown', alPresionar);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', alPresionar);
      document.body.style.overflow = '';
    };
  }, [abierto, onCerrar]);
  if (!abierto) return null;
  return (
    <div className="modal-fondo" onMouseDown={(e) => e.target === e.currentTarget && onCerrar()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={titulo} style={{ maxWidth: ancho }}>
        <header className="modal-cabecera">
          <h2>{titulo}</h2>
          <button type="button" className="icono-boton" onClick={onCerrar} aria-label="Cerrar">
            <X size={18} />
          </button>
        </header>
        <div className="modal-cuerpo">{children}</div>
      </div>
    </div>
  );
}

/** Lista de pares etiqueta/valor. */
export function Datos({ items, columnas = 2 }) {
  return (
    <dl className="datos" style={{ '--columnas': columnas }}>
      {items.filter(Boolean).map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v ?? '—'}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Origen de un dato (regla 7): registro del usuario, IA o perito. */
export function Origen({ tipo }) {
  const textos = {
    USUARIO: 'Registro del usuario',
    SISTEMA: 'Registro automático del sistema',
    IA: 'Análisis automático mediante IA',
    PERITO: 'Evaluación firmada de un perito',
    REVISION: 'Revisión del propietario',
    EVENTO: 'Registro del usuario',
    INSPECCION: 'Evaluación de un perito',
  };
  return <span className={`origen origen-${String(tipo).toLowerCase()}`}>{textos[tipo] ?? tipo}</span>;
}

export function Pestanas({ pestanas, activa, onCambiar }) {
  return (
    <div className="pestanas" role="tablist">
      {pestanas.map(({ id, texto, icono: Icono }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={activa === id}
          className={activa === id ? 'activa' : ''}
          onClick={() => onCambiar(id)}
        >
          {Icono && <Icono size={16} aria-hidden />}
          {texto}
        </button>
      ))}
    </div>
  );
}

/** Mensaje temporal tras una operación completada. */
export function useMensaje() {
  const [mensaje, setMensaje] = useState('');
  useEffect(() => {
    if (!mensaje) return undefined;
    const t = setTimeout(() => setMensaje(''), 5000);
    return () => clearTimeout(t);
  }, [mensaje]);
  const vista = mensaje ? (
    <Aviso tono="exito" titulo={mensaje} onCerrar={() => setMensaje('')} />
  ) : null;
  return [vista, setMensaje];
}
