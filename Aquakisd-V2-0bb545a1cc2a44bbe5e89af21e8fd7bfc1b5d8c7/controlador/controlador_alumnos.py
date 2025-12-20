from modelo.manejador_db import ManejadorDB
from vista.editar.editar_alumno_vista import EditarAlumnoVista
from PySide6.QtWidgets import QMessageBox, QDialog
from PySide6.QtCore import Signal, QObject
from vista.editar.historial_vista import HistorialVista
class ControladorAlumnos(QObject):
    alumno_actualizado = Signal()
            
    def __init__(self, vista, modelo):
        super().__init__()
        self.modelo = modelo if modelo else ManejadorDB()
        self.vista = vista
        self.vista.set_controlador(self)
        self.cargar_datos_iniciales()

        try:
            # preferir la convención set_controlador si está disponible
            if hasattr(self.vista, 'set_controlador'):
                self.vista.set_controlador(self)
            elif hasattr(self.vista, 'setControlador'):
                self.vista.setControlador(self)
            else:
                self.vista.controlador = self
        except Exception:
            try:
                self.vista.controlador = self
            except Exception:
                pass
        self._connect_events()
        self.cargar_programas_clases()
        self.cargar_alumnos()
    
    def set_vista(self, vista):
        self.vista = vista
    

    def mostrar_historial_alumno(self, alumno_id):
        try:
            historial = self.modelo.obtener_historial_alumno(alumno_id)
            vista_historial = HistorialVista(historial, self.vista)
            vista_historial.exec()
        except Exception as e:
            QMessageBox.critical(self.vista, "Error", f"No se pudo cargar el historial: {e}")
                
    def cargar_datos_iniciales(self):
        """Carga inicial mínima de datos. Este método existe porque el
        constructor lo invoca en algunos flujos; aquí delegamos a los
        métodos que preparan la vista y la tabla si están disponibles.
        """
        try:
            self.cargar_programas_clases()
        except Exception:
            pass
        try:
            self.cargar_alumnos()
        except Exception:
            pass

    def _connect_events(self):
        # la vista ya conecta señales hacia los métodos _on_search; mantenemos interfaz
        pass

    def cargar_programas_clases(self):
        programas = self.modelo.obtener_programas()
        clases = self.modelo.obtener_clases_y_descripcion()
        try:
            self.vista.set_programas(programas)
            self.vista.set_clases(clases)
        except Exception:
            pass

    def cargar_alumnos(self, estado=None):
        filas = self.modelo.listar_alumnos(estado=estado)
        self.vista.limpiar_tabla()
        for fila in filas:
            self.vista.agregar_fila(fila)

    def buscar_alumnos(self, query=None, estado=None, id_programa=None, id_clase=None, edad=None):
        """
        Buscar alumnos usando filtros pasados por la vista.
        """
        try:
            filas = self.modelo.buscar_alumnos(
                query=query,
                estado=estado,
                id_programa=id_programa,
                id_clase=id_clase,
                edad=edad
            )
        except Exception:
            # Fallback a listar todos si ocurre algún error en la consulta
            filas = self.modelo.listar_alumnos()

        # Actualizar la vista
        try:
            self.vista.limpiar_tabla()
            for fila in filas:
                self.vista.agregar_fila(fila)
        except Exception:
            pass
            
    def editar_alumno(self, alumno_id):
        # 1. Obtener datos del alumno y recursos
        datos_alumno = self.modelo.obtener_alumno_por_id(alumno_id)
        if not datos_alumno:
            QMessageBox.warning(self.vista, "Error", "No se pudo encontrar al alumno seleccionado.")
            return

        clases = self.modelo.obtener_clases_y_descripcion()
        programas = self.modelo.obtener_programas()

        # 2. Crear la vista de edición
        vista_edicion = EditarAlumnoVista(
            datos_alumno=datos_alumno,
            programas=programas,
            clases=clases,
            parent=self.vista
        )

        # 3. Conectar la señal del botón de historial ANTES de mostrar el diálogo
        vista_edicion.btn_historial.clicked.connect(lambda: self.mostrar_historial_alumno(alumno_id))

        # 4. Mostrar el diálogo y esperar a que se cierre
        if vista_edicion.exec() == QDialog.Accepted:
            # 5. Si el usuario hizo clic en "Guardar", obtener y guardar los datos
            datos_actualizados = vista_edicion.obtener_datos()
        
            # Lógica para resolver id_clasefk si no está presente
            if 'id_programa' in datos_actualizados and ('id_clasefk' not in datos_actualizados or not datos_actualizados.get('id_clasefk')):
                try:
                    id_prog = datos_actualizados.get('id_programa')
                    if id_prog:
                        id_clase = self.modelo.obtener_primera_clase_para_programa(id_prog)
                        datos_actualizados['id_clasefk'] = id_clase
                except Exception:
                    pass
        
            # 6. Actualizar el modelo y la vista principal
            try:
                self.modelo.actualizar_alumno(alumno_id, datos_actualizados)
                self.cargar_alumnos()
                QMessageBox.information(self.vista, "Éxito", "Alumno actualizado correctamente.")
                self.alumno_actualizado.emit()
            except Exception as e:
                QMessageBox.critical(self.vista, "Error al actualizar", f"No se pudo actualizar el alumno en la base de datos.\n\nError: {e}")
            
        def obtener_historial_alumno(self, alumno_id):
            """Obtiene el historial de modificaciones para un alumno específico."""
            self.cursor.execute('''
                SELECT FECHA, TIPO_MODIFICACION, DETALLES 
                FROM HISTORIAL_MODIFICACIONES 
                WHERE ID_ALUMNO = ? 
                ORDER BY FECHA DESC
            ''', (alumno_id,))
            return self.cursor.fetchall()  
        
    def otorgar_clase_extra(self, alumno_id):
        """ Otorga una clase extra a la inscripción activa de un alumno. """
        try:
            # Buscar la inscripción activa del alumno
            self.modelo.cursor.execute("""
                SELECT ID_INSCRIPCIÓN FROM INSCRIPCIONES
                WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'
                ORDER BY FECHA_INICIO DESC
                LIMIT 1
            """, (alumno_id,))
            resultado = self.modelo.cursor.fetchone()

            if not resultado:
                QMessageBox.warning(self.vista, "Sin Inscripción Activa",
                                    "No se encontró una inscripción activa para este alumno.")
                return

            id_inscripcion_activa = resultado[0]

            # Confirmar acción
            reply = QMessageBox.question(self.vista, 'Confirmar Clase Extra',
                                         f'¿Está seguro de que desea agregar +1 clase restante a la inscripción actual del alumno ID {alumno_id}?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                if self.modelo.agregar_clase_extra_individual(id_inscripcion_activa):
                    QMessageBox.information(self.vista, "Éxito", "Clase extra agregada correctamente.")
                    self.alumno_actualizado.emit() # Emitir señal para refrescar vistas
                else:
                    QMessageBox.critical(self.vista, "Error", "No se pudo agregar la clase extra en la base de datos.")

        except Exception as e:
            QMessageBox.critical(self.vista, "Error", f"Ocurrió un error al otorgar la clase extra: {e}")

    def otorgar_clase_extra_grupo_multiple(self, lista_ids_clase, motivo="Clase cancelada por instructor"):
        """ Otorga una clase extra a todos los alumnos activos de las clases seleccionadas. """
        if not lista_ids_clase:
            QMessageBox.warning(self.vista, "Sin Selección", "No se seleccionaron clases.")
            return

        num_clases = len(lista_ids_clase)
        mensaje_confirmacion = f"¿Está seguro de que desea agregar +1 clase restante a TODOS los alumnos activos en las {num_clases} clases seleccionadas?"

        reply = QMessageBox.question(self.vista, 'Confirmar Clase Extra Grupal',
                                     mensaje_confirmacion,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            exitos = 0
            fallos = 0
            ids_fallidos = []

            try:
                for id_clase in lista_ids_clase:
                    if self.modelo.agregar_clase_extra_grupo(id_clase, motivo):
                        exitos += 1
                    else:
                        fallos += 1
                        ids_fallidos.append(str(id_clase)) # Guardar como string para el mensaje

                mensaje_resultado = f"Proceso completado.\n\nClases procesadas exitosamente: {exitos}"
                if fallos > 0:
                    mensaje_resultado += f"\nClases con errores: {fallos} (IDs: {', '.join(ids_fallidos)})"
                    QMessageBox.warning(self.vista, "Resultado Parcial", mensaje_resultado)
                else:
                    QMessageBox.information(self.vista, "Éxito", mensaje_resultado)

                # Emitir señal UNA VEZ después de procesar todo
                if exitos > 0:
                    self.alumno_actualizado.emit()

            except Exception as e:
                QMessageBox.critical(self.vista, "Error Crítico", f"Ocurrió un error durante el proceso grupal: {e}")   
