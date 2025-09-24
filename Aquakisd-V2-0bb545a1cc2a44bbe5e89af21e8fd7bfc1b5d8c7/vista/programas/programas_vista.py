# programas_vista.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Signal, Qt
from modelo.manejador_db import ManejadorDB


class ProgramasVista(QWidget):
    programa_seleccionado = Signal(int)

    def __init__(self, modelo: ManejadorDB = None, parent=None):
        super().__init__(parent)
        self.setObjectName('programas_vista')

        self.modelo = modelo or ManejadorDB()
        self._programas_data = []
        self.clases_data = []
        
        self._build_ui()
        self._load_initial_data()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_strip = QWidget()
        top_strip.setObjectName("top_strip")
        top_strip.setFixedHeight(80)
        main_layout.addWidget(top_strip)

        center_area = QWidget()
        center_area.setObjectName("center_area")
        center_layout = QVBoxLayout(center_area)
        center_layout.setContentsMargins(30, 30, 30, 30)
        center_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Seleccionar Programa:"))
        self.combo_programas = QComboBox()
        self.combo_programas.setFixedWidth(400)
        self.combo_programas.currentIndexChanged.connect(self._on_programa_selected)
        header_layout.addWidget(self.combo_programas)
        header_layout.addStretch()
        center_layout.addLayout(header_layout)

        self.tabla_clases = QTableWidget()
        self.tabla_clases.setColumnCount(5)
        self.tabla_clases.setHorizontalHeaderLabels([
            "Horario", "Cupo Disponible", "Días", "Instructor", "Alumnos Inscritos"
        ])
        self.tabla_clases.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_clases.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.tabla_clases.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_clases.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_clases.setAlternatingRowColors(True)
        center_layout.addWidget(self.tabla_clases)

        main_layout.addWidget(center_area, 1)

        bottom_strip = QWidget()
        bottom_strip.setObjectName("bottom_strip")
        bottom_strip.setFixedHeight(80)
        main_layout.addWidget(bottom_strip)

        self.setLayout(main_layout)

    def _load_initial_data(self):
        try:
            programas = self.modelo.obtener_programas()
            programas_normalizados = [
                {'id_programa': p[0], 'nombre_programa': p[1]} for p in programas
            ]
            self.cargar_programas(programas_normalizados)
        except Exception as e:
            print(f"Error loading initial programs: {e}")
            self.cargar_programas([])

    def _on_programa_selected(self, index):
        if index <= 0:
            self.mostrar_clases([])
            return

        programa_id = self.combo_programas.itemData(index)
        nombre_prog = self.combo_programas.itemText(index)
        
        try:
            program_ids = self.modelo.mapear_programa_a_ids(programa_id, nombre_prog)
            filas = self.modelo.obtener_clases_detalle_por_programas(program_ids)
            
            clases = []
            for id_clase, hora_inicio, hora_fin, capacidad, dias, id_prog_fk in filas:
                alumnos_inscritos = self.modelo.contar_alumnos_en_clase(id_clase) or 0
                
                cupo_disp = (capacidad - alumnos_inscritos) if capacidad is not None else 'N/A'
                if isinstance(cupo_disp, int) and cupo_disp < 0:
                    cupo_disp = 0

                alumnos_data = self.modelo.buscar_alumnos(id_clase=id_clase)
                nombres_alumnos = [f"{a[1]} {a[2]}".strip() for a in alumnos_data]
                
                clases.append({
                    'horario': f"{hora_inicio} - {hora_fin}",
                    'cupo_disponible': str(cupo_disp),
                    'dias_semana': dias or '',
                    'nombre_instructor': 'No Asignado',  # Placeholder
                    'alumnos_inscritos': ", ".join(nombres_alumnos)
                })
            self.mostrar_clases(clases)
        except Exception as e:
            print(f"Error fetching classes for program {programa_id}: {e}")
            self.mostrar_clases([])

    def cargar_programas(self, programas):
        self.combo_programas.clear()
        self.combo_programas.addItem("Seleccione un programa", None)
        self._programas_data = programas
        for programa in programas:
            self.combo_programas.addItem(programa['nombre_programa'], programa['id_programa'])

    def mostrar_clases(self, clases):
        self.tabla_clases.setRowCount(0)
        self.clases_data = clases
        for row_idx, clase in enumerate(clases):
            self.tabla_clases.insertRow(row_idx)
            for col_idx, key in enumerate(['horario', 'cupo_disponible', 'dias_semana', 'nombre_instructor', 'alumnos_inscritos']):
                item = QTableWidgetItem(clase.get(key, ''))
                item.setTextAlignment(Qt.AlignCenter)
                self.tabla_clases.setItem(row_idx, col_idx, item)
