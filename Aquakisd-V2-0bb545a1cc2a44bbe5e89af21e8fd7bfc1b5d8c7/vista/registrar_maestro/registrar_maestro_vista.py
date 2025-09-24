import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QComboBox, QLabel
)
from PySide6.QtCore import Qt


class RegistrarMaestroVista(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controlador = None
        self.setObjectName("registrar_maestro_view")
        self.setWindowTitle("Aqua Kids - Instructores")
        self.resize(1100, 600)
        self._build_ui()



    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        central = QWidget()
        central.setObjectName("central_widget")
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(30, 30, 30, 30)
        central_layout.setSpacing(18)

        search_panel = self._create_search_panel()
        central_layout.addWidget(search_panel)

        self.table = self._create_table()
        central_layout.addWidget(self.table)
        main_layout.addWidget(central)

        self.search_input.textChanged.connect(self._on_search_text)
        self.btn_registrar.clicked.connect(self._open_registrar_dialog)

    def _create_search_panel(self):
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("Buscar por nombre...")
        self.search_input.setFixedWidth(320)

        self.btn_registrar = QPushButton("Registrar Instructor")
        self.btn_registrar.setObjectName("btn_registrar")

        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        search_layout.addWidget(self.btn_registrar)
        return search_panel

    def _create_table(self):
        table = QTableWidget(0, 4)
        table.setObjectName("maestros_table")
        table.setHorizontalHeaderLabels(["Nombre Completo", "Número De Teléfono", "Estado", "Acciones"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table.setColumnWidth(3, 120)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def _on_search_text(self, text):
        if self.controlador:
            self.controlador.buscar_maestros(text)

    def _open_registrar_dialog(self):
        dlg = QDialog(self)
        dlg.setObjectName("registrar_dialog")
        dlg.setWindowTitle("Registrar Nuevo Instructor")
        
        form = QFormLayout(dlg)
        form.setSpacing(10)
        
        nombre_input = QLineEdit()
        telefono_input = QLineEdit()
        estado_combo = QComboBox()
        estado_combo.addItems(["Activo", "Inactivo"])
        
        form.addRow(QLabel("Nombre Completo:"), nombre_input)
        form.addRow(QLabel("Número De Teléfono:"), telefono_input)
        form.addRow(QLabel("Estado:"), estado_combo)
        
        btn_agregar = QPushButton("Agregar")
        form.addRow("", btn_agregar)

        def on_agregar():
            nombre = nombre_input.text().strip()
            telefono = telefono_input.text().strip()
            if nombre and self.controlador:
                self.controlador.agregar_maestro(nombre, telefono, estado_combo.currentText())
                dlg.accept()
        
        btn_agregar.clicked.connect(on_agregar)
        dlg.exec()

    def limpiar_lista(self):
        self.table.setRowCount(0)

    def agregar_item_lista(self, id_maestro, nombre, telefono, estado):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 48)

        self.table.setItem(row, 0, QTableWidgetItem(nombre))
        self.table.setItem(row, 1, QTableWidgetItem(telefono))
        self.table.setItem(row, 2, QTableWidgetItem(estado))

        edit_btn = QPushButton('\u270E') # Pencil icon
        edit_btn.setProperty("class", "edit_button")
        edit_btn.setToolTip("Editar Instructor")
        edit_btn.clicked.connect(lambda: self.controlador.editar_maestro(id_maestro))

        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.setAlignment(Qt.AlignCenter)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.addWidget(edit_btn)
        self.table.setCellWidget(row, 3, cell_widget)

    def mostrar_mensaje(self, texto):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Información", texto)

    def set_controlador(self, controlador):
        self.controlador = controlador