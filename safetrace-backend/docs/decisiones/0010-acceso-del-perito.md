# El acceso del perito depende de permiso y asignación

**Fecha:** 2026-11-06

**Decisión:** Para ver un inmueble ajeno se exige el permiso `seleccionar` en `inspecciones` y estar asignado. Ya no se compara `usuario["rol"] == "PERITO"`.

**Motivo:** Los roles se administran en la base de datos, así que el código no debe depender de un nombre fijo. Exigir también el permiso impide que quien dejó de ser perito conserve el acceso.
