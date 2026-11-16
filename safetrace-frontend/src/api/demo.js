/**
 * Modo demostración: responde como el backend con datos de ejemplo en memoria.
 * Sirve para presentar la aplicación sin backend, sin base de datos y sin proveedor de archivos.
 * Nada se guarda: al recargar la página los datos vuelven al estado inicial.
 */
import { ErrorApi } from './errores';

const CLAVE = 'safetrace.demo';

export function modoDemo() {
  try {
    return Boolean(sessionStorage.getItem(CLAVE));
  } catch {
    return false;
  }
}

export function activarDemo(rol) {
  try {
    sessionStorage.setItem(CLAVE, rol);
  } catch {
    /* sin almacenamiento */
  }
}

export function desactivarDemo() {
  try {
    sessionStorage.removeItem(CLAVE);
  } catch {
    /* sin almacenamiento */
  }
}

function rolDemo() {
  try {
    return sessionStorage.getItem(CLAVE) || 'PROPIETARIO';
  } catch {
    return 'PROPIETARIO';
  }
}

// ---------------------------------------------------------------- utilidades
const ahora = () => new Date().toISOString();
const hace = (dias, horas = 0) => new Date(Date.now() - dias * 86400000 - horas * 3600000).toISOString();
const en = (dias) => new Date(Date.now() + dias * 86400000).toISOString();
let contador = 1000;
const nuevoId = () => (++contador).toString(16).padStart(24, 'a');
const hash = () => Array.from({ length: 64 }, () => '0123456789abcdef'[Math.floor(Math.random() * 16)]).join('');
const error = (estado, detail) => new ErrorApi({ estado, detail, codigo: 'DEMO', request_id: 'demo' });

function paginar(lista, consulta, tamanoPorDefecto = 20) {
  const pagina = Number(consulta.get('pagina') ?? 1);
  const tamano = Number(consulta.get('tamano') ?? tamanoPorDefecto);
  return {
    pagina,
    tamano,
    total: lista.length,
    total_paginas: Math.ceil(lista.length / tamano),
    datos: lista.slice((pagina - 1) * tamano, pagina * tamano),
  };
}

// ---------------------------------------------------------------- permisos (iguales a db/semillas.py)
const MODULOS = {
  usuarios: 'Administración de usuarios (RF-04 a RF-06)',
  supresion: 'Solicitudes de supresión de datos (RF-08, RF-09)',
  auditoria: 'Consulta de auditoría (RF-10)',
  configuracion: 'Magnitud mínima y radio de afectación (RF-11, RF-12)',
  roles: 'Roles',
  modulos: 'Módulos',
  permisos: 'Permisos por rol y módulo',
  perfil_perito: 'Perfil y documentos del perito (RF-13, RF-14)',
  validacion_peritos: 'Validación de credenciales de peritos (RF-15, RF-16)',
  inmuebles: 'Registro y consulta de inmuebles (RF-17 a RF-21)',
  supervision_inmuebles: 'Ver todos los inmuebles y su información, solo lectura (RNF-10)',
  bitacora: 'Eventos y evidencias (RF-22 a RF-27)',
  archivos: 'Autorización de subida de archivos (RF-24, RF-25)',
  revisiones: 'Revisión del propietario (RF-28, RF-29)',
  solicitudes_inspeccion: 'Solicitar inspecciones (RF-48)',
  asignacion_peritos: 'Asignar peritos a solicitudes (RF-49)',
  inspecciones: 'Registrar, editar, firmar y corregir inspecciones (RF-50 a RF-53)',
  enlaces: 'Enlaces públicos del inmueble (RF-59 a RF-61)',
  analisis_ia: 'Reintentar análisis de IA (RF-64)',
  priorizacion: 'Priorización de inmuebles por sismo (RF-66)',
};

const PERMISOS_ROL = {
  ADMINISTRADOR_GENERAL: {
    usuarios: ['seleccionar', 'actualizar'],
    supresion: ['seleccionar', 'actualizar'],
    auditoria: ['seleccionar'],
    configuracion: ['seleccionar', 'actualizar'],
    validacion_peritos: ['seleccionar', 'actualizar'],
    inmuebles: ['seleccionar'],
    supervision_inmuebles: ['seleccionar'],
    asignacion_peritos: ['seleccionar', 'actualizar'],
    analisis_ia: ['actualizar'],
    priorizacion: ['seleccionar'],
  },
  PERITO: {
    perfil_perito: ['insertar', 'seleccionar'],
    archivos: ['insertar'],
    inspecciones: ['insertar', 'seleccionar', 'actualizar'],
  },
  PROPIETARIO: {
    inmuebles: ['insertar', 'seleccionar', 'actualizar'],
    bitacora: ['insertar', 'actualizar'],
    archivos: ['insertar'],
    revisiones: ['insertar'],
    solicitudes_inspeccion: ['insertar'],
    enlaces: ['insertar', 'seleccionar', 'borrar'],
    analisis_ia: ['actualizar'],
  },
};

function permisosDe(rol) {
  const acciones = ['insertar', 'actualizar', 'seleccionar', 'borrar'];
  return Object.keys(MODULOS)
    .map((modulo) => {
      const lista = rol === 'SUPERADMIN' ? acciones : PERMISOS_ROL[rol]?.[modulo];
      if (!lista) return null;
      return { id: `${modulo}-${rol}`, modulo, rol, ...Object.fromEntries(acciones.map((a) => [a, lista.includes(a)])) };
    })
    .filter(Boolean);
}

// ---------------------------------------------------------------- datos de ejemplo
function crearDatos() {
  const consentimiento = { aceptado: true, version_politica: 'v1.0', fecha: hace(120) };
  const usuarios = [
    { id: 'u-prop', nombre_completo: 'María Fernanda López', correo: 'maria.lopez@ejemplo.co', rol: 'PROPIETARIO', activo: true, consentimiento, creado_en: hace(120) },
    { id: 'u-perito', nombre_completo: 'Carlos Andrés Restrepo', correo: 'carlos.restrepo@ejemplo.co', rol: 'PERITO', activo: true, consentimiento, creado_en: hace(200) },
    { id: 'u-perito2', nombre_completo: 'Laura Gómez Arango', correo: 'laura.gomez@ejemplo.co', rol: 'PERITO', activo: true, consentimiento, creado_en: hace(6) },
    { id: 'u-admin', nombre_completo: 'Administrador General', correo: 'admin@safetrace.co', rol: 'ADMINISTRADOR_GENERAL', activo: true, consentimiento, creado_en: hace(300) },
    { id: 'u-super', nombre_completo: 'Superadministrador', correo: 'super@safetrace.co', rol: 'SUPERADMIN', activo: true, consentimiento, creado_en: hace(300) },
    { id: 'u-prop2', nombre_completo: 'Jorge Iván Cardona', correo: 'jorge.cardona@ejemplo.co', rol: 'PROPIETARIO', activo: true, consentimiento, creado_en: hace(40) },
    { id: 'u-prop3', nombre_completo: 'Ana Sofía Ramírez', correo: 'ana.ramirez@ejemplo.co', rol: 'PROPIETARIO', activo: false, consentimiento, creado_en: hace(90) },
  ];

  const zonas = [
    ['MURO_SALA', 'Muro de la sala', 'MUROS'],
    ['MURO_HABITACION', 'Muro de habitación', 'MUROS'],
    ['MURO_COCINA', 'Muro de la cocina', 'MUROS'],
    ['MURO_BANO', 'Muro del baño', 'MUROS'],
    ['COLUMNA', 'Columna', 'ESTRUCTURA'],
    ['VIGA', 'Viga', 'ESTRUCTURA'],
    ['PLACA_ENTREPISO', 'Placa de entrepiso', 'ESTRUCTURA'],
    ['ESCALERA', 'Escalera', 'ESTRUCTURA'],
    ['CUBIERTA', 'Cubierta o techo', 'EXTERIOR'],
    ['FACHADA', 'Fachada', 'EXTERIOR'],
    ['PISO', 'Piso', 'INTERIOR'],
  ].map(([id, nombre, grupo]) => ({ id, nombre, grupo }));

  const sismos = [
    { id: 's-1', fecha_hora: hace(2, 5), magnitud: 5.8, profundidad_km: 112, epicentro: { type: 'Point', coordinates: [-75.94, 4.62] }, fuentes: [{ fuente: 'SGC', id_externo: 'SGC2026wxyz', magnitud: 5.8 }, { fuente: 'USGS', id_externo: 'us7000abcd', magnitud: 5.7 }], es_relevante: true, inmuebles_marcados: 37, recibido_en: hace(2, 5) },
    { id: 's-2', fecha_hora: hace(9), magnitud: 4.1, profundidad_km: 145, epicentro: { type: 'Point', coordinates: [-73.1, 6.8] }, fuentes: [{ fuente: 'SGC', id_externo: 'SGC2026qrst', magnitud: 4.1 }], es_relevante: false, inmuebles_marcados: 0, recibido_en: hace(9) },
    { id: 's-3', fecha_hora: hace(48), magnitud: 6.1, profundidad_km: 89, epicentro: { type: 'Point', coordinates: [-76.3, 3.9] }, fuentes: [{ fuente: 'USGS', id_externo: 'us7000efgh', magnitud: 6.1 }], es_relevante: true, inmuebles_marcados: 21, recibido_en: hace(48) },
    { id: 's-4', fecha_hora: hace(15), magnitud: 3.6, profundidad_km: 20, epicentro: { type: 'Point', coordinates: [-75.5, 5.1] }, fuentes: [{ fuente: 'SGC', id_externo: 'SGC2026mnop', magnitud: 3.6 }], es_relevante: false, inmuebles_marcados: 0, recibido_en: hace(15) },
  ];

  const base = (id, extra) => ({
    id,
    propietario_id: 'u-prop',
    matricula_inmobiliaria: null,
    ultimo_indice: null,
    revision_semestral: { ultima: hace(150), proxima: en(30) },
    ultimos_eventos: [],
    creado_en: hace(100),
    actualizado_en: hace(2),
    fecha_registro: hace(100),
    ...extra,
  });

  const inmuebles = [
    base('i-1', {
      tipo_inmueble: 'CASA', direccion: 'Calle 14 # 23-45, barrio Álamos', ciudad: 'Pereira', matricula_inmobiliaria: '290-123456', anio_construccion: 1978,
      sistema_constructivo: 'MAMPOSTERIA_NO_REFORZADA', numero_pisos: 2, ubicacion: { type: 'Point', coordinates: [-75.6961, 4.8133] },
      estado: { codigo: 2, nombre: 'MARCADO_POR_EVENTO_SISMICO', desde: hace(2, 5), version: 4 },
      ultimo_indice: { valor: 68.4, sismo_id: 's-1', calculado_en: hace(2, 5) },
    }),
    base('i-2', {
      tipo_inmueble: 'APARTAMENTO', direccion: 'Carrera 7 # 19-28, apto 402', ciudad: 'Pereira', anio_construccion: 2004,
      sistema_constructivo: 'PORTICOS_CONCRETO', numero_pisos: 8, ubicacion: { type: 'Point', coordinates: [-75.6906, 4.8143] },
      estado: { codigo: 5, nombre: 'INSPECCION_FIRMADA', desde: hace(20), version: 6 },
      ultimo_indice: { valor: 41.2, sismo_id: 's-3', calculado_en: hace(48) },
      revision_semestral: { ultima: hace(25), proxima: en(155) },
    }),
    base('i-3', {
      tipo_inmueble: 'LOCAL', direccion: 'Avenida 30 de Agosto # 45-12', ciudad: 'Dosquebradas', anio_construccion: 2015,
      sistema_constructivo: 'MAMPOSTERIA_CONFINADA', numero_pisos: 1, ubicacion: { type: 'Point', coordinates: [-75.6725, 4.8353] },
      estado: { codigo: 1, nombre: 'SIN_EVENTO_PENDIENTE', desde: hace(60), version: 1 },
    }),
    base('i-4', {
      propietario_id: 'u-prop2', tipo_inmueble: 'CASA', direccion: 'Manzana 8 casa 14, Cuba', ciudad: 'Pereira', anio_construccion: 1985,
      sistema_constructivo: 'BAHAREQUE', numero_pisos: 2, ubicacion: { type: 'Point', coordinates: [-75.7353, 4.7927] },
      estado: { codigo: 4, nombre: 'INSPECCION_SOLICITADA', desde: hace(1), version: 3 },
      ultimo_indice: { valor: 74.9, sismo_id: 's-1', calculado_en: hace(2, 5) },
    }),
  ];

  const evidencia = (id, inmueble_id, origen, zona_id, dias, extra = {}) => ({
    id, inmueble_id, origen, tipo_archivo: 'FOTO', categoria_documento: null, zona_id,
    archivo: { ruta: `inmuebles/${inmueble_id}/2026/11/${id}.jpg`, hash_sha256: hash() }, estado: 'VIGENTE',
    reemplazada_por: null, invalidacion: null, cargado_por: 'u-prop', creado_en: hace(dias), ...extra,
  });

  const eventos = [
    { id: 'e-1', inmueble_id: 'i-1', tipo: 'EVENTO_EXTERNO', fecha_evento: hace(2, 5), descripcion: 'Sismo de magnitud 5.8 a 30 km del inmueble (SGC y USGS). El inmueble quedó dentro del radio de afectación.', zona_id: null, origen: 'SISTEMA', sismo_id: 's-1', registrado_por: null, creado_en: hace(2, 5) },
    { id: 'e-2', inmueble_id: 'i-1', tipo: 'DANO', fecha_evento: hace(40), descripcion: 'Fisura horizontal de unos 40 cm sobre la ventana del muro de la sala, ancho aproximado 0,5 mm.', zona_id: 'MURO_SALA', origen: 'USUARIO', sismo_id: null, registrado_por: 'u-prop', creado_en: hace(40) },
    { id: 'e-3', inmueble_id: 'i-1', tipo: 'REPARACION', fecha_evento: hace(35), descripcion: 'Resane y pintura de la fisura del muro de la sala con malla de refuerzo.', zona_id: 'MURO_SALA', origen: 'USUARIO', sismo_id: null, registrado_por: 'u-prop', creado_en: hace(35) },
    { id: 'e-4', inmueble_id: 'i-1', tipo: 'MANTENIMIENTO', fecha_evento: hace(95), descripcion: 'Cambio de tejas rotas y limpieza de canales en la cubierta.', zona_id: 'CUBIERTA', origen: 'USUARIO', sismo_id: null, registrado_por: 'u-prop', creado_en: hace(95) },
    { id: 'e-5', inmueble_id: 'i-2', tipo: 'MANTENIMIENTO', fecha_evento: hace(70), descripcion: 'Impermeabilización de la terraza y revisión de bajantes.', zona_id: 'CUBIERTA', origen: 'USUARIO', sismo_id: null, registrado_por: 'u-prop', creado_en: hace(70) },
    { id: 'e-6', inmueble_id: 'i-2', tipo: 'EVENTO_EXTERNO', fecha_evento: hace(48), descripcion: 'Sismo de magnitud 6.1 a 110 km del inmueble (USGS).', zona_id: null, origen: 'SISTEMA', sismo_id: 's-3', registrado_por: null, creado_en: hace(48) },
  ];

  const evidencias = [
    evidencia('v-1', 'i-1', { tipo: 'EVENTO', id: 'e-2' }, 'MURO_SALA', 40),
    evidencia('v-2', 'i-1', { tipo: 'EVENTO', id: 'e-2' }, 'MURO_SALA', 40, { estado: 'REEMPLAZADA', reemplazada_por: 'v-3', invalidacion: { usuario_id: 'u-prop', fecha: hace(39), motivo: 'Foto borrosa' } }),
    evidencia('v-3', 'i-1', { tipo: 'EVENTO', id: 'e-2' }, 'MURO_SALA', 39),
    evidencia('v-4', 'i-1', { tipo: 'EVENTO', id: 'e-3' }, 'MURO_SALA', 35, { tipo_archivo: 'DOCUMENTO', categoria_documento: 'FACTURA', archivo: { ruta: 'inmuebles/i-1/2026/10/v-4.pdf', hash_sha256: hash() } }),
    evidencia('v-5', 'i-1', { tipo: 'EVENTO', id: 'e-4' }, 'CUBIERTA', 95),
    evidencia('v-6', 'i-2', { tipo: 'EVENTO', id: 'e-5' }, 'CUBIERTA', 70),
  ];

  const revisiones = [
    { id: 'r-1', inmueble_id: 'i-1', fecha: hace(150), observaciones: 'Revisión semestral: sin fisuras nuevas. La fisura del muro de la sala sigue resanada.', hubo_cambios: false, solicitara_inspeccion: false, evidencias_ids: ['v-5'], cambio_estado_aplicado: false, registrada_por: 'u-prop', creado_en: hace(150) },
    { id: 'r-2', inmueble_id: 'i-2', fecha: hace(47), observaciones: 'Después del sismo revisé muros y columnas del apartamento. Pequeña fisura en el muro del baño.', hubo_cambios: true, solicitara_inspeccion: true, evidencias_ids: ['v-6'], cambio_estado_aplicado: true, registrada_por: 'u-prop', creado_en: hace(47) },
  ];

  const peritos = [
    {
      id: 'p-1', usuario_id: 'u-perito', documento: { tipo: 'CC', numero: '1088234567' }, profesion: 'Ingeniero civil', especialidad: 'Estructuras',
      matricula_profesional: '66202-123456 RSD', vigencia_matricula: null, estado_credencial: 'VALIDADO',
      documentos: [
        { documento_id: 'd-1', tipo: 'MATRICULA', archivo: { ruta: 'peritos/p-1/matricula.pdf', hash_sha256: hash() }, cargado_en: hace(190) },
        { documento_id: 'd-2', tipo: 'TITULO', archivo: { ruta: 'peritos/p-1/titulo.pdf', hash_sha256: hash() }, cargado_en: hace(190) },
      ],
      validaciones: [{ decision: 'APROBADO', motivo: null, validado_por: 'u-admin', fecha: hace(185), documentos_revisados: ['d-1', 'd-2'] }],
      creado_en: hace(195), actualizado_en: hace(185),
    },
    {
      id: 'p-2', usuario_id: 'u-perito2', documento: { tipo: 'CC', numero: '1093456789' }, profesion: 'Arquitecta', especialidad: null,
      matricula_profesional: 'A66-2019-0456', vigencia_matricula: en(400), estado_credencial: 'PENDIENTE_VALIDACION',
      documentos: [{ documento_id: 'd-3', tipo: 'MATRICULA', archivo: { ruta: 'peritos/p-2/matricula.pdf', hash_sha256: hash() }, cargado_en: hace(5) }],
      validaciones: [], creado_en: hace(6), actualizado_en: hace(5),
    },
  ];

  const solicitudes = [
    { id: 'sol-1', inmueble_id: 'i-2', solicitada_por: 'u-prop', motivo: 'Fisura en el muro del baño después del sismo del Valle', tipo_inspeccion: 'POST_SISMO', fecha_propuesta: hace(30), estado: 'FIRMADA', perito_id: 'p-1', asignada_por: 'u-admin', cambios_estado: [], creado_en: hace(46) },
    { id: 'sol-2', inmueble_id: 'i-4', solicitada_por: 'u-prop2', motivo: 'Grietas diagonales en muros de bahareque después del sismo', tipo_inspeccion: 'POST_SISMO', fecha_propuesta: en(3), estado: 'ASIGNADA', perito_id: 'p-1', asignada_por: 'u-admin', cambios_estado: [], creado_en: hace(1) },
    { id: 'sol-3', inmueble_id: 'i-4', solicitada_por: 'u-prop2', motivo: 'Revisión preventiva de la cubierta y la escalera', tipo_inspeccion: 'PREVENTIVA', fecha_propuesta: en(10), estado: 'SOLICITADA', perito_id: null, asignada_por: null, cambios_estado: [], creado_en: hace(0, 6) },
  ];

  const AVISO_LEGAL = 'Constancia de inspección visual realizada por el profesional indicado. SafeTrace no declara la condición estructural del inmueble ni certifica el cumplimiento de la NSR-10.';
  const inspecciones = [
    {
      id: 'insp-1', solicitud_id: 'sol-1', inmueble_id: 'i-2', perito_id: 'p-1', version: 1, version_anterior_id: null, es_version_activa: true,
      fecha_inspeccion: hace(21), motivo: 'Inspección posterior al sismo del 2026 en el Valle',
      observaciones: 'Visita de 2 horas. Se revisaron muros, columnas y placas del apartamento 402 y zonas comunes del piso 4.',
      hallazgos: 'Fisura capilar (< 0,3 mm) en el pañete del muro del baño, sin continuidad hacia elementos estructurales. Columnas y vigas sin fisuras visibles.',
      resultado: 'Daño no estructural en acabados. Se recomienda resanar y repetir la revisión en seis meses.',
      evidencias_ids: ['v-6'], firma: { firmada: true, fecha: hace(20), metodo: 'CONTRASENA', huella_sha256: hash() },
      constancia: { codigo: 'ST-2026-8F3K2Q', emitida_en: hace(20), vigencia_meses: 6, vigente_hasta: en(160), estado: 'VIGENTE' },
      aviso_legal: AVISO_LEGAL, creado_en: hace(21),
    },
  ];

  const variablesIndice = {
    anio_construccion: 1978, sistema_constructivo: 'MAMPOSTERIA_NO_REFORZADA', numero_pisos: 2, magnitud: 5.8, distancia_km: 30.4, profundidad_km: 112,
    fecha_ultima_revision: hace(150), periodo_s: 0.2, relacion_periodos: 0.4, factor_resonancia: 1.18, distancia_hipocentral_km: 116.05,
  };
  const indices = [
    {
      id: 'ix-1', inmueble_id: 'i-1', sismo_id: 's-1', valor: 68.4, variables: variablesIndice,
      variables_normalizadas: { antiguedad: 0.48, sistema_constructivo: 1, resonancia: 0.39, magnitud: 0.27, cercania: 0.43, danos_previos: 1, crecimiento_grietas: 0.2, tiempo_sin_revision: 0.83 },
      pesos: { antiguedad: 0.12, sistema_constructivo: 0.2, resonancia: 0.12, magnitud: 0.12, cercania: 0.14, danos_previos: 0.12, crecimiento_grietas: 0.08, tiempo_sin_revision: 0.1 },
      aportes: { antiguedad: 5.8, sistema_constructivo: 20, resonancia: 4.7, magnitud: 3.2, cercania: 6, danos_previos: 12, crecimiento_grietas: 1.6, tiempo_sin_revision: 8.3 },
      parametros: { zeta: 0.05, periodo_suelo_s: 0.5 }, aviso: 'Índice orientativo calculado por el sistema; no es una evaluación profesional.', formula_version: 'v2-modelos', calculado_en: hace(2, 5),
    },
    {
      id: 'ix-4', inmueble_id: 'i-4', sismo_id: 's-1', valor: 74.9, variables: { ...variablesIndice, anio_construccion: 1985, sistema_constructivo: 'BAHAREQUE', distancia_km: 22.1 },
      variables_normalizadas: null, pesos: null, aportes: null, parametros: { zeta: 0.05, periodo_suelo_s: 0.5 }, aviso: 'Índice orientativo calculado por el sistema; no es una evaluación profesional.', formula_version: 'v2-modelos', calculado_en: hace(2, 5),
    },
    {
      id: 'ix-2', inmueble_id: 'i-2', sismo_id: 's-3', valor: 41.2, variables: { ...variablesIndice, anio_construccion: 2004, sistema_constructivo: 'PORTICOS_CONCRETO', numero_pisos: 8, periodo_s: 0.8, relacion_periodos: 1.6, factor_resonancia: 0.64, distancia_km: 110, magnitud: 6.1, profundidad_km: 89, distancia_hipocentral_km: 141.5 },
      variables_normalizadas: null, pesos: null, aportes: null, parametros: { zeta: 0.05, periodo_suelo_s: 0.5 }, aviso: 'Índice orientativo calculado por el sistema; no es una evaluación profesional.', formula_version: 'v2-modelos', calculado_en: hace(48),
    },
  ];

  const analisis = [
    { id: 'a-1', inmueble_id: 'i-1', zona_id: 'MURO_SALA', evidencia_anterior_id: 'v-1', evidencia_nueva_id: 'v-3', estado: 'COMPLETADO', tarea_id: 't-1', resultado: { cambio_detectado: true, descripcion: 'La fisura se ve más larga que en la foto anterior de la misma zona.', confianza: 0.82 }, leyenda: 'Análisis automático mediante IA', modelo_version: 'cnn-fisuras-0.3', completado_en: hace(39), creado_en: hace(39) },
    { id: 'a-2', inmueble_id: 'i-1', zona_id: 'CUBIERTA', evidencia_anterior_id: 'v-5', evidencia_nueva_id: 'v-5', estado: 'FALLIDO', tarea_id: 't-2', resultado: null, leyenda: 'Análisis automático mediante IA', modelo_version: 'cnn-fisuras-0.3', completado_en: null, creado_en: hace(10) },
  ];

  const enlaces = [{ id: 'l-1', inmueble_id: 'i-2', codigo: 'k7PqX2mN9vRt', campos_compartidos: ['LINEA_CRONOLOGICA', 'INSPECCIONES_FIRMADAS'], activo: true, creado_por: 'u-prop', creado_en: hace(15), revocado_en: null }];

  const historial = [
    { id: 'h-1', inmueble_id: 'i-1', estado_anterior: 1, estado_nuevo: 2, fecha: hace(2, 5), causa: 'RF-39', referencia: { tipo: 'SISMO', id: 's-1' }, producido_por: { tipo: 'PROCESO', id: 'n8n' } },
    { id: 'h-2', inmueble_id: 'i-2', estado_anterior: 1, estado_nuevo: 2, fecha: hace(48), causa: 'RF-39', referencia: { tipo: 'SISMO', id: 's-3' }, producido_por: { tipo: 'PROCESO', id: 'n8n' } },
    { id: 'h-3', inmueble_id: 'i-2', estado_anterior: 2, estado_nuevo: 3, fecha: hace(47), causa: 'RF-40', referencia: { tipo: 'REVISION', id: 'r-2' }, producido_por: { tipo: 'USUARIO', id: 'u-prop' } },
    { id: 'h-4', inmueble_id: 'i-2', estado_anterior: 3, estado_nuevo: 4, fecha: hace(46), causa: 'RF-41', referencia: { tipo: 'SOLICITUD', id: 'sol-1' }, producido_por: { tipo: 'USUARIO', id: 'u-prop' } },
    { id: 'h-5', inmueble_id: 'i-2', estado_anterior: 4, estado_nuevo: 5, fecha: hace(20), causa: 'RF-42', referencia: { tipo: 'INSPECCION', id: 'insp-1' }, producido_por: { tipo: 'USUARIO', id: 'u-perito' } },
  ];

  const notificaciones = [
    { id: 'n-1', usuario_id: 'u-prop', tipo: 'SISMO_RELEVANTE', referencia: { tipo: 'SISMO', id: 's-1' }, estado: 'ENVIADA', creado_en: hace(2, 5), enviada_en: hace(2, 5) },
    { id: 'n-2', usuario_id: 'u-prop', tipo: 'INSPECCION_FIRMADA', referencia: { tipo: 'INSPECCION', id: 'insp-1' }, estado: 'ENVIADA', creado_en: hace(20), enviada_en: hace(20) },
    { id: 'n-3', usuario_id: 'u-prop', tipo: 'INSPECCION_ASIGNADA', referencia: { tipo: 'SOLICITUD', id: 'sol-1' }, estado: 'ENVIADA', creado_en: hace(45), enviada_en: hace(45) },
    { id: 'n-4', usuario_id: 'u-prop', tipo: 'SISMO_RELEVANTE', referencia: { tipo: 'SISMO', id: 's-3' }, estado: 'FALLIDA', creado_en: hace(48), enviada_en: null },
    { id: 'n-5', usuario_id: 'u-perito', tipo: 'NUEVA_ASIGNACION', referencia: { tipo: 'SOLICITUD', id: 'sol-2' }, estado: 'ENVIADA', creado_en: hace(1), enviada_en: hace(1) },
  ];

  const auditoria = [
    { id: 'au-1', coleccion: 'inspecciones', documento_id: 'insp-1', accion: 'FIRMAR', actor: { tipo: 'USUARIO', id: 'u-perito', rol: 'PERITO' }, cambios: { 'firma.firmada': true, 'constancia.codigo': 'ST-2026-8F3K2Q' }, fecha: hace(20) },
    { id: 'au-2', coleccion: 'solicitudes_inspeccion', documento_id: 'sol-2', accion: 'ASIGNAR', actor: { tipo: 'USUARIO', id: 'u-admin', rol: 'ADMINISTRADOR_GENERAL' }, cambios: { perito_id: 'p-1', estado: 'ASIGNADA' }, fecha: hace(1) },
    { id: 'au-3', coleccion: 'inmuebles', documento_id: 'i-1', accion: 'CAMBIAR_ESTADO', actor: { tipo: 'PROCESO', id: 'n8n' }, cambios: { 'estado.codigo': { antes: 1, despues: 2 } }, fecha: hace(2, 5) },
    { id: 'au-4', coleccion: 'configuracion', documento_id: 'parametros_sismo', accion: 'ACTUALIZAR', actor: { tipo: 'USUARIO', id: 'u-admin', rol: 'ADMINISTRADOR_GENERAL' }, cambios: { magnitud_minima: { antes: 5.5, despues: 5 } }, fecha: hace(60) },
    { id: 'au-5', coleccion: 'peritos', documento_id: 'p-1', accion: 'VALIDAR', actor: { tipo: 'USUARIO', id: 'u-admin', rol: 'ADMINISTRADOR_GENERAL' }, cambios: { estado_credencial: 'VALIDADO' }, fecha: hace(185) },
  ];

  const roles = [
    ['SUPERADMIN', 'Acceso total: gestiona roles, módulos, permisos y administradores'],
    ['ADMINISTRADOR_GENERAL', 'Administra usuarios, peritos, solicitudes y configuración; consulta todo'],
    ['PERITO', 'Registra, firma y corrige inspecciones asignadas'],
    ['PROPIETARIO', 'Registra sus inmuebles, bitácora, revisiones y enlaces públicos'],
  ].map(([id, descripcion]) => ({ id, nombre_rol: id, descripcion, estado: true }));

  const modulos = Object.entries(MODULOS).map(([id, descripcion]) => ({ id, nombre_modulo: id, descripcion, estado: true }));
  const permisos = ['SUPERADMIN', 'ADMINISTRADOR_GENERAL', 'PERITO', 'PROPIETARIO'].flatMap(permisosDe);

  const supresiones = [{ id: 'sup-1', usuario_id: 'u-prop3', fecha_solicitud: hace(3), estado: 'RECIBIDA', datos_eliminados: [], datos_conservados: [], atendida_por: null, fecha_atencion: null }];

  inmuebles.forEach((i) => {
    i.ultimos_eventos = eventos
      .filter((e) => e.inmueble_id === i.id)
      .sort((a, b) => b.fecha_evento.localeCompare(a.fecha_evento))
      .slice(0, 3)
      .map((e) => ({ evento_id: e.id, tipo: e.tipo, fecha: e.fecha_evento, resumen: e.descripcion.slice(0, 80) }));
  });

  return {
    usuarios, zonas, sismos, inmuebles, eventos, evidencias, revisiones, peritos, solicitudes, inspecciones, indices, analisis, enlaces,
    historial, notificaciones, auditoria, roles, modulos, permisos, supresiones,
    configuracion: { magnitud_minima: 5, radio_afectacion_km: 200, actualizado_por: 'u-admin', actualizado_en: hace(60) },
  };
}

let db = null;
const datos = () => (db ??= crearDatos());

const USUARIO_POR_ROL = { PROPIETARIO: 'u-prop', PERITO: 'u-perito', ADMINISTRADOR_GENERAL: 'u-admin', SUPERADMIN: 'u-super' };
const yo = () => datos().usuarios.find((u) => u.id === USUARIO_POR_ROL[rolDemo()]);
const esAdmin = () => ['ADMINISTRADOR_GENERAL', 'SUPERADMIN'].includes(rolDemo());

function inmueble(id) {
  const i = datos().inmuebles.find((x) => x.id === id);
  if (!i) throw error(404, 'Inmueble no encontrado');
  return i;
}

function cambiarEstado(i, nuevo, causa, referencia) {
  const NOMBRES = { 1: 'SIN_EVENTO_PENDIENTE', 2: 'MARCADO_POR_EVENTO_SISMICO', 3: 'REVISION_PROPIETARIO_REGISTRADA', 4: 'INSPECCION_SOLICITADA', 5: 'INSPECCION_FIRMADA' };
  datos().historial.unshift({ id: nuevoId(), inmueble_id: i.id, estado_anterior: i.estado.codigo, estado_nuevo: nuevo, fecha: ahora(), causa, referencia, producido_por: { tipo: 'USUARIO', id: yo().id } });
  i.estado = { codigo: nuevo, nombre: NOMBRES[nuevo], desde: ahora(), version: i.estado.version + 1 };
}

function resumirEventos(i) {
  i.ultimos_eventos = datos()
    .eventos.filter((e) => e.inmueble_id === i.id)
    .sort((a, b) => b.fecha_evento.localeCompare(a.fecha_evento))
    .slice(0, 3)
    .map((e) => ({ evento_id: e.id, tipo: e.tipo, fecha: e.fecha_evento, resumen: e.descripcion.slice(0, 80) }));
}

// ---------------------------------------------------------------- modelos del índice (como core/modelos_indice.py)
function curvas(indice) {
  const { periodo_s: T, relacion_periodos, factor_resonancia, distancia_km, profundidad_km, distancia_hipocentral_km, numero_pisos } = indice.variables;
  const { zeta, periodo_suelo_s } = indice.parametros;
  const wn = (2 * Math.PI) / T;
  const wd = wn * Math.sqrt(1 - zeta ** 2);
  const b = zeta / Math.sqrt(1 - zeta ** 2);
  const tMax = 10 * T;
  const vib = Array.from({ length: 101 }, (_, k) => {
    const t = (tMax * k) / 100;
    return { t: +t.toFixed(4), x: +(Math.exp(-zeta * wn * t) * (Math.cos(wd * t) + b * Math.sin(wd * t))).toFixed(4) };
  });
  const res = Array.from({ length: 121 }, (_, k) => {
    const r = (3 * k) / 120;
    return { r: +r.toFixed(4), factor: +(1 / Math.sqrt((1 - r ** 2) ** 2 + (2 * zeta * r) ** 2)).toFixed(4) };
  });
  const dMax = Math.max(2 * distancia_km, 100);
  const aten = Array.from({ length: 101 }, (_, k) => {
    const d = (dMax * k) / 100;
    const R = Math.hypot(d, profundidad_km);
    return { distancia_epicentral_km: +d.toFixed(2), distancia_hipocentral_km: +R.toFixed(2), amplitud_relativa: +Math.min(1, 50 / R).toFixed(4) };
  });
  return {
    inmueble_id: indice.inmueble_id, sismo_id: indice.sismo_id, formula_version: indice.formula_version, aviso: indice.aviso,
    vibracion_libre: { ecuacion: "m·x'' + c·x' + k·x = 0", parametros: { numero_pisos, periodo_s: T, zeta, omega_n_rad_s: +wn.toFixed(3), omega_d_rad_s: +wd.toFixed(3) }, puntos: vib },
    resonancia: { ecuacion: "m·x'' + c·x' + k·x = −m·a_suelo(t)", parametros: { periodo_s: T, periodo_suelo_s, zeta, relacion_periodos, factor_resonancia }, puntos: res },
    atenuacion: { ecuacion: '∂²u/∂t² = v²·∇²u', parametros: { distancia_epicentral_km: distancia_km, profundidad_km, distancia_hipocentral_km }, puntos: aten },
  };
}

function svgEjemplo(texto) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="100%" height="100%" fill="#e4eef8"/><path d="M180 420 L320 300 L400 360 L520 220 L640 420 Z" fill="#c9dcf3"/><text x="400" y="500" font-family="sans-serif" font-size="28" fill="#1f5baa" text-anchor="middle">${texto}</text><text x="400" y="540" font-family="sans-serif" font-size="18" fill="#6b7588" text-anchor="middle">Archivo de ejemplo (modo demostración)</text></svg>`;
  return URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
}

function datosPublicos(i) {
  const { tipo_inmueble, ciudad, anio_construccion, numero_pisos, sistema_constructivo } = i;
  return { tipo_inmueble, ciudad, anio_construccion, numero_pisos, sistema_constructivo };
}

function verificacion(insp) {
  const perito = datos().peritos.find((p) => p.id === insp.perito_id);
  const u = datos().usuarios.find((x) => x.id === perito.usuario_id);
  return {
    perito: { nombre_completo: u.nombre_completo, profesion: perito.profesion, matricula_profesional: perito.matricula_profesional },
  };
}

// ---------------------------------------------------------------- rutas
const rutas = [];
const ruta = (metodo, patron, manejador) => rutas.push({ metodo, patron: new RegExp(`^${patron}$`), manejador });

ruta('POST', '/auth/sesion', () => ({ usuario: yo(), access_token: 'demo', token_type: 'bearer', minutos_inactividad: 30 }));
ruta('POST', '/auth/registro', (_, c) => ({ id: nuevoId(), ...c, activo: true, creado_en: ahora() }));
ruta('GET', '/auth/yo', () => yo());
ruta('GET', '/auth/yo/permisos', () => permisosDe(rolDemo()));
ruta('GET', '/zonas', () => datos().zonas);

// Inmuebles
ruta('GET', '/inmuebles', (_, __, q) => {
  const lista = esAdmin() ? datos().inmuebles : datos().inmuebles.filter((i) => i.propietario_id === yo().id);
  return paginar(lista, q);
});
ruta('POST', '/inmuebles', (_, c) => {
  const { latitud, longitud, ...resto } = c;
  const i = { id: nuevoId(), propietario_id: yo().id, ...resto, ubicacion: { type: 'Point', coordinates: [longitud, latitud] }, fecha_registro: ahora(), estado: { codigo: 1, nombre: 'SIN_EVENTO_PENDIENTE', desde: ahora(), version: 1 }, ultimo_indice: null, revision_semestral: { ultima: null, proxima: en(180) }, ultimos_eventos: [], creado_en: ahora(), actualizado_en: ahora() };
  datos().inmuebles.unshift(i);
  return i;
});
ruta('GET', '/inmuebles/([\\w-]+)', ([id]) => inmueble(id));
ruta('PUT', '/inmuebles/([\\w-]+)', ([id], c) => {
  const i = inmueble(id);
  const { latitud, longitud, ...resto } = c;
  Object.assign(i, resto, { actualizado_en: ahora() });
  if (latitud !== undefined) i.ubicacion = { type: 'Point', coordinates: [longitud, latitud] };
  return i;
});
ruta('GET', '/inmuebles/([\\w-]+)/estado', ([id]) => inmueble(id).estado);
ruta('GET', '/inmuebles/([\\w-]+)/historial-estados', ([id], _, q) => paginar(datos().historial.filter((h) => h.inmueble_id === id), q));

// Bitácora
ruta('GET', '/inmuebles/([\\w-]+)/linea-cronologica', ([id], _, q) => {
  const lista = datos()
    .eventos.filter((e) => e.inmueble_id === id)
    .sort((a, b) => b.fecha_evento.localeCompare(a.fecha_evento))
    .map((e) => ({ ...e, evidencias: datos().evidencias.filter((v) => v.origen.tipo === 'EVENTO' && v.origen.id === e.id) }));
  return paginar(lista, q, 50);
});
ruta('POST', '/inmuebles/([\\w-]+)/eventos', ([id], c) => {
  const e = { id: nuevoId(), inmueble_id: id, ...c, origen: 'USUARIO', sismo_id: null, registrado_por: yo().id, creado_en: ahora() };
  datos().eventos.push(e);
  resumirEventos(inmueble(id));
  return e;
});
ruta('POST', '/archivos/autorizacion', (_, c) => ({ ruta: `inmuebles/${c.inmueble_id}/demo/${nuevoId()}.jpg`, url_subida: 'about:blank', metodo: 'PUT', encabezados: { 'Content-Type': c.tipo_contenido }, expira_en: en(0.01) }));
ruta('POST', '/peritos/archivos/autorizacion', () => ({ ruta: `peritos/p-1/${nuevoId()}.pdf`, url_subida: 'about:blank', metodo: 'PUT', encabezados: { 'Content-Type': 'application/pdf' }, expira_en: en(0.01) }));
ruta('POST', '/inmuebles/([\\w-]+)/evidencias', ([id], c) => {
  const { evento_id, ...resto } = c;
  const v = { id: nuevoId(), inmueble_id: id, origen: { tipo: 'EVENTO', id: evento_id }, ...resto, estado: 'VIGENTE', reemplazada_por: null, invalidacion: null, cargado_por: yo().id, creado_en: ahora() };
  datos().evidencias.push(v);
  return v;
});
ruta('GET', '/evidencias/([\\w-]+)/archivo', ([id]) => {
  const v = datos().evidencias.find((x) => x.id === id);
  const zona = datos().zonas.find((z) => z.id === v?.zona_id)?.nombre ?? 'Evidencia';
  return { url: svgEjemplo(zona), expira_en: en(0.01) };
});
ruta('PATCH', '/evidencias/([\\w-]+)/invalidacion', ([id], c) => {
  const v = datos().evidencias.find((x) => x.id === id);
  Object.assign(v, { estado: c.estado, reemplazada_por: c.reemplazada_por, invalidacion: { usuario_id: yo().id, fecha: ahora(), motivo: c.motivo } });
  return v;
});

// Revisiones
ruta('GET', '/inmuebles/([\\w-]+)/revisiones', ([id], _, q) => paginar(datos().revisiones.filter((r) => r.inmueble_id === id).sort((a, b) => b.fecha.localeCompare(a.fecha)), q));
ruta('POST', '/inmuebles/([\\w-]+)/revisiones', ([id], c) => {
  const i = inmueble(id);
  const ids = c.fotos.map((f) => {
    const v = { id: nuevoId(), inmueble_id: id, origen: { tipo: 'REVISION', id: 'nueva' }, ...f, estado: 'VIGENTE', reemplazada_por: null, invalidacion: null, cargado_por: yo().id, creado_en: ahora() };
    datos().evidencias.push(v);
    return v.id;
  });
  const enFlujo = i.estado.codigo === 2;
  const r = { id: nuevoId(), inmueble_id: id, fecha: ahora(), observaciones: c.observaciones, hubo_cambios: c.hubo_cambios, solicitara_inspeccion: c.solicitara_inspeccion, evidencias_ids: ids, cambio_estado_aplicado: enFlujo, registrada_por: yo().id, creado_en: ahora() };
  datos().revisiones.push(r);
  if (enFlujo) cambiarEstado(i, 3, 'RF-40', { tipo: 'REVISION', id: r.id });
  i.revision_semestral = { ultima: ahora(), proxima: en(180) };
  return r;
});

// Sismos
ruta('GET', '/sismos', (_, __, q) => paginar(q.get('solo_relevantes') === 'true' ? datos().sismos.filter((s) => s.es_relevante) : datos().sismos, q));
ruta('GET', '/sismos/([\\w-]+)', ([id]) => datos().sismos.find((s) => s.id === id));

// Solicitudes e inspecciones
ruta('GET', '/inmuebles/([\\w-]+)/solicitudes-inspeccion', ([id], _, q) => paginar(datos().solicitudes.filter((s) => s.inmueble_id === id), q));
ruta('POST', '/inmuebles/([\\w-]+)/solicitudes-inspeccion', ([id], c) => {
  const i = inmueble(id);
  const s = { id: nuevoId(), inmueble_id: id, solicitada_por: yo().id, ...c, estado: 'SOLICITADA', perito_id: null, asignada_por: null, cambios_estado: [], creado_en: ahora() };
  datos().solicitudes.unshift(s);
  if ([2, 3].includes(i.estado.codigo)) cambiarEstado(i, 4, 'RF-41', { tipo: 'SOLICITUD', id: s.id });
  return s;
});
ruta('GET', '/admin/solicitudes-inspeccion', (_, __, q) => paginar(q.get('estado') ? datos().solicitudes.filter((s) => s.estado === q.get('estado')) : datos().solicitudes, q));
ruta('POST', '/admin/solicitudes-inspeccion/([\\w-]+)/asignacion', ([id], c) => {
  const s = datos().solicitudes.find((x) => x.id === id);
  Object.assign(s, { perito_id: c.perito_id, estado: 'ASIGNADA', asignada_por: yo().id });
  return s;
});
ruta('GET', '/peritos/solicitudes', (_, __, q) => paginar(datos().solicitudes.filter((s) => s.perito_id === 'p-1'), q));
ruta('GET', '/inmuebles/([\\w-]+)/inspecciones', ([id]) => datos().inspecciones.filter((i) => i.inmueble_id === id));
ruta('GET', '/inspecciones/([\\w-]+)', ([id]) => datos().inspecciones.find((i) => i.id === id) ?? (() => { throw error(404, 'Inspección no encontrada'); })());
ruta('POST', '/solicitudes-inspeccion/([\\w-]+)/inspeccion', ([id], c) => {
  const s = datos().solicitudes.find((x) => x.id === id);
  const { evidencias, ...resto } = c;
  const insp = { id: nuevoId(), solicitud_id: id, inmueble_id: s.inmueble_id, perito_id: 'p-1', version: 1, version_anterior_id: null, es_version_activa: true, ...resto, evidencias_ids: [], firma: { firmada: false }, constancia: null, aviso_legal: datos().inspecciones[0].aviso_legal, creado_en: ahora() };
  datos().inspecciones.push(insp);
  return insp;
});
ruta('PUT', '/inspecciones/([\\w-]+)', ([id], c) => Object.assign(datos().inspecciones.find((i) => i.id === id), c));
ruta('POST', '/inspecciones/([\\w-]+)/firma', ([id], c) => {
  const insp = datos().inspecciones.find((i) => i.id === id);
  if (!c.contrasena) throw error(401, 'Contraseña incorrecta: no se firmó la inspección');
  const codigo = `ST-2026-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
  insp.firma = { firmada: true, fecha: ahora(), metodo: 'CONTRASENA', huella_sha256: hash() };
  insp.constancia = { codigo, emitida_en: ahora(), vigencia_meses: c.vigencia_meses, vigente_hasta: en(30 * c.vigencia_meses), estado: 'VIGENTE' };
  const s = datos().solicitudes.find((x) => x.id === insp.solicitud_id);
  if (s) s.estado = 'FIRMADA';
  const i = inmueble(insp.inmueble_id);
  if (i.estado.codigo === 4) cambiarEstado(i, 5, 'RF-42', { tipo: 'INSPECCION', id: insp.id });
  return insp;
});
ruta('POST', '/inspecciones/([\\w-]+)/correccion', ([id], c) => {
  const anterior = datos().inspecciones.find((i) => i.id === id);
  anterior.es_version_activa = false;
  const { evidencias, ...cambios } = c;
  const nueva = { ...anterior, ...cambios, id: nuevoId(), version: anterior.version + 1, version_anterior_id: anterior.id, es_version_activa: true, firma: { firmada: false }, constancia: null, creado_en: ahora() };
  datos().inspecciones.push(nueva);
  return nueva;
});
ruta('GET', '/constancias/([\\w-]+)', ([codigo]) => {
  const insp = datos().inspecciones.find((i) => i.constancia?.codigo === codigo.toUpperCase());
  if (!insp) throw error(404, 'No existe una constancia con ese código');
  const c = insp.constancia;
  return {
    codigo: c.codigo, estado: c.estado, integra: true, es_version_activa: insp.es_version_activa, version: insp.version, emitida_en: c.emitida_en,
    vigente_hasta: c.vigente_hasta, fecha_inspeccion: insp.fecha_inspeccion, huella_sha256: insp.firma.huella_sha256, ...verificacion(insp),
    inmueble: datosPublicos(inmueble(insp.inmueble_id)), aviso_legal: insp.aviso_legal,
  };
});

// Enlaces
ruta('GET', '/inmuebles/([\\w-]+)/enlaces', ([id]) => datos().enlaces.filter((e) => e.inmueble_id === id));
ruta('POST', '/inmuebles/([\\w-]+)/enlaces', ([id], c) => {
  const e = { id: nuevoId(), inmueble_id: id, codigo: Math.random().toString(36).slice(2, 14), campos_compartidos: c.campos_compartidos, activo: true, creado_por: yo().id, creado_en: ahora(), revocado_en: null };
  datos().enlaces.unshift(e);
  return e;
});
ruta('DELETE', '/enlaces/([\\w-]+)', ([id]) => Object.assign(datos().enlaces.find((e) => e.id === id), { activo: false, revocado_en: ahora() }));
ruta('GET', '/publico/([\\w-]+)', ([codigo]) => {
  const e = datos().enlaces.find((x) => x.codigo === codigo && x.activo);
  if (!e) throw error(404, 'Enlace inexistente o revocado');
  const i = inmueble(e.inmueble_id);
  const vista = { inmueble: datosPublicos(i), campos_compartidos: e.campos_compartidos, aviso: 'Información compartida por el propietario. SafeTrace no declara la condición estructural del inmueble.' };
  if (e.campos_compartidos.includes('LINEA_CRONOLOGICA')) vista.linea_cronologica = datos().eventos.filter((x) => x.inmueble_id === i.id).map(({ tipo, fecha_evento, descripcion, zona_id }) => ({ tipo, fecha_evento, descripcion, zona_id }));
  if (e.campos_compartidos.includes('FOTOS')) vista.fotos = datos().evidencias.filter((v) => v.inmueble_id === i.id && v.tipo_archivo === 'FOTO' && v.estado === 'VIGENTE').map((v) => ({ zona_id: v.zona_id, fecha: v.creado_en, url: null, expira_en: null }));
  if (e.campos_compartidos.includes('INSPECCIONES_FIRMADAS'))
    vista.inspecciones_firmadas = datos().inspecciones.filter((x) => x.inmueble_id === i.id && x.constancia?.estado === 'VIGENTE' && x.es_version_activa).map((x) => ({
      fecha_inspeccion: x.fecha_inspeccion, hallazgos: x.hallazgos, resultado: x.resultado, constancia: x.constancia, ...verificacion(x), aviso_legal: x.aviso_legal,
    }));
  return vista;
});

// IA e índice
ruta('GET', '/inmuebles/([\\w-]+)/analisis-ia', ([id], _, q) => paginar(datos().analisis.filter((a) => a.inmueble_id === id), q));
ruta('POST', '/analisis-ia/([\\w-]+)/reintento', ([id]) => Object.assign(datos().analisis.find((a) => a.id === id), { estado: 'PENDIENTE' }));
ruta('GET', '/inmuebles/([\\w-]+)/indice', ([id]) => datos().indices.find((x) => x.inmueble_id === id) ?? (() => { throw error(404, 'El inmueble aún no tiene índice calculado'); })());
ruta('GET', '/inmuebles/([\\w-]+)/indice/modelos', ([id]) => {
  const ix = datos().indices.find((x) => x.inmueble_id === id);
  if (!ix) throw error(404, 'El inmueble aún no tiene índice calculado');
  return curvas(ix);
});
ruta('GET', '/admin/sismos/([\\w-]+)/priorizacion', ([id], _, q) => paginar(datos().indices.filter((x) => x.sismo_id === id).sort((a, b) => b.valor - a.valor), q));

// Notificaciones
ruta('GET', '/notificaciones', (_, __, q) => paginar(datos().notificaciones.filter((n) => n.usuario_id === yo().id), q));

// Perito
ruta('GET', '/peritos/mi-estado', () => datos().peritos.find((p) => p.usuario_id === yo().id) ?? (() => { throw error(404, 'Primero registre su perfil profesional'); })());
ruta('POST', '/peritos/documentos', (_, c) => {
  const p = datos().peritos.find((x) => x.usuario_id === yo().id);
  p.documentos.push(...c.documentos.map((d) => ({ documento_id: nuevoId(), ...d, cargado_en: ahora() })));
  return p;
});
ruta('GET', '/peritos/documentos/([\\w-]+)/archivo', () => ({ url: svgEjemplo('Documento profesional'), expira_en: en(0.01) }));

// Administración
ruta('GET', '/admin/usuarios', (_, __, q) => {
  let lista = datos().usuarios;
  if (q.get('rol')) lista = lista.filter((u) => u.rol === q.get('rol'));
  if (q.get('activo')) lista = lista.filter((u) => String(u.activo) === q.get('activo'));
  return paginar(lista, q);
});
ruta('PATCH', '/admin/usuarios/([\\w-]+)/estado', ([id], c) => Object.assign(datos().usuarios.find((u) => u.id === id), c));
ruta('PATCH', '/admin/usuarios/([\\w-]+)/rol', ([id], c) => Object.assign(datos().usuarios.find((u) => u.id === id), c));
ruta('GET', '/admin/peritos', (_, __, q) => paginar(q.get('estado') ? datos().peritos.filter((p) => p.estado_credencial === q.get('estado')) : datos().peritos, q));
ruta('GET', '/admin/peritos/([\\w-]+)/documentos/([\\w-]+)/archivo', () => ({ url: svgEjemplo('Documento del perito'), expira_en: en(0.01) }));
ruta('POST', '/admin/peritos/([\\w-]+)/validacion', ([id], c) => {
  const p = datos().peritos.find((x) => x.id === id);
  p.estado_credencial = c.decision === 'APROBADO' ? 'VALIDADO' : 'RECHAZADO';
  p.validaciones.push({ ...c, validado_por: yo().id, fecha: ahora() });
  return p;
});
ruta('POST', '/admin/peritos/([\\w-]+)/inconsistencia', ([id], c) => {
  const p = datos().peritos.find((x) => x.id === id);
  p.estado_credencial = 'INCONSISTENTE';
  p.validaciones.push({ decision: 'INCONSISTENTE', motivo: c.motivo, validado_por: yo().id, fecha: ahora(), documentos_revisados: [] });
  return p;
});
ruta('GET', '/admin/configuracion', () => datos().configuracion);
ruta('PUT', '/admin/configuracion', (_, c) => Object.assign(datos().configuracion, c, { actualizado_en: ahora(), actualizado_por: yo().id }));
ruta('GET', '/admin/auditoria', (_, __, q) => {
  let lista = datos().auditoria;
  if (q.get('coleccion')) lista = lista.filter((r) => r.coleccion === q.get('coleccion'));
  if (q.get('accion')) lista = lista.filter((r) => r.accion === q.get('accion'));
  if (q.get('documento_id')) lista = lista.filter((r) => r.documento_id === q.get('documento_id'));
  return paginar(lista, q);
});
ruta('GET', '/admin/solicitudes-supresion', (_, __, q) => paginar(q.get('estado') ? datos().supresiones.filter((s) => s.estado === q.get('estado')) : datos().supresiones, q));
ruta('POST', '/admin/solicitudes-supresion/([\\w-]+)/atencion', ([id]) =>
  Object.assign(datos().supresiones.find((s) => s.id === id), {
    estado: 'ATENDIDA', atendida_por: yo().id, fecha_atencion: ahora(),
    datos_eliminados: ['nombre_completo', 'correo', 'sesiones'],
    datos_conservados: [{ dato: 'Inspecciones firmadas', motivo: 'Integridad de constancias verificables por terceros' }, { dato: 'Registros de auditoría', motivo: 'Obligación de trazabilidad (sin datos personales)' }],
  }),
);
ruta('POST', '/cuentas/supresion', () => {
  const s = { id: nuevoId(), usuario_id: yo().id, fecha_solicitud: ahora(), estado: 'RECIBIDA', datos_eliminados: [], datos_conservados: [], atendida_por: null, fecha_atencion: null };
  datos().supresiones.push(s);
  return s;
});
ruta('GET', '/admin/roles', (_, __, q) => paginar(datos().roles, q));
ruta('PUT', '/admin/roles/([\\w-]+)', ([id], c) => Object.assign(datos().roles.find((r) => r.id === id), c));
ruta('PATCH', '/admin/roles/([\\w-]+)/estado', ([id], c) => Object.assign(datos().roles.find((r) => r.id === id), c));
ruta('POST', '/admin/roles', (_, c) => { const r = { id: c.nombre_rol, ...c }; datos().roles.push(r); return r; });
ruta('GET', '/admin/modulos', () => datos().modulos);
ruta('PUT', '/admin/modulos/([\\w-]+)', ([id], c) => Object.assign(datos().modulos.find((r) => r.id === id), c));
ruta('PATCH', '/admin/modulos/([\\w-]+)/estado', ([id], c) => Object.assign(datos().modulos.find((r) => r.id === id), c));
ruta('POST', '/admin/modulos', (_, c) => { const m = { id: c.nombre_modulo, ...c }; datos().modulos.push(m); return m; });
ruta('GET', '/admin/permisos', (_, __, q) => datos().permisos.filter((p) => (!q.get('rol') || p.rol === q.get('rol')) && (!q.get('modulo_id') || p.modulo === q.get('modulo_id'))));
ruta('PUT', '/admin/permisos/([\\w-]+)/([\\w-]+)', ([modulo, rol], c) => Object.assign(datos().permisos.find((p) => p.modulo === modulo && p.rol === rol), c));
ruta('POST', '/admin/permisos', (_, c) => {
  const p = { id: nuevoId(), insertar: false, actualizar: false, seleccionar: false, borrar: false, ...c };
  datos().permisos.push(p);
  return p;
});

export async function responderDemo(metodo, url, cuerpo) {
  await new Promise((r) => setTimeout(r, 120)); // latencia simulada
  const [camino, consulta = ''] = url.split('?');
  const q = new URLSearchParams(consulta);
  for (const r of rutas) {
    if (r.metodo !== metodo) continue;
    const m = camino.match(r.patron);
    if (m) {
      const resultado = r.manejador(m.slice(1).map(decodeURIComponent), cuerpo ?? {}, q);
      return resultado === undefined ? null : structuredClone(resultado);
    }
  }
  throw error(501, `Ruta no disponible en el modo demostración: ${metodo} ${camino}`);
}
