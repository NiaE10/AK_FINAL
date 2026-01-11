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

        # 1. Crear la vista
        self.alumnos_view = ConsultaAlumnosVista()
        
        # 2. ACTIVAR EL MODO SOLICITUDES
        # Esto cambia las columnas (poniendo Horario en vez de Fecha Nac) y oculta el botón Clase Extra
        self.alumnos_view.activar_modo_solicitudes()

        # 3. Personalizar filtros (agregar estados específicos)
        try:
            combo_estado = self.alumnos_view.combo_estado
            combo_estado.clear()
            combo_estado.addItem("Todos", None)
            combo_estado.addItem("Lista De Espera", "Lista De Espera")
            combo_estado.addItem("Prioridad", "Prioridad")
        except Exception as e:
            print(f"No se pudo personalizar la vista de solicitudes: {e}")
        
        layout.addWidget(self.alumnos_view)

    def set_controlador(self, controlador):
        self.controlador = controlador
        if self.alumnos_view:
            self.alumnos_view.set_controlador(controlador)

    def cargar_datos(self, filas):
        if self.alumnos_view:
            self.alumnos_view.table.blockSignals(True)
            self.alumnos_view.limpiar_tabla()
            for fila in filas:
                self.alumnos_view.agregar_fila(fila)
            self.alumnos_view.table.blockSignals(False)

    def mostrar_mensaje(self, texto):
        QMessageBox.information(self, 'Información', str(texto))