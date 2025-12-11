# Reemplaza todo el contenido de: vista/editar/historial_vista.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class HistorialVista(QDialog):
    def __init__(self, historial=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Modificaciones")
        self.setMinimumSize(800, 400)  # Aumentamos el tamaño mínimo

        layout = QVBoxLayout(self)
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(5) # <-- CAMBIO a 5 columnas
        
        # <-- CAMBIO en los títulos
        self.tabla_historial.setHorizontalHeaderLabels([
            "Fecha de Registro", 
            "Tipo de Modificación", 
            "Fecha de Inicio", 
            "Fecha de Fin", 
            "Detalles"
        ])
        
        # Ajustamos el tamaño de las columnas
        self.tabla_historial.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) # Detalles ocupa el espacio restante
        
        self.tabla_historial.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.tabla_historial)
        
        self.cargar_datos(historial or [])

    def cargar_datos(self, historial):
        self.tabla_historial.setRowCount(0)
        for fila_datos in historial:
            row = self.tabla_historial.rowCount()
            self.tabla_historial.insertRow(row)
            
            # --- Lógica de carga modificada para 5 columnas ---
            # fila_datos ahora es: (FECHA_REGISTRO, TIPO, FECHA_INICIO, FECHA_FIN, DETALLES)
            
            # Columna 0: Fecha de Registro
            self.tabla_historial.setItem(row, 0, QTableWidgetItem(str(fila_datos[0] or '')))
            # Columna 1: Tipo de Modificación
            self.tabla_historial.setItem(row, 1, QTableWidgetItem(str(fila_datos[1] or '')))
            # Columna 2: Fecha de Inicio
            self.tabla_historial.setItem(row, 2, QTableWidgetItem(str(fila_datos[2] or '')))
            # Columna 3: Fecha de Fin
            self.tabla_historial.setItem(row, 3, QTableWidgetItem(str(fila_datos[3] or '')))
            # Columna 4: Detalles
            self.tabla_historial.setItem(row, 4, QTableWidgetItem(str(fila_datos[4] or '')))