from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QComboBox,
    QDateEdit, QRadioButton, QButtonGroup, QPushButton, QTextEdit, QMessageBox,
    QGridLayout, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QDate

class RegistrarNinoVista(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controlador = None
        self.setObjectName("registrar_nino_view")
        self.setWindowTitle("Aqua Kids - Registrar Alumno")
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("top_bar")
        top_bar.setFixedHeight(80)
        main_layout.addWidget(top_bar)

        central_widget = self._create_central_widget()
        main_layout.addWidget(central_widget, 1)

        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottom_bar")
        bottom_bar.setFixedHeight(80)
        main_layout.addWidget(bottom_bar)

    def _create_central_widget(self):
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(40, 30, 40, 30)
        central_layout.setSpacing(25)

        title = QLabel("REGISTRAR NIÑO")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)
        central_layout.addWidget(title)

        # Usar QHBoxLayout para las dos columnas de grupos
        form_columns_layout = QHBoxLayout()

        # --- Columna Izquierda ---
        col_1_group = QGroupBox("Datos del Alumno")
        col_1_layout = QFormLayout(col_1_group)
        self.input_nombre = QLineEdit()
        self.fecha_nacimiento = QDateEdit(calendarPopup=True)
        self.input_celular = QLineEdit()
        self.input_celular2 = QLineEdit()
        col_1_layout.addRow("Nombre completo:", self.input_nombre)
        col_1_layout.addRow("Fecha de nacimiento:", self.fecha_nacimiento)
        col_1_layout.addRow("Celular:", self.input_celular)
        col_1_layout.addRow("Celular 2:", self.input_celular2)
        form_columns_layout.addWidget(col_1_group)

        # --- Columna Derecha ---
        col_2_group = QGroupBox("Detalles de Inscripción")
        col_2_layout = QFormLayout(col_2_group)
        self.programa_combo = QComboBox()
        self.dias_combo = QComboBox()
        self.horario_combo = QComboBox()
        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(["Principiante 1", "Principiante 2", "Intermedio", "Avanzado", "Sin nivel"])
        self.fecha_inicio = QDateEdit(calendarPopup=True)
        estado_widget = self._create_estado_widget()
        col_2_layout.addRow("Programa:", self.programa_combo)
        col_2_layout.addRow("Días:", self.dias_combo)
        col_2_layout.addRow("Horario:", self.horario_combo)
        col_2_layout.addRow("Nivel:", self.nivel_combo)
        col_2_layout.addRow("Fecha de inicio:", self.fecha_inicio)
        col_2_layout.addRow("Estado:", estado_widget)
        form_columns_layout.addWidget(col_2_group)

        central_layout.addLayout(form_columns_layout)

        # --- Fila Inferior para Observaciones y Otros Datos ---
        obs_group = QGroupBox("Información Adicional")
        obs_layout = QFormLayout(obs_group)
        self.input_obs = QTextEdit()
        self.input_obs.setFixedHeight(60)
        self.input_discapacidad = QLineEdit()
        self.input_neurodiversidad = QLineEdit()
        obs_layout.addRow("Observaciones:", self.input_obs)
        obs_layout.addRow("¿Discapacidad?:", self.input_discapacidad)
        obs_layout.addRow("¿Neurodiversidad?:", self.input_neurodiversidad)
        central_layout.addWidget(obs_group)

        self.guardar_btn = QPushButton("Guardar")
        self.guardar_btn.setObjectName("guardar_btn")
        central_layout.addWidget(self.guardar_btn, 0, Qt.AlignCenter)

        for date_edit in [self.fecha_nacimiento, self.fecha_inicio]:
            date_edit.setDate(QDate.currentDate())
            date_edit.setDisplayFormat("dd/MM/yyyy")

        return central_widget
    
    def _create_estado_widget(self):
        estado_widget = QWidget()
        estado_layout = QHBoxLayout(estado_widget)
        estado_layout.setContentsMargins(0,0,0,0)
        self.radio_activo = QRadioButton("Activo")
        self.radio_espera = QRadioButton("Lista De Espera")
        self.radio_prioridad = QRadioButton("Prioridad")
        self.radio_activo.setChecked(True)
        self.estado_group = QButtonGroup()
        self.estado_group.addButton(self.radio_activo)
        self.estado_group.addButton(self.radio_espera)
        self.estado_group.addButton(self.radio_prioridad)
        estado_layout.addWidget(self.radio_activo)
        estado_layout.addWidget(self.radio_espera)
        estado_layout.addWidget(self.radio_prioridad)
        estado_layout.addStretch()
        return estado_widget

    def obtener_datos_formulario(self):
        nombre_completo = self.input_nombre.text().strip()
        partes = nombre_completo.split(' ', 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ''

        fecha_nacimiento_qdate = self.fecha_nacimiento.date()
        hoy = QDate.currentDate()
        edad_en_meses = (hoy.year() - fecha_nacimiento_qdate.year()) * 12 + hoy.month() - fecha_nacimiento_qdate.month()
        if hoy.day() < fecha_nacimiento_qdate.day():
            edad_en_meses -= 1

        estado = ""
        if self.radio_activo.isChecked(): estado = 'Activo'
        elif self.radio_espera.isChecked(): estado = 'Lista De Espera'
        elif self.radio_prioridad.isChecked(): estado = 'Prioridad'

        return {
            'nombre': nombre,
            'apellido': apellido,
            'edad': edad_en_meses,
            'telefono': self.input_celular.text().strip(),
            'telefono2': self.input_celular2.text().strip(),
            'fecha_nacimiento': fecha_nacimiento_qdate.toString('yyyy-MM-dd'),
            'observaciones': self.input_obs.toPlainText().strip(),
            'estado': estado,
            'id_programa': self.programa_combo.currentData(),
            'nivel': self.nivel_combo.currentText(),
            'id_clase': self.horario_combo.currentData(),
            'fecha_inicio': self.fecha_inicio.date().toString('yyyy-MM-dd')
        }

    def mostrar_mensaje(self, texto, tipo='informacion'):
        if tipo == 'error':
            QMessageBox.critical(self, "Error", texto)
        else:
            QMessageBox.information(self, "Información", texto)

    def limpiar_formulario(self):
        self.input_nombre.clear()
        self.input_celular.clear()
        self.input_celular2.clear()
        self.input_discapacidad.clear()
        self.input_neurodiversidad.clear()
        self.input_obs.clear()
        self.fecha_nacimiento.setDate(QDate.currentDate())
        self.fecha_inicio.setDate(QDate.currentDate())
        self.programa_combo.setCurrentIndex(0)
        self.nivel_combo.setCurrentIndex(0)
        self.radio_activo.setChecked(True)