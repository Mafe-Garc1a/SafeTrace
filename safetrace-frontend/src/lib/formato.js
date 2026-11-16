/**
 * Formatos y catálogos de la interfaz.
 * Regla del equipo: nunca usar «seguro», «inseguro» ni «habitable» para describir un inmueble.
 */

const ZONA_HORARIA = 'America/Bogota';

export function fecha(valor) {
  if (!valor) return '—';
  return new Date(valor).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric', timeZone: ZONA_HORARIA });
}

export function fechaHora(valor) {
  if (!valor) return '—';
  return new Date(valor).toLocaleString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: ZONA_HORARIA,
  });
}

/** Valor para <input type="datetime-local"> con la hora local del navegador. */
export function aInputFecha(valor = new Date()) {
  const d = new Date(valor);
  const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export function deInputFecha(texto) {
  return texto ? new Date(texto).toISOString() : null;
}

export function numero(valor, decimales = 1) {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return '—';
  return Number(valor).toLocaleString('es-CO', { maximumFractionDigits: decimales, minimumFractionDigits: 0 });
}

export function bytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

/** Etiqueta legible de un catálogo; si no está, convierte CODIGO_EN_MAYUS a «Codigo en mayus». */
export function etiqueta(catalogo, codigo) {
  if (codigo === null || codigo === undefined) return '—';
  if (catalogo && catalogo[codigo]) return catalogo[codigo];
  const texto = String(codigo).replaceAll('_', ' ').toLowerCase();
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

// Estados del inmueble: etapa del proceso de revisión, nunca la seguridad (sin semáforo)
export const ESTADOS = {
  1: { nombre: 'Sin evento pendiente', corto: 'Sin evento' },
  2: { nombre: 'Marcado por evento sísmico', corto: 'Marcado por sismo' },
  3: { nombre: 'Revisión del propietario registrada', corto: 'Revisión registrada' },
  4: { nombre: 'Inspección profesional solicitada', corto: 'Inspección solicitada' },
  5: { nombre: 'Inspección profesional firmada', corto: 'Inspección firmada' },
};

export const TIPOS_INMUEBLE = { CASA: 'Casa', APARTAMENTO: 'Apartamento', LOCAL: 'Local', OFICINA: 'Oficina' };

export const SISTEMAS_CONSTRUCTIVOS = {
  MAMPOSTERIA_CONFINADA: 'Mampostería confinada',
  MAMPOSTERIA_NO_REFORZADA: 'Mampostería no reforzada',
  MAMPOSTERIA_REFORZADA: 'Mampostería reforzada',
  PORTICOS_CONCRETO: 'Pórticos de concreto',
  MUROS_CONCRETO: 'Muros de concreto',
  ESTRUCTURA_METALICA: 'Estructura metálica',
  BAHAREQUE: 'Bahareque',
  TAPIA_ADOBE: 'Tapia o adobe',
  MADERA: 'Madera',
  OTRO: 'Otro',
};

export const TIPOS_EVENTO = {
  MANTENIMIENTO: 'Mantenimiento',
  DANO: 'Daño',
  REPARACION: 'Reparación',
  INTERVENCION: 'Intervención',
  EVENTO_EXTERNO: 'Evento externo (sismo)',
};

export const CATEGORIAS_DOCUMENTO = {
  FACTURA: 'Factura',
  ORDEN_TRABAJO: 'Orden de trabajo',
  CONTRATO: 'Contrato',
  INFORME_TECNICO: 'Informe técnico',
};

export const TIPOS_INSPECCION = { POST_SISMO: 'Posterior a sismo', PREVENTIVA: 'Preventiva', SEGUIMIENTO: 'Seguimiento' };

export const ESTADOS_SOLICITUD = {
  SOLICITADA: 'Solicitada',
  ASIGNADA: 'Perito asignado',
  FIRMADA: 'Firmada',
  CANCELADA: 'Cancelada',
};

export const ESTADOS_CREDENCIAL = {
  REGISTRADO: 'Registrado',
  PENDIENTE_VALIDACION: 'Pendiente de validación',
  VALIDADO: 'Validado',
  RECHAZADO: 'Rechazado',
  VENCIDO: 'Matrícula vencida',
  INCONSISTENTE: 'Inconsistente',
};

export const TIPOS_DOCUMENTO_PERITO = { MATRICULA: 'Matrícula profesional', TITULO: 'Título', CEDULA: 'Cédula', OTRO: 'Otro' };

export const DOCUMENTOS_IDENTIDAD = { CC: 'Cédula de ciudadanía', CE: 'Cédula de extranjería', PA: 'Pasaporte', PPT: 'PPT' };

export const CAMPOS_COMPARTIDOS = {
  LINEA_CRONOLOGICA: 'Línea cronológica',
  FOTOS: 'Fotos',
  INSPECCIONES_FIRMADAS: 'Inspecciones firmadas',
};

export const ROLES = {
  PROPIETARIO: 'Propietario',
  PERITO: 'Perito',
  ADMINISTRADOR_GENERAL: 'Administrador general',
  SUPERADMIN: 'Superadministrador',
};

export const CAUSAS_ESTADO = {
  'RF-39': 'Sismo relevante en el radio',
  'RF-40': 'El propietario registró una revisión',
  'RF-41': 'Se solicitó una inspección',
  'RF-42': 'El perito firmó la inspección',
  'RF-43': 'Revisión sin cambios y sin inspección',
  'RF-44': 'Venció la constancia',
  'RF-45': 'Nuevo sismo relevante',
};

export const VARIABLES_INDICE = {
  antiguedad: 'Antigüedad',
  sistema_constructivo: 'Sistema constructivo',
  resonancia: 'Resonancia',
  magnitud: 'Magnitud del sismo',
  cercania: 'Cercanía al hipocentro',
  distancia: 'Distancia',
  profundidad: 'Profundidad',
  danos_previos: 'Daños previos',
  crecimiento_grietas: 'Crecimiento de grietas',
  tiempo_sin_revision: 'Tiempo sin revisión',
  anio_construccion: 'Año de construcción',
  numero_pisos: 'Número de pisos',
  distancia_km: 'Distancia epicentral (km)',
  profundidad_km: 'Profundidad (km)',
  distancia_hipocentral_km: 'Distancia hipocentral (km)',
  periodo_s: 'Periodo natural (s)',
  relacion_periodos: 'Relación de periodos',
  factor_resonancia: 'Factor de resonancia',
  fecha_ultima_revision: 'Última revisión',
};

export function nombreZona(zonas, id) {
  if (!id) return 'Sin zona';
  return zonas?.find((z) => z.id === id)?.nombre ?? etiqueta(null, id);
}
