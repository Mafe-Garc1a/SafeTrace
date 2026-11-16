import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Bell,
  Building2,
  ClipboardCheck,
  ClipboardList,
  FileCheck2,
  FileSearch,
  Gauge,
  HelpCircle,
  History,
  Home,
  KeyRound,
  ListOrdered,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  UserCog,
  UserRound,
  Users,
  Boxes,
  Eraser,
} from 'lucide-react';
import { useSesion } from '@/context/SesionContext';
import { ROLES } from '@/lib/formato';

/** Menú según los permisos del rol (GET /auth/yo/permisos), no según el nombre del rol. */
function useMenu() {
  const { puede } = useSesion();
  const esPerito = puede('inspecciones', 'insertar');
  const supervisa = puede('supervision_inmuebles');
  // Misma organización que los mockups de Figma (SafeTrace / Menú lateral)
  const grupos = [
    {
      titulo: null,
      items: [
        { a: '/inicio', texto: 'Inicio', icono: Home, ver: true },
        { a: supervisa ? '/admin/inmuebles' : '/inmuebles', texto: supervisa ? 'Inmuebles' : 'Mis inmuebles', icono: Building2, ver: supervisa || puede('inmuebles', 'insertar') },
        { a: '/perito/solicitudes', texto: 'Mis asignaciones', icono: ClipboardCheck, ver: esPerito },
        { a: '/bitacora', texto: 'Bitácora', icono: History, ver: !esPerito },
        { a: supervisa && puede('asignacion_peritos') ? '/admin/solicitudes' : '/inspecciones', texto: 'Inspecciones', icono: ClipboardList, ver: true },
        { a: '/constancias', texto: 'Constancias', icono: FileCheck2, ver: true },
        { a: '/sismos', texto: 'Sismos', icono: Activity, ver: true },
        { a: '/perito/perfil', texto: 'Mi perfil', icono: UserRound, ver: puede('perfil_perito', 'seleccionar') },
        { a: '/cuenta', texto: 'Configuración', detalle: 'Privacidad y datos', icono: Settings, ver: true },
      ],
    },
    {
      titulo: 'Administración',
      items: [
        { a: '/admin/usuarios', texto: 'Usuarios', icono: Users, ver: puede('usuarios') },
        { a: '/admin/peritos', texto: 'Validación de peritos', icono: ShieldCheck, ver: puede('validacion_peritos') },
        { a: '/admin/priorizacion', texto: 'Priorización por sismo', icono: ListOrdered, ver: puede('priorizacion') },
        { a: '/admin/auditoria', texto: 'Auditoría', icono: FileSearch, ver: puede('auditoria') },
        { a: '/admin/configuracion', texto: 'Configuración de sismos', icono: Gauge, ver: puede('configuracion') },
        { a: '/admin/supresion', texto: 'Supresión de datos', icono: Eraser, ver: puede('supresion') },
      ],
    },
    {
      titulo: 'Seguridad',
      items: [
        { a: '/admin/roles', texto: 'Roles', icono: UserCog, ver: puede('roles') },
        { a: '/admin/modulos', texto: 'Módulos', icono: Boxes, ver: puede('modulos') },
        { a: '/admin/permisos', texto: 'Permisos', icono: KeyRound, ver: puede('permisos') },
      ],
    },
  ];
  return grupos.map((g) => ({ ...g, items: g.items.filter((i) => i.ver) })).filter((g) => g.items.length);
}

function Buscador() {
  const navegar = useNavigate();
  const [texto, setTexto] = useState('');
  const { puede } = useSesion();
  const enviar = (e) => {
    e.preventDefault();
    const q = texto.trim();
    if (!q) return;
    // Un código de constancia (ST-AAAA-XXXXXX) va a la verificación; lo demás filtra los inmuebles
    if (/^ST-\d{4}-/i.test(q)) navegar(`/verificar/${encodeURIComponent(q.toUpperCase())}`);
    else navegar(`${puede('supervision_inmuebles') ? '/admin/inmuebles' : '/inmuebles'}?q=${encodeURIComponent(q)}`);
  };
  return (
    <form className="buscador" onSubmit={enviar} role="search">
      <Search size={16} />
      <input type="search" aria-label="Buscar" placeholder="Buscar inmueble, dirección o código de constancia…" value={texto} onChange={(e) => setTexto(e.target.value)} />
    </form>
  );
}

export default function Layout() {
  const { usuario, cerrar, demo } = useSesion();
  const grupos = useMenu();
  const [abierto, setAbierto] = useState(false);
  const ubicacion = useLocation();

  useEffect(() => {
    setAbierto(false);
    window.scrollTo(0, 0);
  }, [ubicacion.pathname]);

  const iniciales = (usuario?.nombre_completo ?? '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase();

  return (
    <div className="app">
      {abierto && <div className="velo" onClick={() => setAbierto(false)} aria-hidden />}
      <aside className={`lateral ${abierto ? 'abierta' : ''}`}>
        <NavLink to="/inicio" className="marca">
          <span className="marca-icono"><img src="/logo.svg" alt="" /></span>
          <div>
            <strong>SafeTrace</strong>
            <small>Historial. Evidencia. Confianza.</small>
          </div>
        </NavLink>
        <div className="espacio">
          <b>Espacio de trabajo</b>
          <span>{ROLES[usuario?.rol] ?? 'Portal'}</span>
        </div>
        <nav className="menu" aria-label="Menú principal">
          {grupos.map((g) => (
            <div key={g.titulo ?? 'principal'} className="pila-chica" style={{ gap: 2 }}>
              {g.titulo && <div className="menu-grupo">{g.titulo}</div>}
              {g.items.map(({ a, texto, detalle, icono: Icono }) => (
                <NavLink key={a} to={a}>
                  <Icono size={17} aria-hidden />
                  <span>{texto}{detalle && <small>{detalle}</small>}</span>
                </NavLink>
              ))}
            </div>
          ))}

        </nav>
        <div className="ayuda">
          <strong><HelpCircle size={15} /> ¿Necesitas ayuda?</strong>
          Consulta cómo funciona el proceso de revisión.
          <br />
          <Link to="/guia">Guía del proceso ↗</Link>
        </div>
        <div className="lateral-pie">
          <button type="button" onClick={() => cerrar()}>
            <LogOut size={16} aria-hidden /> Cerrar sesión
          </button>
          <span>v{__APP_VERSION__}</span>
        </div>
      </aside>

      <div className="principal">
        {demo && (
          <div className="franja-demo">
            Modo demostración: los datos son de ejemplo y nada se guarda en el backend.
          </div>
        )}
        <header className="barra">
          <button type="button" className="icono-boton barra-menu" onClick={() => setAbierto(true)} aria-label="Abrir menú">
            <Menu size={20} />
          </button>
          <Buscador />
          <div className="barra-usuario">
            <Link to="/notificaciones" className="campana" aria-label="Notificaciones">
              <Bell size={19} />
            </Link>
            <span className="separador-v oculto-movil" />
            <Link to="/cuenta" className="fila" style={{ gap: 10, textDecoration: 'none', color: 'inherit' }}>
              <div className="avatar" aria-hidden>
                {iniciales}
              </div>
              <div className="oculto-movil">
                <div className="nombre">{usuario?.nombre_completo}</div>
                <div className="rol">{ROLES[usuario?.rol] ?? usuario?.rol}</div>
              </div>
            </Link>
          </div>
        </header>
        <main className="contenido">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
