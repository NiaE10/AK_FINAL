from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QTableWidgetItem, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

COL_NOMBRE = 0
COL_PROGRAMA = 1
COL_CLASES_REST = 2
COL_DIAS = 3
COL_ACCIONES = 4
NUM_COLUMNAS = 5

class InicioVista(QWidget):
    reinscribir_alumno = Signal(int)
    editar_alumno = Signal(int)
    baja_alumno = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('inicio_vista')
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        central_widget = self._create_central_widget()
        layout.addWidget(central_widget)
        
        self.setLayout(layout)
        # Estado inicial
        self.table.setVisible(False)
        self.placeholder.setVisible(True)

    def _create_central_widget(self):
        central = QWidget()
        central.setObjectName('inicio_central')
        central_layout = QVBoxLayout(central)
        
        # RESPONSIVIDAD: Márgenes equilibrados (20px es estándar y limpio)
        central_layout.setContentsMargins(20, 20, 20, 20)
        central_layout.setSpacing(15)
        
        self.table = self._create_table()
        central_layout.addWidget(self.table)
        
        self.placeholder = self._create_placeholder()
        central_layout.addWidget(self.placeholder)
        
        return central

    def _create_table(self):
        table = QTableWidget(0, NUM_COLUMNAS)
        headers = ['Nombre', 'Programa', 'Clases Rest.', 'Días', 'Acciones']
        table.setHorizontalHeaderLabels(headers)
        
        # --- 1. CONFIGURACIÓN VISUAL (Texto ajustado y limpio) ---
        table.setWordWrap(True)
        table.setTextElideMode(Qt.ElideNone)
        table.verticalHeader().setDefaultSectionSize(45) # Altura para que quepa texto en 2 lineas

        # --- 2. NÚMEROS DE FILA (Centrados) ---
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # --- 3. COLUMNAS ELÁSTICAS ---
        hdr = table.horizontalHeader()
        
        # Nombre y Programa ocupan el espacio sobrante
        hdr.setSectionResizeMode(COL_NOMBRE, QHeaderView.Stretch)
        hdr.setSectionResizeMode(COL_PROGRAMA, QHeaderView.Stretch)
        
        # Datos numéricos y cortos se ajustan
        hdr.setSectionResizeMode(COL_CLASES_REST, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_DIAS, QHeaderView.ResizeToContents)
        
        # Acciones: Ancho fijo suficiente para los botones
        hdr.setSectionResizeMode(COL_ACCIONES, QHeaderView.Fixed)
        table.setColumnWidth(COL_ACCIONES, 220)
        
        hdr.setMinimumSectionSize(80)
        
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setFocusPolicy(Qt.NoFocus)
        table.setMinimumHeight(100)
        
        return table

    def _create_placeholder(self):
        placeholder = QLabel('No hay alumnos con inscripciones próximas a vencer.')
        placeholder.setObjectName('placeholder_label')
        placeholder.setAlignment(Qt.AlignCenter)
        # Estilo inline opcional para el texto de "Sin alertas"
        placeholder.setStyleSheet("color: #7f8c8d; font-size: 16px; font-weight: bold;")
        return placeholder

    def mostrar_alertas(self, alertas):
        self.table.setRowCount(0)
        if not alertas:
            self.table.setVisible(False)
            self.placeholder.setVisible(True)
            return
        
        self.table.setVisible(True)
        self.placeholder.setVisible(False)
        
        for row_idx, data_row in enumerate(alertas):
            nombre, apellido, id_alumno, id_inscripcion, programa, clases_restantes, dias_clase = data_row
            
            self.table.insertRow(row_idx)
            # Altura de fila cómoda para touch/mouse (50px)
            self.table.setRowHeight(row_idx, 50)
            
            self.table.setItem(row_idx, COL_NOMBRE, QTableWidgetItem(f"{nombre} {apellido}"))
            self.table.setItem(row_idx, COL_PROGRAMA, QTableWidgetItem(str(programa)))
            
            # Centrar números
            item_rest = QTableWidgetItem(str(clases_restantes))
            item_rest.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, COL_CLASES_REST, item_rest)
            
            self.table.setItem(row_idx, COL_DIAS, QTableWidgetItem(str(dias_clase)))
            
            # Alerta visual (Rojo suave) si quedan pocas clases
            if int(clases_restantes) <= 3:
                for col in range(NUM_COLUMNAS - 1): # Pintamos todo menos los botones
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor("#FFE0E0"))
                        item.setForeground(QColor("#c0392b")) # Texto rojo oscuro para contraste
            
            self._add_action_buttons(row_idx, id_alumno, id_inscripcion)

    def _add_action_buttons(self, row_idx, id_alumno, id_inscripcion):
        acciones_widget = QWidget()
        acciones_layout = QHBoxLayout(acciones_widget)
        acciones_layout.setContentsMargins(5, 5, 5, 5)
        acciones_layout.setSpacing(8) # Espacio entre botones
        acciones_layout.setAlignment(Qt.AlignCenter)

        btn_reinscribir = QPushButton("Reinscribir")
        btn_reinscribir.setObjectName("btn_reinscribir")
        btn_reinscribir.setCursor(Qt.PointingHandCursor) # Cursor de mano
        
        btn_baja = QPushButton("Baja")
        btn_baja.setObjectName("btn_baja")
        btn_baja.setCursor(Qt.PointingHandCursor) # Cursor de mano

        btn_reinscribir.clicked.connect(lambda: self.reinscribir_alumno.emit(id_inscripcion))
        btn_baja.clicked.connect(lambda: self.baja_alumno.emit(id_alumno))
        
        acciones_layout.addWidget(btn_reinscribir)
        acciones_layout.addWidget(btn_baja)
        
        self.table.setCellWidget(row_idx, COL_ACCIONES, acciones_widget)

    def clear(self):
        self.table.setRowCount(0)
        self.table.setVisible(False)
        self.placeholder.setVisible(True)