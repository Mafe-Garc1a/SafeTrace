/** Inicio: resumen según los permisos del usuario. */
import { useSesion } from '@/context/SesionContext';
import { Encabezado } from '@/components/ui';



export default function Inicio() {
  const { usuario } = useSesion();
  const nombre = usuario?.nombre_completo?.split(' ')[0] ?? '';
  return (
    <Encabezado
      titulo= {`Bienvenido, ${nombre}`}
      descripcion="Aqui van los módulos, en el menú lateral."
    />
  );
}
