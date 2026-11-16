import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Layout from '@/components/Layout';
import { useSesion } from '@/context/SesionContext';
import { Ingresar, Registro } from '@/pages/Acceso';
import Inicio from '@/pages/Inicio';
import { Vacio } from '@/components/ui';

function Protegida({ children }) {
  const { autenticado } = useSesion();
  const ubicacion = useLocation();
  if (!autenticado) return <Navigate to="/ingresar" replace state={{ desde: ubicacion.pathname }} />;
  return children;
}

function SoloInvitado({ children }) {
  const { autenticado } = useSesion();
  return autenticado ? <Navigate to="/inicio" replace /> : children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/ingresar" element={<SoloInvitado><Ingresar /></SoloInvitado>} />
      <Route path="/registro" element={<SoloInvitado><Registro /></SoloInvitado>} />

      <Route element={<Protegida><Layout /></Protegida>}>
        <Route path="/" element={<Navigate to="/inicio" replace />} />
        <Route path="/inicio" element={<Inicio />} />
        <Route path="*" element={<Vacio titulo="Página no encontrada">La dirección no existe o se movió.</Vacio>} />
      </Route>
    </Routes>
  );
}
