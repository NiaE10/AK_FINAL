from modelo.manejador_db import ManejadorDB
from PySide6.QtWidgets import QMessageBox

class ControladorSolicitudes:
    def __init__(self, vista: object, modelo: ManejadorDB):
        self.vista = vista
        self.modelo = modelo
        self.controlador_alumnos = None
        if hasattr(self.vista, 'set_controlador'):
            self.vista.set_controlador(self)

    def set_controlador_alumnos(self, controlador_alumnos):
        self.controlador_alumnos = controlador_alumnos

    def editar_alumno(self, alumno_id):
        if self.controlador_alumnos:
            self.controlador_alumnos.editar_alumno(alumno_id)
        else:
            QMessageBox.warning(self.vista, "Error", "No se puede editar el alumno en este contexto.")

    def actualizar_estado_solicitud(self, alumno_id: int, nuevo_estado: str):
        """
        Actualiza el estado de una solicitud (alumno) en la base de datos.
        """
        try:
            self.modelo.actualizar_estado_alumno(alumno_id, nuevo_estado)
            self.vista.mostrar_mensaje(f"Estado del alumno {alumno_id} actualizado a {nuevo_estado}.")
            self.cargar_solicitudes()  # Recargar para reflejar el cambio
        except Exception as e:
            print(f"Error al actualizar estado: {e}")
            self.vista.mostrar_mensaje("Error al actualizar el estado de la solicitud.")

    def buscar_alumnos(self, query=None, estado=None, id_programa=None, id_clase=None, edad=None):
        """
        Busca alumnos en la lista de solicitudes con filtros adicionales.
        Filtra por 'Lista De Espera' y 'Prioridad' si no se especifica un estado.
        """
        if estado:
            estados_a_buscar = [estado]
        else:
            estados_a_buscar = ['Lista De Espera', 'Prioridad']
        
        try:
            filas = self.modelo.buscar_alumnos(
                query=query,
                estado=estados_a_buscar,
                id_programa=id_programa,
                id_clase=id_clase,
                edad=edad
            )
            self.vista.cargar_datos(filas)
        except Exception as e:
            print(f"Error al buscar en solicitudes: {e}")
            self.vista.cargar_datos([])

    def cargar_solicitudes(self):
        """
        Carga los alumnos en estado 'Lista De Espera' o 'Prioridad' y los muestra en la vista.
        """
        self.buscar_alumnos()
