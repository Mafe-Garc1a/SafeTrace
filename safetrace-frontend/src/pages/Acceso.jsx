/**
 * Inicio de sesión y registro (RF-01, RF-02, RF-07).
 * Diseño de los mockups «Iniciar sesión - Estilo Blueprint Arquitectónico» y «Crear cuenta - Institucional».
 */
import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Activity, ArrowRight, ClipboardCheck, History, QrCode, ShieldCheck } from 'lucide-react';
import { api } from '@/api/cliente';
import { useSesion } from '@/context/SesionContext';
import { Aviso, Boton, Casilla, Entrada, ErrorCaja } from '@/components/ui';
import { Plano } from '@/components/Inmueble';
import { ROLES } from '@/lib/formato';

/** Marco de las páginas públicas (verificación de constancias y enlace público). */
export function MarcoPublico({ children, derecha }) {
  return (
    <div className="publico">
      <header className="publico-barra">
        <Link to="/" className="marca" style={{ border: 'none' }}>
          <span className="marca-icono"><img src="/logo.svg" alt="" /></span>
          <div>
            <strong>SafeTrace</strong>
            <small>Historial. Evidencia. Confianza.</small>
          </div>
        </Link>
        {derecha ?? (
          <Link to="/verificar" className="boton boton-secundario boton-pequeno">
            <QrCode size={16} aria-hidden /> Verificar constancia
          </Link>
        )}
      </header>
      {children}
      <footer className="pie-publico">
        SafeTrace no declara la condición estructural de un inmueble ni certifica la NSR-10. Proyecto integrador · CIAF 2026.
      </footer>
    </div>
  );
}

function MarcoPlano({ claro = false, children }) {
  return (
    <div className={`plano-pagina ${claro ? 'claro' : ''}`}>
      <div className="plano-cinta">
        <span>SafeTrace · CIAF 2026</span>
        <span>Historia clínica verificable del inmueble</span>
        <Link to="/verificar" style={{ color: 'inherit' }}>Verificar constancia ↗</Link>
      </div>
      <div className="plano-cuerpo">
        <div>
          <Link to="/" className="plano-marca">SafeTrace <span>/ Historia clínica del inmueble</span></Link>
          <h1 className="plano-titulo">
            Cada inmueble tiene una historia. Nosotros la <span className="resaltado">registramos.</span>
          </h1>
          <div className="plano-dibujo"><Plano claro={claro} /></div>
          <ul className="plano-lista">
            <li><History size={16} /> Bitácora con eventos, fotos y documentos</li>
            <li><Activity size={16} /> Sismos del SGC y del USGS por ubicación</li>
            <li><ClipboardCheck size={16} /> Revisión propia e inspección de un perito</li>
            <li><ShieldCheck size={16} /> Constancia con QR verificable por cualquiera</li>
          </ul>
        </div>
        {children}
      </div>
      <div className="plano-pie">
        <span>SafeTrace certifica quién inspeccionó, cuándo y con qué evidencia</span>
        <span>Ley 1581 de 2012 · No declara la condición estructural del inmueble</span>
      </div>
    </div>
  );
}

function AccesoDemo() {
  const { iniciarDemo } = useSesion();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const entrar = async (rol, destino = '/inicio') => {
    await iniciarDemo(rol);
    navegar(destino, { replace: true });
  };

  // Acceso directo para presentaciones: /ingresar?demo=PROPIETARIO&ir=/inmuebles
  useEffect(() => {
    const parametros = new URLSearchParams(ubicacion.search);
    const rol = parametros.get('demo');
    const destino = parametros.get('ir');
    if (rol && ROLES[rol]) entrar(rol, destino?.startsWith('/') ? destino : '/inicio');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div className="separador">o explore sin backend</div>
      <div className="demo-roles">
        {Object.entries(ROLES).map(([rol, texto]) => (
          <Boton key={rol} variante="secundario" tamano="pequeno" onClick={() => entrar(rol)}>
            {texto}
          </Boton>
        ))}
      </div>
      <p className="texto-mini">El modo demostración usa datos de ejemplo y no guarda nada.</p>
    </>
  );
}

export function Ingresar() {
  const { iniciar, aviso, setAviso } = useSesion();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const [correo, setCorreo] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      await iniciar(correo.trim(), contrasena);
      navegar(ubicacion.state?.desde ?? '/inicio', { replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <MarcoPlano>
      <form className="plano-tarjeta" onSubmit={enviar}>
        <span className="plano-pildora">Portal institucional · Acceso seguro</span>
        <div>
          <h2>Bienvenido de nuevo</h2>
          <p className="texto-suave">Ingrese para gestionar el historial verificable de sus inmuebles.</p>
        </div>
        {ubicacion.state?.registrado && <Aviso tono="exito" titulo="Cuenta creada. Ya puede iniciar sesión." />}
        {aviso && <Aviso tono="info" titulo={aviso} onCerrar={() => setAviso('')} />}
        <ErrorCaja error={error} />
        <Entrada etiqueta="Correo electrónico" type="email" autoComplete="email" placeholder="nombre@ejemplo.com" value={correo} onChange={(e) => setCorreo(e.target.value)} requerido />
        <Entrada etiqueta="Contraseña" type="password" autoComplete="current-password" placeholder="••••••••" value={contrasena} onChange={(e) => setContrasena(e.target.value)} requerido />
        <Boton type="submit" variante="acento" cargando={enviando} className="boton-bloque" style={{ padding: '12px 16px', fontSize: '1rem' }}>
          Iniciar sesión <ArrowRight size={17} />
        </Boton>
        <p className="texto-suave" style={{ fontSize: '0.88rem', textAlign: 'center' }}>
          ¿No tiene cuenta registrada? <Link to="/registro">Crear cuenta</Link>
        </p>
        <AccesoDemo />
      </form>
    </MarcoPlano>
  );
}

function fuerzaContrasena(c) {
  return [c.length >= 8, /[A-Z]/.test(c) && /[a-z]/.test(c), /\d/.test(c), /[^A-Za-z0-9]/.test(c) || c.length >= 12].filter(Boolean).length;
}

export function Registro() {
  const navegar = useNavigate();
  const [datos, setDatos] = useState({ nombre_completo: '', correo: '', contrasena: '', confirmar: '', rol: 'PROPIETARIO', acepta_politica: false });
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);
  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });
  const noCoinciden = datos.confirmar && datos.confirmar !== datos.contrasena;
  const fuerza = fuerzaContrasena(datos.contrasena);

  const enviar = async (e) => {
    e.preventDefault();
    if (noCoinciden) return;
    setEnviando(true);
    setError(null);
    try {
      const { confirmar, ...cuerpo } = datos;
      await api('/auth/registro', { metodo: 'POST', cuerpo: { ...cuerpo, correo: cuerpo.correo.trim() }, sinToken: true });
      navegar('/ingresar', { state: { registrado: true } });
    } catch (err) {
      setError(err);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <MarcoPlano claro>
      <form className="plano-tarjeta" onSubmit={enviar}>
        <span className="plano-pildora">Portal institucional · Registro ciudadano</span>
        <div>
          <h2>Crea tu cuenta</h2>
          <p className="texto-suave">Solo pedimos los datos mínimos.</p>
        </div>
        <ErrorCaja error={error} />
        <div>
          <span className="sobretitulo">Tipo de perfil</span>
          <div className="perfiles" style={{ marginTop: 6 }}>
            <label className="perfil">
              <input type="radio" name="rol" value="PROPIETARIO" checked={datos.rol === 'PROPIETARIO'} onChange={cambiar('rol')} />
              <strong>Soy propietario</strong>
              <span>Gestiono mis inmuebles</span>
            </label>
            <label className="perfil">
              <input type="radio" name="rol" value="PERITO" checked={datos.rol === 'PERITO'} onChange={cambiar('rol')} />
              <strong>Soy perito</strong>
              <span>Inspección y firma</span>
            </label>
          </div>
          {datos.rol === 'PERITO' && <p className="texto-mini" style={{ marginTop: 6 }}>Después de ingresar, registre su perfil profesional para que un administrador lo valide.</p>}
        </div>
        <Entrada etiqueta="Nombre completo" placeholder="Ej. Laura Martínez Gómez" value={datos.nombre_completo} onChange={cambiar('nombre_completo')} minLength={3} maxLength={100} requerido />
        <Entrada etiqueta="Correo electrónico" type="email" autoComplete="email" placeholder="tu.correo@ejemplo.com" value={datos.correo} onChange={cambiar('correo')} requerido />
        <div className="pila-chica">
          <Entrada etiqueta="Contraseña" type="password" autoComplete="new-password" minLength={8} maxLength={72} value={datos.contrasena} onChange={cambiar('contrasena')} requerido />
          <div className="fuerza" aria-label={`Fortaleza de la contraseña: ${fuerza} de 4`}>
            {[1, 2, 3, 4].map((n) => <i key={n} className={n <= fuerza ? 'on' : ''} />)}
          </div>
          <span className="texto-mini">Mínimo 8 caracteres{fuerza >= 3 ? ' · Contraseña fuerte' : ''}</span>
        </div>
        <Entrada etiqueta="Confirmar contraseña" type="password" autoComplete="new-password" value={datos.confirmar} onChange={cambiar('confirmar')} requerido />
        {noCoinciden && <small className="texto-error">Las contraseñas no coinciden.</small>}
        <Casilla
          checked={datos.acepta_politica}
          onChange={cambiar('acepta_politica')}
          required
          etiqueta="Acepto la política de tratamiento de datos personales (Ley 1581 de 2012), versión v1.0."
        />
        <Boton type="submit" variante="acento" cargando={enviando} disabled={!datos.acepta_politica} className="boton-bloque" style={{ padding: '12px 16px', fontSize: '1rem' }}>
          Crear cuenta <ArrowRight size={17} />
        </Boton>
        <p className="texto-suave" style={{ fontSize: '0.88rem', textAlign: 'center' }}>
          ¿Ya tiene una cuenta registrada? <Link to="/ingresar">Iniciar sesión</Link>
        </p>
      </form>
    </MarcoPlano>
  );
}
