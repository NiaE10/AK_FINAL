# vista/editar/editar_alumno_vista.py

import os
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QComboBox, QDateEdit, QLabel, QHBoxLayout
from PySide6.QtCore import QDate


class EditarAlumnoVista(QDialog):
    def __init__(self, datos_alumno=None, programas=None, clases=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Alumno")
        self.setObjectName("editar_alumno_dialog")

        self.datos_alumno = datos_alumno or {}

        self.layout = QFormLayout(self)
        self.layout.setSpacing(10)
        self.campos = {}

        # Define fields to create
        fields_to_create = {
            'nombre': ('Nombre:', QLineEdit(self.datos_alumno.get('NOMBRE', ''))),
            'apellido': ('Apellido:', QLineEdit(self.datos_alumno.get('APELLIDO', ''))),
            'telefono': ('Teléfono:', QLineEdit(self.datos_alumno.get('TELEFONO', ''))),
            'telefono2': ('Teléfono 2:', QLineEdit(self.datos_alumno.get('TELEFONO2', ''))),
            'fecha_de_nacimiento': ('Fecha de Nacimiento:', self._create_date_edit()),
            'observaciones': ('Observaciones:', QLineEdit(self.datos_alumno.get('OBSERVACIONES', ''))),
            'estado': ('Estado:', self._create_estado_combo()),
            'id_programafk': ('Programa:', self._create_programas_combo(programas)),
            'id_clasefk': ('Clase:', QComboBox()),
            'nivel': ('Nivel:', self._create_nivel_combo())
        }

        for key, (label, widget) in fields_to_create.items():
            self.campos[key] = widget
            self.layout.addRow(QLabel(label), self.campos[key])

        # Initialize class and program lists
        self.programas = programas or []
        self.clases = self._normalize_clases(clases)

        # Connect signals
        self.campos['id_programafk'].currentIndexChanged.connect(self._actualizar_clases_segun_programa)

        # Set current program and class
        self._set_initial_program_and_class()

        # Save button
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.clicked.connect(self.accept)
        self.layout.addRow("", self.btn_guardar)
        self.btn_historial = QPushButton("Ver Historial")
        self.btn_historial.setObjectName("btn_historial")
  
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_guardar)
        button_layout.addWidget(self.btn_historial)
        self.layout.addRow("", button_layout)
    def _create_date_edit(self):
        date_edit = QDateEdit()
        fecha_str = self.datos_alumno.get('FECHA_DE_NACIMIENTO', '') or ''
        qdate = QDate.fromString(fecha_str, 'yyyy-MM-dd')
        date_edit.setDate(qdate if qdate.isValid() else QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd/MM/yyyy")
        return date_edit

    def _create_estado_combo(self):
        combo = QComboBox()
        combo.addItems(["Activo", "Inactivo", "Lista De Espera", "Prioridad"])
        current_estado = self.datos_alumno.get('ESTADO')
        if current_estado:
            combo.setCurrentText(current_estado)
        return combo

    def _create_programas_combo(self, programas):
        combo = QComboBox()
        combo.addItem("Selecciona un programa", None)
        for id_prog, nombre in (programas or []):
            combo.addItem(nombre, id_prog)
        return combo

    def _create_nivel_combo(self):
        combo = QComboBox()
        combo.addItem("Selecciona nivel", None)
        for nivel in ["Principiante 1", "Principiante 2", "Intermedio", "Avanzado"]:
            combo.addItem(nivel, nivel)
        nivel_actual = self.datos_alumno.get('NIVEL')
        if nivel_actual:
            combo.setCurrentText(nivel_actual)
        return combo

    def _normalize_clases(self, clases):
        normalized = []
        for entry in (clases or []):
            if len(entry) == 3:
                normalized.append(entry)
            elif len(entry) == 2:
                normalized.append((entry[0], entry[1], None))
        return normalized

    def _set_initial_program_and_class(self):
        id_clase_actual = self.datos_alumno.get('ID_CLASEFK')
        id_programa_actual = self._obtener_id_programa_por_clase(id_clase_actual)
        if id_programa_actual:
            idx = self.campos['id_programafk'].findData(id_programa_actual)
            if idx >= 0:
                self.campos['id_programafk'].setCurrentIndex(idx)
        self._actualizar_clases_segun_programa(id_clase_seleccionada=id_clase_actual)

    def _obtener_id_programa_por_clase(self, id_clase):
        for id_cl, desc, id_prog in self.clases:
            if id_cl == id_clase:
                return id_prog
        return None

    def _actualizar_clases_segun_programa(self, index=None, id_clase_seleccionada=None):
        combo_clases = self.campos['id_clasefk']
        combo_clases.clear()
        combo_clases.addItem("Selecciona una clase", None)

        id_programa_seleccionado = self.campos['id_programafk'].currentData()

        if id_programa_seleccionado:
            clases_filtradas = [
                (id_cl, desc) for id_cl, desc, id_prog_fk in self.clases if id_prog_fk == id_programa_seleccionado
            ]
        else:
            clases_filtradas = [(item[0], item[1]) for item in self.clases]

        for id_cl, desc in clases_filtradas:
            combo_clases.addItem(desc, id_cl)
        
        if id_clase_seleccionada:
            idx = combo_clases.findData(id_clase_seleccionada)
            if idx >= 0:
                combo_clases.setCurrentIndex(idx)

    def obtener_datos(self):
        qdate = self.campos['fecha_de_nacimiento'].date()
        hoy = QDate.currentDate()
        edad_en_meses = (hoy.year() - qdate.year()) * 12 + hoy.month() - qdate.month()
        if hoy.day() < qdate.day():
            edad_en_meses -= 1

        return {
            'nombre': self.campos['nombre'].text(),
            'apellido': self.campos['apellido'].text(),
            'edad': edad_en_meses,
            'telefono': self.campos['telefono'].text(),
            'telefono2': self.campos['telefono2'].text(),
            'fecha_de_nacimiento': qdate.toString('yyyy-MM-dd'),
            'observaciones': self.campos['observaciones'].text(),
            'estado': self.campos['estado'].currentText(),
            'id_clasefk': self.campos['id_clasefk'].currentData(),
            'nivel': self.campos['nivel'].currentData(),
        }
