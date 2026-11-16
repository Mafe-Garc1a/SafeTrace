/** Error con el formato único del backend: {detail, codigo, request_id, errores}. */
export class ErrorApi extends Error {
  constructor({ estado, detail, codigo, request_id, errores }) {
    super(typeof detail === 'string' ? detail : 'No se pudo completar la operación');
    this.estado = estado;
    this.codigo = codigo;
    this.requestId = request_id;
    this.errores = errores ?? [];
  }
}
