# vista/editar/editar_alumno_vista.py

import os
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QComboBox, QDateEdit, QLabel, QHBoxLayout, QMessageBox
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
            'fecha_inicio_actividad': ('Fecha Inicio:', self._create_date_edit_inicio()),
            'id_programafk': ('Programa:', self._create_programas_combo(programas)),
            'id_clasefk': ('Clase:', QComboBox()),
            'nivel': ('Nivel:', self._create_nivel_combo())
        }

        for key, (label, widget) in fields_to_create.items():
            self.campos[key] = widget
            self.layout.addRow(QLabel(label), self.campos[key])

        # Conectar el cambio de estado con la función de ocultar/mostrar
        self.campos['estado'].currentTextChanged.connect(self._on_estado_changed)
        
        # Ejecutar una vez al inicio para establecer el estado correcto (oculto/visible)
        self._on_estado_changed(self.campos['estado'].currentText())        # Initialize class and program lists
        self.programas = programas or []
        self.clases = self._normalize_clases(clases)

        # Connect signals
        self.campos['id_programafk'].currentIndexChanged.connect(self._actualizar_clases_segun_programa)

        # Set current program and class
        self._set_initial_program_and_class()

        # Save button
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.clicked.connect(self._validar_y_guardar)
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
        dropdown_style = """
            QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #4095b9;
                selection-color: white;
            }
        """
        calendar = date_edit.calendarWidget()
        if calendar:
            combo_boxes = calendar.findChildren(QComboBox)
            for combo in combo_boxes:
                combo.view().setStyleSheet(dropdown_style)
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

        # --- CORRECCIÓN: REDIRECCIÓN DE VISTA ---
        target_id = id_programa_seleccionado
        if id_programa_seleccionado == 5: target_id = 3
        elif id_programa_seleccionado == 6: target_id = 4
        # ----------------------------------------

        if target_id:
            # Filtramos usando target_id en lugar de id_programa_seleccionado
            clases_filtradas = [
                (id_cl, desc) for id_cl, desc, id_prog_fk in self.clases if id_prog_fk == target_id
            ]
        else:
            clases_filtradas = []

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
            'fecha_inicio_actividad': self.campos['fecha_inicio_actividad'].date().toString('yyyy-MM-dd'),
            'id_clasefk': self.campos['id_clasefk'].currentData(),
            'nivel': self.campos['nivel'].currentData(),
            'id_programafk': self.campos['id_programafk'].currentData(),
        }

    def _create_date_edit_inicio(self):
        """Crea un selector de fecha por defecto con el día de hoy para el inicio de actividades."""
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd/MM/yyyy")
        
        # Estilo consistente con el resto de la app
        dropdown_style = """
            QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #4095b9;
                selection-color: white;
            }
        """
        calendar = date_edit.calendarWidget()
        if calendar:
            combo_boxes = calendar.findChildren(QComboBox)
            for combo in combo_boxes:
                combo.view().setStyleSheet(dropdown_style)
        return date_edit
    
    def _on_estado_changed(self, texto_estado):
        """Muestra u oculta el campo de fecha según el estado seleccionado."""
        es_activo = (texto_estado == "Activo")
        widget_fecha = self.campos.get('fecha_inicio_actividad')
        
        if widget_fecha:
            # setRowVisible oculta tanto la etiqueta como el campo en un FormLayout
            self.layout.setRowVisible(widget_fecha, es_activo)

    def _validar_y_guardar(self):
        """Valida Nivel y Clase antes de cerrar la ventana."""
        
        # 1. Validar Nivel (Obligatorio siempre)
        nivel = self.campos['nivel'].currentData()
        if nivel is None:
            QMessageBox.warning(self, "Falta Información", "Por favor, selecciona un Nivel para el alumno.")
            return  # NO cerramos la ventana
        
        # 2. Validar Clase (Obligatorio SOLO si el estado es 'Activo')
        estado = self.campos['estado'].currentText()
        id_clase = self.campos['id_clasefk'].currentData()
        
        if estado == 'Activo' and id_clase is None:
            QMessageBox.warning(
                self, 
                "Falta Información", 
                "Un alumno 'Activo' debe tener un horario asignado.\n\n"
                "Por favor, selecciona un Programa y una Clase."
            )
            return  # NO cerramos la ventana

        # Si pasó todas las validaciones, ahora sí aceptamos y cerramos
        self.accept()