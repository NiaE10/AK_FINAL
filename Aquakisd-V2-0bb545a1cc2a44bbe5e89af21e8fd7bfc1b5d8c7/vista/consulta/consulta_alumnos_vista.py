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
        self.controlador = None
        self.es_modo_solicitudes = False # Bandera para saber qué columnas mostrar
        
        self.setWindowTitle('Consulta de Alumnos')
        self.resize(1100, 680)
        self.setMinimumSize(800, 500)

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
        central_layout.setSpacing(12)

        filtro_panel = self._create_filters_panel()
        central_layout.addWidget(filtro_panel)

        self.table = self._create_table()
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
        form_layout.setSpacing(10)

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
        self.btn_editar_alumno.setCursor(Qt.PointingHandCursor)
        form_layout.addRow(self.btn_editar_alumno)
        
        self.btn_clase_extra = QPushButton("Clase Extra (+1)")
        self.btn_clase_extra.setObjectName("btn_clase_extra")
        self.btn_clase_extra.setCursor(Qt.PointingHandCursor)
        form_layout.addRow(self.btn_clase_extra)
        
        self.btn_clase_extra.clicked.connect(self._on_clic_clase_extra)
        self.btn_editar_alumno.clicked.connect(self.on_clic_editar_alumno)

        panel.setLayout(form_layout)

        self.input_busqueda.textChanged.connect(self._on_apply_filters)
        self.combo_programas.currentIndexChanged.connect(self._on_apply_filters)
        self.combo_clases.currentIndexChanged.connect(self._on_apply_filters)
        self.combo_estado.currentIndexChanged.connect(self._on_apply_filters)
        self.spin_edad.valueChanged.connect(self._on_apply_filters)
        self.combo_programas.currentIndexChanged.connect(self._actualizar_clases_segun_programa)

        return panel

    def _create_table(self):
        # MODO NORMAL (Por defecto): ID, Nombre, Edad, Tel1, Tel2, FECHA NAC, Programa, Obs, Estado
        table = QTableWidget(0, 9)
        headers = [
            'ID', 'Nombre Completo', 'Edad', 'Teléfono', 'Teléfono 2',
            'Fecha Nac.', 'Programa', 'Observaciones', 'Estado'
        ]
        table.setHorizontalHeaderLabels(headers)
        table.setColumnHidden(0, True) # Ocultar ID

        table.setWordWrap(True)
        table.setTextElideMode(Qt.ElideNone)
        table.verticalHeader().setDefaultSectionSize(45) 
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        header = table.horizontalHeader()
        # Configuración por defecto (Modo Normal)
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Nombre
        header.setSectionResizeMode(6, QHeaderView.Stretch) # Programa
        header.setSectionResizeMode(7, QHeaderView.Stretch) # Obs
        
        for col in [2, 3, 4, 5, 8]:
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        header.setMinimumSectionSize(80)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setFocusPolicy(Qt.NoFocus)
        table.setAlternatingRowColors(True)

        return table

    def activar_modo_solicitudes(self):
        """
        Activa el modo especial para la pantalla de Solicitudes:
        - Oculta el botón 'Clase Extra'.
        - Cambia las columnas para mostrar HORARIO en lugar de Fecha Nac.
        """
        self.es_modo_solicitudes = True
        
        # 1. Reconfigurar Cabeceras
        headers = [
            'ID', 'Nombre Completo', 'Edad', 'Teléfono 1', 'Teléfono 2',
            'Programa', 'Horario', 'Observaciones', 'Estado'
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setColumnHidden(0, True) # Ocultar ID
        
        # 2. Reajustar anchos de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Nombre
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Programa
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Horario
        header.setSectionResizeMode(7, QHeaderView.Stretch) # Observaciones
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents) # Estado
        
        # 3. Ocultar botón innecesario
        self.btn_clase_extra.setVisible(False)

    def agregar_fila(self, alumno):
        # Datos desde DB (según manejador_db actualizado):
        # 0:ID, 1:Nombre, 2:Apellido, 3:Edad, 4:Tel, 5:Tel2, 6:FechaNac, 
        # 7:Programa, 8:HORARIO, 9:Obs, 10:Estado
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        nombre_completo = f"{alumno[1]} {alumno[2]}".strip()
        
        # Formateo de Edad
        edad_val = alumno[3]
        try:
            edad_en_meses = int(edad_val)
            anyos = edad_en_meses // 12
            meses = edad_en_meses % 12
            edad_str = f"{anyos}a {meses}m" # Formato corto
        except:
            edad_str = str(edad_val)

        # SELECCIÓN DE DATOS SEGÚN EL MODO
        if self.es_modo_solicitudes:
            # MODO SOLICITUDES: Usamos Horario (index 8)
            datos_fila = [
                alumno[0],       # 0. ID
                nombre_completo, # 1. Nombre
                edad_str,        # 2. Edad
                alumno[4],       # 3. Tel 1
                alumno[5],       # 4. Tel 2
                alumno[7],       # 5. Programa (index 7 en DB)
                alumno[8],       # 6. Horario (index 8 en DB - NUEVO)
                alumno[9],       # 7. Obs
                alumno[10]       # 8. Estado
            ]
        else:
            # MODO NORMAL: Usamos Fecha Nac (index 6)
            datos_fila = [
                alumno[0],       # 0. ID
                nombre_completo, # 1. Nombre
                edad_str,        # 2. Edad
                alumno[4],       # 3. Tel 1
                alumno[5],       # 4. Tel 2
                alumno[6],       # 5. Fecha Nac
                alumno[7],       # 6. Programa
                alumno[9],       # 7. Obs
                alumno[10]       # 8. Estado
            ]

        for col, val in enumerate(datos_fila):
            item = QTableWidgetItem(str(val) if val is not None else "")
            
            # Alineación: Textos largos a la izquierda, el resto centrado
            if col not in [1, 5, 6, 7]: 
                item.setTextAlignment(Qt.AlignCenter)
            
            # Bloqueo de edición (excepto Estado)
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if col == 8: # La columna estado siempre es la última visible (índice 8)
                flags |= Qt.ItemIsEditable
                
            item.setFlags(flags)
            self.table.setItem(row, col, item)

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

    def _on_clic_clase_extra(self):
        row = self.table.currentRow()
        if row >= 0:
            id_alumno = self.table.item(row, 0).text()
            if self.controlador:
                self.controlador.otorgar_clase_extra(id_alumno)
        else:
            QMessageBox.information(self, "Aviso", "Selecciona un alumno primero.")

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
            # CAMBIO CLAVE: Limpiamos el nombre para que quepa en el filtro
            nombre_corto = nombre.upper().replace("PROGRAMA ", "").replace("PROGRAMA", "").strip()
            # Si por alguna razón queda vacío (el nombre era solo PROGRAMA), usamos el original
            if not nombre_corto:
                nombre_corto = nombre
            self.combo_programas.addItem(nombre_corto, id_prog)

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

    def mostrar_mensaje(self, texto):
        try:
            QMessageBox.information(self, 'Información', str(texto))
        except Exception:
            pass

    @Slot(QTableWidgetItem)
    def on_item_changed(self, item: QTableWidgetItem):
        # La columna estado es la 8 tanto en modo normal como solicitudes
        if item.column() == 8: 
            row = item.row()
            try:
                alumno_id = int(self.table.item(row, 0).text())
                nuevo_valor = item.text()
                estados_validos = [x[1] for x in self.STATE_OPTIONS if x[1] is not None]
                if nuevo_valor in estados_validos:
                    self.estado_alumno_actualizado.emit(alumno_id, nuevo_valor)
            except (ValueError, TypeError, AttributeError):
                pass