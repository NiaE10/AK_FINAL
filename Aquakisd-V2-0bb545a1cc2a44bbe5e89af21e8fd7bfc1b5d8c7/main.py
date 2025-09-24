import sys
import os
import inspect

DB_FILE = 'aquakids.db'
if not os.path.exists(DB_FILE):
    print(f"Base de datos no encontrada. Creando y poblando {DB_FILE}...")
    import crear_db
    from rellenar_db import rellenar_todos_los_datos
    rellenar_todos_los_datos()
    print("Base de datos creada y poblada.")

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel

app = QApplication.instance() or QApplication(sys.argv)

try:
    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'estilos.qss')
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
except FileNotFoundError:
    print("ADVERTENCIA: No se encontró el archivo de estilos global 'estilos.qss'")

from vista.registrar_ninos.registrar_nino_vista import RegistrarNinoVista
from vista.registrar_maestro.registrar_maestro_vista import RegistrarMaestroVista
from vista.consulta.consulta_alumnos_vista import ConsultaAlumnosVista
from vista.solicitudes.solicitudes_vista import SolicitudesVista
from vista.inicio.inicio_vista import InicioVista
from controlador.controlador_registro import ControladorRegistro
from controlador.controlador_maestros import ControladorMaestros
from controlador.controlador_alumnos import ControladorAlumnos
from controlador.controlador_solicitudes import ControladorSolicitudes
from controlador.controlador_inicio import ControladorInicio
from modelo.manejador_db import ManejadorDB
from vista.programas.programas_vista import ProgramasVista

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AquaKids")
        self.modelo = ManejadorDB()

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        nav_bar = QWidget()
        nav_bar.setObjectName('nav_bar')
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(12, 6, 12, 6)
        nav_layout.setSpacing(8)

        logo = QLabel('AquaKids')
        logo.setObjectName('logo')
        nav_layout.addWidget(logo)
        nav_layout.addStretch()

        self.links = {
            "inicio": QPushButton('Inicio'),
            "instructores": QPushButton('Instructores'),
            "alumnos": QPushButton('Alumnos'),
            "programas": QPushButton('Programas'),
            "registro": QPushButton('Registro'),
            "solicitudes": QPushButton('Solicitudes')
        }

        link_order = ["inicio", "instructores", "alumnos", "programas", "registro", "solicitudes"]
        for i, key in enumerate(link_order):
            button = self.links[key]
            button.setFlat(True)
            if i < len(link_order) - 1:
                button.setProperty("class", "separator")
            nav_layout.addWidget(button)

        container_layout.addWidget(nav_bar)

        self.stacked = QStackedWidget()

        # Vistas y Controladores
        self.vistas = {
            "inicio": InicioVista(),
            "registro": RegistrarNinoVista(),
            "instructores": RegistrarMaestroVista(),
            "alumnos": ConsultaAlumnosVista(),
            "solicitudes": SolicitudesVista(),
            "programas": ProgramasVista(self.modelo),
        }

        self.controlador_inicio = ControladorInicio(self.vistas["inicio"], self.modelo)
        self.controlador_nino = ControladorRegistro(self.vistas["registro"], self.modelo)
        self.controlador_maestros = ControladorMaestros(self.vistas["instructores"], self.modelo)
        self.controlador_alumnos = ControladorAlumnos(self.vistas["alumnos"], self.modelo)
        self.controlador_solicitudes = ControladorSolicitudes(self.vistas["solicitudes"], self.modelo)
        
        self.controlador_solicitudes.set_controlador_alumnos(self.controlador_alumnos)
        self.controlador_alumnos.alumno_actualizado.connect(self.controlador_solicitudes.cargar_solicitudes)
        self.controlador_inicio.alumno_dado_de_baja.connect(self.controlador_alumnos.cargar_alumnos)
        self.controlador_nino.alumno_registrado.connect(self.controlador_alumnos.cargar_alumnos)


        self.stacked.addWidget(self.vistas["inicio"])
        self.stacked.addWidget(self.vistas["registro"])
        self.stacked.addWidget(self.vistas["instructores"])
        self.stacked.addWidget(self.vistas["alumnos"])
        self.stacked.addWidget(self.vistas["solicitudes"])
        self.stacked.addWidget(self.vistas["programas"])
        
        container_layout.addWidget(self.stacked)
        self.setCentralWidget(container)

        # Conexiones de navegación
        self.links["inicio"].clicked.connect(lambda: self._show_view(0, "inicio"))
        self.links["instructores"].clicked.connect(lambda: self._show_view(2, "instructores"))
        self.links["alumnos"].clicked.connect(lambda: self._show_view(3, "alumnos"))
        self.links["programas"].clicked.connect(lambda: self._show_view(5, "programas"))
        self.links["registro"].clicked.connect(lambda: self._show_view(1, "registro"))
        self.links["solicitudes"].clicked.connect(lambda: self._show_view(4, "solicitudes"))
        
        self._show_view(0, "inicio") # Mostrar vista inicial

    def _show_view(self, index, key):
        self.stacked.setCurrentIndex(index)
        for link_key, button in self.links.items():
            button.setProperty("current", "true" if link_key == key else "false")
            # Re-aplicar el estilo para que la propiedad sea evaluada
            button.style().polish(button)

        if index == 0:
            self.controlador_inicio.cargar_alertas()
        elif index == 4:
            self.controlador_solicitudes.cargar_solicitudes()


if __name__ == "__main__":
    window = MainWindow()
    window.show()
    sys.exit(app.exec())