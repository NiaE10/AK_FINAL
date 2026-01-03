import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QLineEdit, QSpinBox, QPushButton, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot

class ConsultaAlumnosVista(QWidget):
    # Ancho fijo para el panel lateral (estándar en diseño UI)
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
        # RESPONSIVIDAD: Tamaño inicial sugerido, pero permitimos redimensionar
        self.resize(1100, 680)
        self.setMinimumSize(800, 500) # Evitamos que la ventana sea inutilizablemente pequeña

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Franja superior decorativa
        top = QWidget(self)
        top.setObjectName('top_stripe')
        top.setFixedHeight(56)
        main_layout.addWidget(top)

        # Área Central (Contiene Panel Lateral + Tabla)
        central = QWidget(self)
        central.setObjectName('central_area')
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(16, 16, 16, 16)
        central_layout.setSpacing(12) # Un poco más de espacio entre panel y tabla

        # 1. Panel de Filtros
        filtro_panel = self._create_filters_panel()
        central_layout.addWidget(filtro_panel)

        # 2. Tabla de Datos
        self.table = self._create_table()
        central_layout.addWidget(self.table)
        
        main_layout.addWidget(central, 1) # El 1 indica que esta parte se expande

        # Franja inferior decorativa
        bottom = QWidget(self)
        bottom.setObjectName('bottom_stripe')
        bottom.setFixedHeight(28)
        main_layout.addWidget(bottom)

        self.table.itemChanged.connect(self.on_item_changed)

    def _create_filters_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setObjectName("filters_panel")
        # El panel lateral se mantiene fijo para no "bailar" al cambiar tamaño
        panel.setFixedWidth(self.FILTER_PANEL_WIDTH)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(10) # Espaciado vertical más limpio

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

        # --- BOTONES LATERALES ---
        # El estilo ya está definido en el QSS (redondeados y bonitos)
        self.btn_editar_alumno = QPushButton("Editar Alumno")
        self.btn_editar_alumno.setObjectName("btn_editar_alumno")
        self.btn_editar_alumno.setCursor(Qt.PointingHandCursor) # Cursor de mano
        form_layout.addRow(self.btn_editar_alumno)
        
        self.btn_clase_extra = QPushButton("Clase Extra (+1)")
        self.btn_clase_extra.setObjectName("btn_clase_extra")
        self.btn_clase_extra.setCursor(Qt.PointingHandCursor) # Cursor de mano
        form_layout.addRow(self.btn_clase_extra)
        
        self.btn_clase_extra.clicked.connect(self._on_clic_clase_extra)
        self.btn_editar_alumno.clicked.connect(self.on_clic_editar_alumno)

        panel.setLayout(form_layout)

        # Conexiones de filtros
        self.input_busqueda.textChanged.connect(self._on_apply_filters)
        self.combo_programas.currentIndexChanged.connect(self._on_apply_filters)
        self.combo_clases.currentIndexChanged.connect(self._on_apply_filters)
        self.combo_estado.currentIndexChanged.connect(self._on_apply_filters)
        self.spin_edad.valueChanged.connect(self._on_apply_filters)
        self.combo_programas.currentIndexChanged.connect(self._actualizar_clases_segun_programa)

        return panel

    def _create_table(self):
        # AHORA SON 9 COLUMNAS (Fusionamos nombre y apellido)
        table = QTableWidget(0, 9)
        headers = [
            'ID', 'Nombre Completo', 'Edad', 'Teléfono', 'Teléfono 2',
            'Fecha Nac.', 'Programa', 'Observaciones', 'Estado'
        ]
        table.setHorizontalHeaderLabels(headers)
        
        # --- 1. OCULTAR COLUMNA ID (El usuario no la ve, pero el sistema la usa) ---
        table.setColumnHidden(0, True) 

        # --- 2. CONFIGURACIÓN VISUAL ---
        table.setWordWrap(True)
        table.setTextElideMode(Qt.ElideNone)
        table.verticalHeader().setDefaultSectionSize(45) 

        # --- 3. NÚMEROS DE FILA CENTRADOS ---
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # --- 4. COLUMNAS ELÁSTICAS ---
        header = table.horizontalHeader()
        
        # Nombre Completo, Programa y Observaciones se ESTIRAN
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Nombre Completo
        header.setSectionResizeMode(6, QHeaderView.Stretch) # Programa (Ahora es la col 6)
        header.setSectionResizeMode(7, QHeaderView.Stretch) # Observaciones (Ahora es la col 7)

        # El resto se ajusta al contenido
        for col in [0, 2, 3, 4, 5, 8]:
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        header.setMinimumSectionSize(80)

        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setFocusPolicy(Qt.NoFocus)
        table.setAlternatingRowColors(True)

        return table

    def _on_clic_clase_extra(self):
        row = self.table.currentRow()
        if row >= 0:
            id_alumno = self.table.item(row, 0).text()
            if self.controlador:
                self.controlador.otorgar_clase_extra(id_alumno)
        else:
            QMessageBox.information(self, "Aviso", "Selecciona un alumno primero.")

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
        # alumno trae: (id, nombre, apellido, edad, tel, tel2, fecha, prog, obs, estado)
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 1. UNIR NOMBRE Y APELLIDO
        nombre_completo = f"{alumno[1]} {alumno[2]}".strip()
        
        # 2. CALCULAR EDAD (Formato Años, Meses)
        edad_val = alumno[3]
        try:
            edad_en_meses = int(edad_val)
            anyos = edad_en_meses // 12
            meses = edad_en_meses % 12
            edad_str = f"{anyos} años, {meses} meses"
        except:
            edad_str = str(edad_val)

        # 3. CREAR LA LISTA DE DATOS EN EL NUEVO ORDEN (9 columnas)
        datos_fila = [
            alumno[0],       # 0. ID (Oculto)
            nombre_completo, # 1. Nombre Completo (Unido)
            edad_str,        # 2. Edad
            alumno[4],       # 3. Teléfono
            alumno[5],       # 4. Teléfono 2
            alumno[6],       # 5. Fecha Nac
            alumno[7],       # 6. Programa
            alumno[8],       # 7. Observaciones
            alumno[9]        # 8. Estado
        ]

        for col, val in enumerate(datos_fila):
            item = QTableWidgetItem(str(val) if val is not None else "")
            
            # Alineación: Centrar todo MENOS los textos largos
            if col not in [1, 6, 7]: # Nombre, Programa y Obs a la izquierda
                item.setTextAlignment(Qt.AlignCenter)
            
            # Bloqueamos edición directa en la tabla (excepto Estado si quisieras)
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            
            # Si quieres permitir editar el ESTADO desde la tabla directamente:
            if col == 8: 
                flags |= Qt.ItemIsEditable
                
            item.setFlags(flags)
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
        # Como quitamos la columna apellido, Estado pasa de ser la columna 9 a la 8
        if item.column() == 8: 
            row = item.row()
            try:
                # Obtenemos el ID (que está en la columna 0 oculta)
                alumno_id = int(self.table.item(row, 0).text())
                nuevo_valor = item.text()
                
                # Validamos que el estado sea válido antes de enviar
                estados_validos = [x[1] for x in self.STATE_OPTIONS if x[1] is not None]
                if nuevo_valor in estados_validos:
                    self.estado_alumno_actualizado.emit(alumno_id, nuevo_valor)
            except (ValueError, TypeError, AttributeError):
                pass