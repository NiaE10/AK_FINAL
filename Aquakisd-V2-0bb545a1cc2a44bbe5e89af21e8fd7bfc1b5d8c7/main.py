import sys
import os
import inspect
import re
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel

def cargar_estilos_globales(app):
    """
    Carga y combina 'tema_global.qss' y 'solicitudes_style.qss'.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Definir rutas explícitas
    estilo_global_path = os.path.join(base_dir, 'vista', 'estilos', 'tema_global.qss')
    estilo_solicitudes_path = os.path.join(base_dir, 'vista', 'solicitudes', 'solicitudes_style.qss')
    
    estilos_combinados = ""

    # 2. Leer Estilo Global
    if os.path.exists(estilo_global_path):
        try:
            with open(estilo_global_path, "r", encoding="utf-8") as f:
                estilos_combinados += f.read()
            print(f"✅ [OK] Tema global cargado: {estilo_global_path}")
        except Exception as e:
            print(f"❌ [ERROR] Falló carga de tema global: {e}")
    else:
        print(f"⚠️ [AVISO] No existe el archivo global en: {estilo_global_path}")

    # 3. Leer Estilo Solicitudes (Concatenar)
    if os.path.exists(estilo_solicitudes_path):
        try:
            with open(estilo_solicitudes_path, "r", encoding="utf-8") as f:
                # Se añade un salto de línea para separar del anterior
                estilos_combinados += "\n" + f.read()
            print(f"✅ [OK] Estilos de solicitudes inyectados: {estilo_solicitudes_path}")
        except Exception as e:
            print(f"❌ [ERROR] Falló carga de estilos solicitudes: {e}")
    else:
        print(f"⚠️ [AVISO] No existe el archivo de solicitudes en: {estilo_solicitudes_path}")
    
    # 4. Aplicar a la aplicación
    if estilos_combinados:
        app.setStyleSheet(estilos_combinados)
        print("🎨 Estilos aplicados a la aplicación.")
    else:
        print("⚠️ ADVERTENCIA: No se aplicó ningún estilo (cadena vacía).")
        # Fallback opcional al antiguo estilos.qss si existe
        old_path = os.path.join(base_dir, 'estilos.qss')
        if os.path.exists(old_path):
             print("Cargando estilo de respaldo antiguo...")
             with open(old_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
                
DB_FILE = 'aquakids.db'
# --- CORRECCIÓN DE RUTA DE BASE DE DATOS ---
if getattr(sys, 'frozen', False):
    # Si es .exe, buscar en la misma carpeta del ejecutable
    base_dir = os.path.dirname(sys.executable)
else:
    # Si es código normal, buscar en la carpeta del script
    base_dir = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(base_dir, 'aquakids.db')

if not os.path.exists(DB_FILE):
    print(f"Base de datos no encontrada en: {DB_FILE}. Creando...")
    # (Nota: crear_db creará el archivo en el directorio de trabajo actual,
    # asegúrate de que tu script crear_db use también rutas absolutas si es posible,
    # pero para la detección esto ya soluciona el problema de reinicio).
    import crear_db
    from rellenar_db import rellenar_todos_los_datos
    rellenar_todos_los_datos()
    print("Base de datos creada y poblada.")


app = QApplication.instance() or QApplication(sys.argv)

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
        cargar_estilos_globales(app)
        # --- CÓDIGO NUEVO PARA EL ICONO (ARRIBA A LA IZQUIERDA) ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_icono = os.path.join(base_dir, 'recursos', 'logo.png') # Asegúrate que sea el nombre exacto de tu imagen
        
        if os.path.exists(ruta_icono):
            # Esto pone el logo en la barra de título y en la barra de tareas
            self.setWindowIcon(QIcon(ruta_icono))
        
        self.modelo = ManejadorDB(db_path=DB_FILE)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        nav_bar = QWidget()
        nav_bar.setObjectName('nav_bar')
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(12, 6, 12, 6)
        nav_layout.setSpacing(8)

        # --- BLOQUE LOGO + TÍTULO (MEJORADO) ---
        
        # 1. Contenedor para Logo y Texto (para mantenerlos juntos a la izquierda)
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10) # Espacio entre el icono y el texto

        # 2. El Logo (Imagen)
        logo_label = QLabel()
        logo_label.setObjectName('logo_img')
        
        # Ruta al archivo (Asegúrate de usar el que es SIN FONDO)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_logo = os.path.join(base_dir, 'recursos', 'logo.png') 
        
        if os.path.exists(ruta_logo):
            pixmap = QPixmap(ruta_logo)
            # Aumentamos un poco el tamaño a 45 o 50 para que luzca más
            pixmap_redim = pixmap.scaledToHeight(45, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap_redim)
        else:
            logo_label.setText("") # Si no hay logo, no mostramos nada en este label

        # 3. El Título (Texto)
        title_label = QLabel("")
        title_label.setObjectName('logo_text') # Usaremos este ID para darle estilo en CSS
        # Estilo directo para asegurar que se vea bien (o muévelo al QSS)
        title_label.setStyleSheet("""
            color: white;
            font-size: 22px;
            font-weight: 900;
            font-family: "Segoe UI", sans-serif;
            letter-spacing: 1px;
        """)

        # 4. Añadimos ambos al layout de marca
        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(title_label)

        # 5. Añadimos el widget de marca a la barra de navegación
        nav_layout.addWidget(brand_widget)
        
        # ---------------------------------------
        
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
        self.controlador_alumnos.alumno_actualizado.connect(self.vistas["programas"].actualizar_vista_actual)
        self.controlador_maestros.maestro_actualizado.connect(self.vistas["programas"].actualizar_vista_actual)
        self.controlador_solicitudes.set_controlador_alumnos(self.controlador_alumnos)
        self.controlador_alumnos.alumno_actualizado.connect(self.controlador_solicitudes.cargar_solicitudes)
        self.controlador_nino.alumno_registrado.connect(self.vistas["programas"].actualizar_vista_actual)
        self.controlador_alumnos.alumno_actualizado.connect(self.controlador_nino.refrescar_cupos)
        self.controlador_inicio.alumno_dado_de_baja.connect(self.controlador_alumnos.cargar_alumnos)
        self.controlador_inicio.alumno_reinscrito.connect(self.controlador_alumnos.cargar_alumnos)
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