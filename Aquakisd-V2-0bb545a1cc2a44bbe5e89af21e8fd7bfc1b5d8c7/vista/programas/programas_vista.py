# programas_vista.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox, QLineEdit,
    QAbstractItemView, QMenu
)
from PySide6.QtCore import Signal, Qt
from modelo.manejador_db import ManejadorDB
from PySide6.QtGui import QAction

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
        
        header_layout.addSpacing(20) # Añadir un espacio
        header_layout.addWidget(QLabel("Filtrar por Instructor:"))
        self.filtro_instructor_input = QLineEdit()
        self.filtro_instructor_input.setPlaceholderText("Nombre del instructor...")
        self.filtro_instructor_input.setFixedWidth(300)
        self.filtro_instructor_input.textChanged.connect(self.actualizar_vista_actual)
        header_layout.addWidget(self.filtro_instructor_input)
        
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
        # Permitir seleccionar múltiples filas (Shift/Ctrl + Clic)
        self.tabla_clases.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Habilitar menú contextual (Clic derecho)
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
        """ Vuelve a cargar los datos de la tabla para el programa seleccionado actualmente. """
        current_index = self.combo_programas.currentIndex()
        self._on_programa_selected(current_index)
        print("Vista de Programas actualizada.") 

    def _on_programa_selected(self, index):
        if index <= 0:
            self.mostrar_clases([])
            return

        programa_id = self.combo_programas.itemData(index)
        nombre_prog = self.combo_programas.itemText(index)
        
        filtro_instructor = self.filtro_instructor_input.text().strip()
        try:
            program_ids = self.modelo.mapear_programa_a_ids(programa_id, nombre_prog)
            filas = self.modelo.obtener_clases_detalle_por_programas(
                program_ids,
                nombre_instructor_filtro=filtro_instructor # Pasar el filtro
            )            
            clases = []
            for id_clase, hora_inicio, hora_fin, capacidad, dias, id_prog_fk, nombre_maestro in filas:
                alumnos_inscritos = self.modelo.contar_alumnos_en_clase(id_clase) or 0
                
                cupo_disp = (capacidad - alumnos_inscritos) if capacidad is not None else 'N/A'
                if isinstance(cupo_disp, int) and cupo_disp < 0:
                    cupo_disp = 0

                alumnos_data = self.modelo.buscar_alumnos(id_clase=id_clase, estado=('Activo', 'Baja Pendiente'))
                nombres_alumnos = [f"{a[1]} {a[2]}".strip() for a in alumnos_data]
                
                clases.append({
                    'id_clase': id_clase,
                    'horario': f"{hora_inicio} - {hora_fin}",
                    'cupo_disponible': str(cupo_disp),
                    'dias_semana': dias or '',
                    'nombre_instructor': nombre_maestro if nombre_maestro else 'No Asignado',
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
            self.clases_data = clases # clases ahora contiene 'id_clase'
            for row_idx, clase in enumerate(clases):
                self.tabla_clases.insertRow(row_idx)

                # --- GUARDAR ID_CLASE en el item de la primera columna (Horario) ---
                horario_item = QTableWidgetItem(clase.get('horario', ''))
                horario_item.setData(Qt.UserRole, clase.get('id_clase')) # Guardamos el id_clase aquí
                horario_item.setTextAlignment(Qt.AlignCenter)
                self.tabla_clases.setItem(row_idx, 0, horario_item)
                # ------------------------------------------------------------------

                # Llenar las otras columnas (empezando desde la columna 1)
                column_keys = ['cupo_disponible', 'dias_semana', 'nombre_instructor', 'alumnos_inscritos']
                for col_idx_offset, key in enumerate(column_keys):
                    col_idx = col_idx_offset + 1 # El índice real de la columna
                    item = QTableWidgetItem(clase.get(key, ''))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tabla_clases.setItem(row_idx, col_idx, item)

    def _on_instructor_cell_double_clicked(self, row, column):
        """ Manejador para el doble clic en una celda de la tabla de clases. """
        INSTRUCTOR_COLUMN = 3 # Índice de la columna "Instructor"

        if column == INSTRUCTOR_COLUMN:
            # 1. Obtener el ID de la clase de la fila clickeada
            horario_item = self.tabla_clases.item(row, 0) # El ID se guardó en la columna 0
            if not horario_item: return
            id_clase = horario_item.data(Qt.UserRole)
            if id_clase is None: return

            # 2. Obtener lista de instructores activos del modelo
            try:
                # Usamos el filtro solo_activos=True y orden alfabético
                instructores_raw = self.modelo.listar_maestros(solo_activos=True)
                # Crear diccionario {Nombre: ID} y lista de nombres para el diálogo
                instructores_dict = {m[1]: m[0] for m in instructores_raw}
                nombres_instructores = list(instructores_dict.keys())
                if not nombres_instructores:
                    QMessageBox.warning(self, "Sin Instructores", "No hay instructores activos registrados.")
                    return

                # Añadir opción para desasignar
                nombres_instructores.insert(0, "[Quitar Instructor]")
                instructores_dict["[Quitar Instructor]"] = None # Usamos None como ID para desasignar

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo obtener la lista de instructores: {e}")
                return

            # 3. Mostrar diálogo de selección QInputDialog
            nombre_seleccionado, ok = QInputDialog.getItem(
                self,
                "Asignar Instructor",
                f"Selecciona un instructor para la clase:",
                nombres_instructores,
                0, # Índice inicial (mostrar "[Quitar Instructor]" primero)
                False # No editable
            )

            # 4. Si el usuario seleccionó y presionó OK
            if ok and nombre_seleccionado:
                id_maestro_seleccionado = instructores_dict[nombre_seleccionado]

                # 5. Llamar al modelo para actualizar la base de datos
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
                    QMessageBox.critical(self, "Error", f"Error al intentar asignar instructor: {e}")
                    
    def _mostrar_menu_clase(self, position):
        """Muestra menú contextual para reponer una o varias clases seleccionadas."""
        # Obtener índices de filas seleccionadas únicas
        filas_seleccionadas = sorted(set(idx.row() for idx in self.tabla_clases.selectedIndexes()))
        
        if not filas_seleccionadas:
            return

        # Recuperar los IDs de las clases de esas filas
        ids_clases = []
        for row in filas_seleccionadas:
            item_horario = self.tabla_clases.item(row, 0)
            if item_horario:
                ids_clases.append(item_horario.data(Qt.UserRole))
        
        if not ids_clases:
            return

        cantidad = len(ids_clases)
        texto_menu = f"Reponer Clases (+1) a {cantidad} grupos seleccionados"

        menu = QMenu()
        action_reponer = QAction(texto_menu, self)
        menu.addAction(action_reponer)

        action = menu.exec(self.tabla_clases.viewport().mapToGlobal(position))

        if action == action_reponer:
            reply = QMessageBox.question(
                self, "Confirmar Reposición Masiva",
                f"¿Estás seguro de reponer la clase a los {cantidad} grupos seleccionados?\n\n"
                "Se sumará +1 clase a TODOS los alumnos activos inscritos en estos horarios.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                exitos = 0
                for id_clase in ids_clases:
                    if self.modelo.agregar_clase_extra_grupo(id_clase, "Falta Instructor (Reposición Masiva)"):
                        exitos += 1
                
                QMessageBox.information(self, "Proceso Terminado", f"Se procesaron correctamente {exitos} de {cantidad} clases.")
                # Opcional: Recargar la vista si quisieras ver cambios inmediatos en cupos (aunque aquí solo cambiamos clases restantes)
                # self.actualizar_vista_actual()