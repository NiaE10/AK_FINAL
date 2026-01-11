import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from vista.consulta.consulta_alumnos_vista import ConsultaAlumnosVista


class SolicitudesVista(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('solicitudes_vista')
        self.controlador = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Reuse the student query view to leverage its table and filters
        self.alumnos_view = ConsultaAlumnosVista()

        # Customize the status filter for the context of solicitations
        try:
            combo_estado = self.alumnos_view.combo_estado
            combo_estado.clear()
            combo_estado.addItem("Todos", None)
            combo_estado.addItem("Lista De Espera", "Lista De Espera")
            combo_estado.addItem("Prioridad", "Prioridad")
            
            # Verificamos si existe el botón y lo ocultamos
            if hasattr(self.alumnos_view, 'btn_clase_extra'):
                self.alumnos_view.btn_clase_extra.setVisible(False)
            
        except Exception as e:
            print(f"Could not customize status combo box: {e}")
        
        

        layout.addWidget(self.alumnos_view)

    def set_controlador(self, controlador):
        self.controlador = controlador
        # Also assign the same controller to the embedded view if applicable
        if self.alumnos_view:
            self.alumnos_view.set_controlador(controlador)

    def cargar_datos(self, filas):
        # Fill the internal table
        if self.alumnos_view:
            self.alumnos_view.table.blockSignals(True)
            self.alumnos_view.limpiar_tabla()
            for fila in filas:
                self.alumnos_view.agregar_fila(fila)
            self.alumnos_view.table.blockSignals(False)

    def mostrar_mensaje(self, texto):
        QMessageBox.information(self, 'Información', str(texto))
