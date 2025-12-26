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