/**
 * Estado del inmueble como etapa del proceso de revisión (RF-38 a RF-47).
 * Sin semáforo: todas las etapas usan el mismo azul; el estado nunca describe la seguridad del inmueble.
 * Diseño: círculos numerados como en los mockups de Figma.
 */
import { ESTADOS, fechaHora } from '@/lib/formato';

export function EstadoChip({ estado }) {
  if (!estado) return null;
  const info = ESTADOS[estado.codigo];
  return (
    <span className="estado-chip" title={info?.nombre}>
      <b>{estado.codigo}</b>
      {info?.corto ?? estado.nombre}
    </span>
  );
}

function Pasos({ codigo, conTexto = true }) {
  return (
    <div className="etapas" role="img" aria-label={`Etapa ${codigo} de 5: ${ESTADOS[codigo]?.nombre}`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <div key={n} className={`etapa ${n === codigo ? 'actual' : n < codigo ? 'hecha' : ''}`}>
          <div className="etapa-circulo">{n}</div>
          {conTexto && <span>{ESTADOS[n].corto}</span>}
        </div>
      ))}
    </div>
  );
}

/** Versión compacta para tarjetas: «Etapa del proceso · Etapa 2 de 5». */
export function CajaEtapas({ estado }) {
  if (!estado) return null;
  return (
    <div className="caja-etapas">
      <div className="fila-entre">
        <span className="sobretitulo">Etapa del proceso</span>
        <span className="estado-chip" style={{ padding: '2px 10px' }}>Etapa {estado.codigo} de 5</span>
      </div>
      <Pasos codigo={estado.codigo} conTexto={false} />
      <div className="fila-entre">
        <strong style={{ fontSize: '0.82rem', color: 'var(--azul-700)' }}>
          {estado.codigo}. {ESTADOS[estado.codigo]?.corto}
        </strong>
        <span className="sobretitulo" style={{ fontSize: '0.66rem' }}>Actual</span>
      </div>
    </div>
  );
}

export function EtapasEstado({ estado }) {
  if (!estado) return null;
  return (
    <div className="pila">
      <div className="fila-entre">
        <strong>
          Etapa {estado.codigo} de 5 · {ESTADOS[estado.codigo]?.nombre ?? estado.nombre}
        </strong>
        <span className="texto-mini">Desde {fechaHora(estado.desde)}</span>
      </div>
      <Pasos codigo={estado.codigo} />
      <p className="texto-mini">
        Las 5 etapas reflejan el avance del proceso de revisión. No son indicadores de la condición estructural del inmueble.
      </p>
    </div>
  );
}
