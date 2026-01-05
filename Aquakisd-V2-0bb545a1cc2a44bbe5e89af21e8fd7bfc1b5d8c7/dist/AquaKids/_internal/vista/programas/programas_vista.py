# programas_vista.py
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox, QLineEdit,
    QAbstractItemView, QMenu
)
from PySide6.QtCore import Signal, Qt
from modelo.manejador_db import ManejadorDB
from PySide6.QtGui import QAction, QColor

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

        # Franja superior decorativa
        top_strip = QWidget()
        top_strip.setObjectName("top_strip")
        top_strip.setFixedHeight(80)
        main_layout.addWidget(top_strip)

        center_area = QWidget()
        center_area.setObjectName("center_area")
        center_layout = QVBoxLayout(center_area)
        center_layout.setContentsMargins(30, 30, 30, 30)
        center_layout.setSpacing(20)

        # --- Filtros ---
        header_layout = QHBoxLayout()
        
        # Combo Programas
        lbl_prog = QLabel("Seleccionar Programa:")
        lbl_prog.setStyleSheet("font-weight: bold; color: #307EA4; font-size: 14px;")
        header_layout.addWidget(lbl_prog)
        
        self.combo_programas = QComboBox()
        self.combo_programas.setFixedWidth(350)
        self.combo_programas.currentIndexChanged.connect(self._on_programa_selected)
        header_layout.addWidget(self.combo_programas)
        
        header_layout.addSpacing(30)
        
        # Filtro Instructor
        lbl_inst = QLabel("Filtrar por Instructor:")
        lbl_inst.setStyleSheet("font-weight: bold; color: #307EA4; font-size: 14px;")
        header_layout.addWidget(lbl_inst)
        
        self.filtro_instructor_input = QLineEdit()
        self.filtro_instructor_input.setPlaceholderText("Nombre del instructor...")
        self.filtro_instructor_input.setFixedWidth(250)
        self.filtro_instructor_input.textChanged.connect(self.actualizar_vista_actual)
        header_layout.addWidget(self.filtro_instructor_input)
        
        header_layout.addStretch()
        center_layout.addLayout(header_layout)

        # --- Tabla de Clases ---
        self.tabla_clases = QTableWidget()
        self.tabla_clases.setColumnCount(5)
        headers = ["Horario", "Cupo Disp.", "Días", "Instructor", "Alumnos Inscritos"]
        self.tabla_clases.setHorizontalHeaderLabels(headers)
        
        # 1. AJUSTE CLAVE: Permitir que las filas crezcan (WordWrap + ResizeToContents)
        self.tabla_clases.setWordWrap(True)
        self.tabla_clases.setTextElideMode(Qt.ElideNone)
        
        # Ajuste vertical automático para que quepan todos los nombres
        self.tabla_clases.verticalHeader().setVisible(True)
        self.tabla_clases.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.tabla_clases.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Ajuste horizontal
        header = self.tabla_clases.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Horario
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Cupo
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Días
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Instructor
        header.setSectionResizeMode(4, QHeaderView.Stretch)          # Alumnos (El más ancho)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.tabla_clases.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_clases.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_clases.setAlternatingRowColors(True)
        self.tabla_clases.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # Menú contextual
        self.tabla_clases.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_clases.customContextMenuRequested.connect(self._mostrar_menu_clase)
        self.tabla_clases.cellDoubleClicked.connect(self._on_instructor_cell_double_clicked)
        
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
            
    def actualizar_vista_actual(self):
        current_index = self.combo_programas.currentIndex()
        self._on_programa_selected(current_index)

    def _on_programa_selected(self, index):
        if index <= 0:
            self.mostrar_clases([])
            return

        programa_id = self.combo_programas.itemData(index)
        nombre_prog = self.combo_programas.itemText(index)
        filtro_instructor = self.filtro_instructor_input.text().strip()
        
        try:
            program_ids = self.modelo.mapear_programa_a_ids(programa_id)            
            filas = self.modelo.obtener_clases_detalle_por_programas(
                program_ids,
                nombre_instructor_filtro=filtro_instructor
            )         
            clases = []
            # CORRECCIÓN: Usamos 'cupo_sql' directamente. La variable 'capacidad' en tu código anterior 
            # en realidad recibía el cupo ya calculado por la Query. Evitamos la doble resta y la consulta N+1.
            for id_clase, hora_inicio, hora_fin, cupo_sql, dias, id_prog_fk, nombre_maestro in filas:
                
                cupo_disp = cupo_sql if cupo_sql is not None else 'N/A'
                if isinstance(cupo_disp, int) and cupo_disp < 0:
                    cupo_disp = 0

                alumnos_data = self.modelo.buscar_alumnos(id_clase=id_clase, estado=('Activo', 'Baja Pendiente'))
                nombres_alumnos = [f"{a[1]} {a[2]}".strip() for a in alumnos_data]
                
                # 2. DISEÑO DE LISTA: Formato vertical con viñetas
                if alumnos_data:
                    # Crea una lista: "• Juan Perez\n• Maria Lopez..."
                    lista_nombres = [f"• {a[1]} {a[2]}".strip() for a in alumnos_data]
                    texto_alumnos = "\n".join(lista_nombres)
                else:
                    texto_alumnos = "Sin Inscritos"

                clases.append({
                    'id_clase': id_clase,
                    'horario': f"{hora_inicio} - {hora_fin}",
                    'cupo_disponible': str(cupo_disp),
                    'dias_semana': dias or '',
                    'nombre_instructor': nombre_maestro if nombre_maestro else 'No Asignado',
                    'alumnos_texto': texto_alumnos, # Texto formateado
                    'tiene_alumnos': bool(alumnos_data)
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

            # Col 0: Horario (Guardamos ID oculto)
            horario_item = QTableWidgetItem(clase.get('horario', ''))
            horario_item.setData(Qt.UserRole, clase.get('id_clase'))
            horario_item.setTextAlignment(Qt.AlignCenter)
            self.tabla_clases.setItem(row_idx, 0, horario_item)

            # Col 1: Cupo
            cupo_item = QTableWidgetItem(clase.get('cupo_disponible', ''))
            cupo_item.setTextAlignment(Qt.AlignCenter)
            self.tabla_clases.setItem(row_idx, 1, cupo_item)

            # Col 2: Días
            dias_item = QTableWidgetItem(clase.get('dias_semana', ''))
            dias_item.setTextAlignment(Qt.AlignCenter)
            self.tabla_clases.setItem(row_idx, 2, dias_item)

            # Col 3: Instructor
            inst_item = QTableWidgetItem(clase.get('nombre_instructor', ''))
            inst_item.setTextAlignment(Qt.AlignCenter)
            # Resaltar si falta instructor
            if clase.get('nombre_instructor') == 'No Asignado':
                inst_item.setForeground(QColor("#E57373")) # Rojo suave
            self.tabla_clases.setItem(row_idx, 3, inst_item)

            # Col 4: Alumnos Inscritos (DISEÑO MEJORADO)
            alumnos_item = QTableWidgetItem(clase.get('alumnos_texto', ''))
            
            # Si hay alumnos, alineamos a la Izquierda para que se lea la lista
            # Si no hay ("Sin Inscritos"), centramos y ponemos gris
            if clase.get('tiene_alumnos'):
                alumnos_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                alumnos_item.setForeground(QColor("#333333"))
            else:
                alumnos_item.setTextAlignment(Qt.AlignCenter)
                alumnos_item.setForeground(QColor("#90A4AE")) # Gris
                
            self.tabla_clases.setItem(row_idx, 4, alumnos_item)

    def _on_instructor_cell_double_clicked(self, row, column):
        INSTRUCTOR_COLUMN = 3 
        if column == INSTRUCTOR_COLUMN:
            horario_item = self.tabla_clases.item(row, 0)
            if not horario_item: return
            id_clase = horario_item.data(Qt.UserRole)
            if id_clase is None: return

            try:
                instructores_raw = self.modelo.listar_maestros(solo_activos=True)
                instructores_dict = {m[1]: m[0] for m in instructores_raw}
                nombres_instructores = list(instructores_dict.keys())
                if not nombres_instructores:
                    QMessageBox.warning(self, "Sin Instructores", "No hay instructores activos registrados.")
                    return

                nombres_instructores.insert(0, "[Quitar Instructor]")
                instructores_dict["[Quitar Instructor]"] = None 

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo obtener la lista de instructores: {e}")
                return

            nombre_seleccionado, ok = QInputDialog.getItem(
                self, "Asignar Instructor", f"Selecciona un instructor:",
                nombres_instructores, 0, False
            )

            if ok and nombre_seleccionado:
                id_maestro_seleccionado = instructores_dict[nombre_seleccionado]
                try:
                    # CORRECCIÓN 1: Usar la variable correcta 'id_maestro_seleccionado'
                    exito, mensaje = self.modelo.asignar_instructor_a_clase(id_clase, id_maestro_seleccionado)
                    
                    if exito:
                        # CORRECCIÓN 2: Limpiar la línea del mensaje de éxito y recargar la tabla
                        QMessageBox.information(self, "Éxito", mensaje)
                        self.actualizar_vista_actual() # Recargar la tabla para ver el cambio
                    else:
                        QMessageBox.warning(self, "Cruce de Horarios", mensaje)
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al asignar: {e}")
                    
    def _mostrar_menu_clase(self, position):
        filas_seleccionadas = sorted(set(idx.row() for idx in self.tabla_clases.selectedIndexes()))
        if not filas_seleccionadas: return

        ids_clases = []
        for row in filas_seleccionadas:
            item_horario = self.tabla_clases.item(row, 0)
            if item_horario:
                ids_clases.append(item_horario.data(Qt.UserRole))
        
        if not ids_clases: return

        cantidad = len(ids_clases)
        texto_menu = f"Reponer Clases (+1) a {cantidad} grupos seleccionados"

        menu = QMenu()
        action_reponer = QAction(texto_menu, self)
        menu.addAction(action_reponer)

        action = menu.exec(self.tabla_clases.viewport().mapToGlobal(position))

        if action == action_reponer:
            reply = QMessageBox.question(
                self, "Confirmar Reposición",
                f"¿Reponer clase a {cantidad} grupos?\n(+1 clase a todos los alumnos activos)",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                exitos = 0
                for id_clase in ids_clases:
                    if self.modelo.agregar_clase_extra_grupo(id_clase, "Falta Instructor (Reposición Masiva)"):
                        exitos += 1
                QMessageBox.information(self, "Listo", f"Se procesaron {exitos} grupos.")