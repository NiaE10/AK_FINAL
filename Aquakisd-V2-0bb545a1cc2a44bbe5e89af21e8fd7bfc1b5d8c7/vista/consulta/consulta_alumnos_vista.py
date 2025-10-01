import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QLineEdit, QSpinBox, QPushButton, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot

class ConsultaAlumnosVista(QWidget):
    FILTER_PANEL_WIDTH = 220
    STATE_OPTIONS = [
        ("Todos", None),
        ("Activo", "Activo"),
        ("Inactivo", "Inactivo"),
        ("Lista De Espera", "Lista De Espera"),
        ("Prioridad", "Prioridad"),
    ]

    estado_alumno_actualizado = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('consulta_main')
        
        self.programas = []
        self.clases = []
        self.columnas_editables = {}

        self.controlador = None
        self.setWindowTitle('Consulta de Alumnos')
        self.resize(1100, 680)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top = QWidget(self)
        top.setObjectName('top_stripe')
        top.setFixedHeight(56)
        main_layout.addWidget(top)

        central = QWidget(self)
        central.setObjectName('central_area')
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(16, 16, 16, 16)
        central_layout.setSpacing(8)

        filtro_panel = self._create_filters_panel()
        central_layout.addWidget(filtro_panel)

        self.table = QTableWidget(0, 12, central)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Nombre', 'Apellido', 'Edad', 'Teléfono', 'Teléfono 2',
            'Fecha de Nacimiento', 'Programa', 'Observaciones', 'Estado',
            'Inicio Curso', 'Fin Curso'
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeToContents)

        
        try:
            self.table.setColumnWidth(1, 140)
            self.table.setColumnWidth(2, 120)
            self.table.setColumnWidth(7, 220)
        except Exception:
            pass
            
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        central_layout.addWidget(self.table)
        main_layout.addWidget(central, 1)

        bottom = QWidget(self)
        bottom.setObjectName('bottom_stripe')
        bottom.setFixedHeight(28)
        main_layout.addWidget(bottom)

        self.table.itemChanged.connect(self.on_item_changed)


    def _create_filters_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setObjectName("filters_panel")
        panel.setFixedWidth(self.FILTER_PANEL_WIDTH)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(8)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Nombre, apellido o teléfono")
        form_layout.addRow(QLabel("Buscar:"), self.input_busqueda)

        self.combo_programas = QComboBox()
        form_layout.addRow(QLabel("Programa:"), self.combo_programas)

        self.combo_clases = QComboBox()
        form_layout.addRow(QLabel("Clase:"), self.combo_clases)

        self.combo_estado = QComboBox()
        for text, data in self.STATE_OPTIONS:
            self.combo_estado.addItem(text, data)
        form_layout.addRow(QLabel("Estado:"), self.combo_estado)

        self.spin_edad = QSpinBox()
        self.spin_edad.setRange(0, 18)
        form_layout.addRow(QLabel("Edad (años):"), self.spin_edad)

        self.combo_programas.addItem("Todos", None)
        self.combo_clases.addItem("Todas", None)

        self.btn_editar_alumno = QPushButton("Editar Alumno")
        self.btn_editar_alumno.setObjectName("btn_editar_alumno")
        form_layout.addRow(self.btn_editar_alumno)

        panel.setLayout(form_layout)

        self.input_busqueda.textChanged.connect(self._on_apply_filters)
        self.combo_programas.currentIndexChanged.connect(self._on_apply_filters)
        self.combo_clases.currentIndexChanged.connect(self._on_apply_filters)
        self.combo_estado.currentIndexChanged.connect(self._on_apply_filters)
        self.spin_edad.valueChanged.connect(self._on_apply_filters)
        self.combo_programas.currentIndexChanged.connect(self._actualizar_clases_segun_programa)

        self.btn_editar_alumno.clicked.connect(self.on_clic_editar_alumno)

        return panel

    def on_clic_editar_alumno(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            alumno_id = self.table.item(selected_row, 0).text()
            try:
                alumno_id = int(alumno_id)
            except Exception:
                pass
            self.controlador.editar_alumno(alumno_id)
        else:
            QMessageBox.information(self, "Seleccionar Alumno", "Por favor, selecciona un alumno de la tabla para editar.")

    def _on_apply_filters(self):
        query = self.input_busqueda.text().strip() or None
        estado = self.combo_estado.currentData()
        id_programa = self.combo_programas.currentData()
        id_clase = self.combo_clases.currentData()
        edad = self.spin_edad.value()

        try:
            self.controlador.buscar_alumnos(
                query=query,
                estado=estado,
                id_programa=id_programa,
                id_clase=id_clase,
                edad=edad if edad > 0 else None
            )
        except Exception:
            try:
                self.controlador.buscar_alumnos()
            except Exception:
                pass

    def set_controlador(self, controlador):
        self.controlador = controlador

    def set_programas(self, programas):
        self.programas = list(programas or [])
        self.combo_programas.clear()
        self.combo_programas.addItem("Todos", None)
        for id_prog, nombre in self.programas:
            self.combo_programas.addItem(nombre, id_prog)

    def set_clases(self, clases):
        self.clases = list(clases or [])
        self.combo_clases.clear()
        self.combo_clases.addItem("Todas", None)
        for item in self.clases:
            if len(item) >= 2:
                id_cl = item[0]
                desc = item[1]
                self.combo_clases.addItem(desc, id_cl)

    def _actualizar_clases_segun_programa(self):
        id_programa_seleccionado = self.combo_programas.currentData()
        self.combo_clases.clear()
        self.combo_clases.addItem("Todas", None)

        if id_programa_seleccionado:
            clases_filtradas = [
                (item[0], item[1]) for item in self.clases if len(item) >= 3 and item[2] == id_programa_seleccionado
            ]
        else:
            clases_filtradas = [(item[0], item[1]) for item in self.clases if len(item) >= 2]

        for id_cl, desc in clases_filtradas:
            self.combo_clases.addItem(desc, id_cl)

    def limpiar_tabla(self):
        self.table.setRowCount(0)

    def agregar_fila(self, alumno):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, val in enumerate(alumno):
            if col == 3:
                try:
                    edad_en_meses = int(val)
                    anyos = edad_en_meses // 12
                    meses = edad_en_meses % 12
                    val = f"{anyos} años, {meses} meses"
                except (ValueError, TypeError):
                    pass
            
            item = QTableWidgetItem('' if val is None else str(val))
            
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if col in self.columnas_editables:
                flags |= Qt.ItemIsEditable
            item.setFlags(flags)

            try:
                item.setTextAlignment(Qt.AlignCenter)
            except Exception:
                pass
            self.table.setItem(row, col, item)

    def mostrar_mensaje(self, texto):
        try:
            QMessageBox.information(self, 'Información', str(texto))
        except Exception:
            pass

    def set_columnas_editables(self, columnas: dict):
        self.columnas_editables = columnas

    @Slot(QTableWidgetItem)
    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() in self.columnas_editables:
            row = item.row()
            col = item.column()
            
            try:
                alumno_id = int(self.table.item(row, 0).text())
                nuevo_valor = item.text()
                
                config = self.columnas_editables[col]
                if config['type'] == 'combo':
                    if nuevo_valor not in config['options']:
                        # Optional: revert or show error if value is not valid
                        return

                if col == 9: # Estado column
                    self.estado_alumno_actualizado.emit(alumno_id, nuevo_valor)

            except (ValueError, TypeError) as e:
                print(f"Error processing item change: {e}")