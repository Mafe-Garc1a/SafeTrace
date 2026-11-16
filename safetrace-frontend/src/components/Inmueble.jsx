/** Piezas visuales del inmueble tomadas de los mockups: ilustración tipo plano y tarjeta con etapas. */
import { Link } from 'react-router-dom';
import { Building, Building2, Home, Store } from 'lucide-react';
import { CajaEtapas } from '@/components/Estado';
import { SISTEMAS_CONSTRUCTIVOS, TIPOS_INMUEBLE, etiqueta, fecha } from '@/lib/formato';

/** Fachada dibujada como plano (el backend no guarda una foto principal del inmueble). */
export function Plano({ claro = false }) {
  const trazo = claro ? '#1e5aa8' : '#9fc2ec';
  const acento = '#f2b33d';
  return (
    <svg viewBox="0 0 400 260" preserveAspectRatio="xMidYMid slice" aria-hidden>
      <defs>
        <pattern id={`cuadricula-${claro}`} width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M20 0H0V20" fill="none" stroke={trazo} strokeOpacity="0.14" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="400" height="260" fill={`url(#cuadricula-${claro})`} />
      <g fill="none" stroke={trazo} strokeWidth="1.6" strokeLinejoin="round">
        <path d="M120 230V95l80-45 80 45v135" />
        <path d="M100 230h220" />
        <path d="M110 100l90-52 90 52" strokeOpacity="0.6" />
        {[0, 1, 2].map((f) => [0, 1, 2].map((c) => <rect key={`${f}-${c}`} x={140 + c * 44} y={112 + f * 34} width="28" height="22" rx="2" />))}
        <rect x="186" y="200" width="28" height="30" rx="2" />
        <path d="M60 230V160h40v70M300 230V140h50v90" strokeOpacity="0.5" />
        <path d="M40 245h320" strokeDasharray="4 4" strokeOpacity="0.5" />
      </g>
      <g fill={acento}>
        <circle cx="282" cy="96" r="4" />
        <circle cx="128" cy="180" r="4" />
      </g>
      <g stroke={acento} strokeWidth="1.2" fill="none">
        <path d="M282 96h40v-30" />
        <path d="M128 180H70v30" />
      </g>
    </svg>
  );
}

const ICONO_TIPO = { CASA: Home, APARTAMENTO: Building, LOCAL: Store, OFICINA: Building2 };

export function codigoInmueble(i) {
  return `INM-${i.id.slice(-6).toUpperCase()}`;
}

export function TarjetaInmueble({ inmueble: i, acciones }) {
  const Icono = ICONO_TIPO[i.tipo_inmueble] ?? Building2;
  return (
    <article className="tarjeta-inmueble">
      <Link to={`/inmuebles/${i.id}`} className="tarjeta-inmueble-imagen" aria-label={`Abrir ${i.direccion}`}>
        <span className="tipo">{etiqueta(TIPOS_INMUEBLE, i.tipo_inmueble)}</span>
        <Icono size={44} strokeWidth={1.3} />
        <span className="codigo">ID: {codigoInmueble(i)}</span>
      </Link>
      <div className="tarjeta-inmueble-cuerpo">
        <div>
          <h3>
            <Link to={`/inmuebles/${i.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>{i.direccion}</Link>
          </h3>
          <span className="texto-mini">{i.ciudad}</span>
        </div>
        <div className="fila-entre texto-mini" style={{ borderTop: '1px solid var(--azul-200)', borderBottom: '1px solid var(--azul-200)', padding: '6px 0' }}>
          <span>Año {i.anio_construccion} · {etiqueta(SISTEMAS_CONSTRUCTIVOS, i.sistema_constructivo)}</span>
          <span>{i.numero_pisos} piso(s)</span>
        </div>
        <CajaEtapas estado={i.estado} />
        {i.estado.codigo === 2 && <div className="aviso-sismo-tarjeta">Marcado por un sismo relevante · Revisión sugerida</div>}
      </div>
      <div className="tarjeta-inmueble-pie">
        {acciones ?? (
          <>
            <span>Último cambio: {fecha(i.estado.desde)}</span>
            <Link to={`/inmuebles/${i.id}?p=resumen`}>Ver historial</Link>
          </>
        )}
      </div>
    </article>
  );
}
