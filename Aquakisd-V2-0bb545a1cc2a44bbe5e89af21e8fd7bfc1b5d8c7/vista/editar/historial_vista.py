# vista/editar/historial_vista.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class HistorialVista(QDialog):
    def __init__(self, historial=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Modificaciones")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(3)
        self.tabla_historial.setHorizontalHeaderLabels(["Fecha", "Tipo de Modificación", "Detalles"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_historial.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.tabla_historial)
        
        self.cargar_datos(historial or [])

    def cargar_datos(self, historial):
        self.tabla_historial.setRowCount(0)
        for fila_datos in historial:
            row = self.tabla_historial.rowCount()
            self.tabla_historial.insertRow(row)
            # Asumiendo que `fila_datos` es una tupla: (FECHA, TIPO_MODIFICACION, DETALLES)
            self.tabla_historial.setItem(row, 0, QTableWidgetItem(str(fila_datos[0])))
            self.tabla_historial.setItem(row, 1, QTableWidgetItem(str(fila_datos[1])))
            self.tabla_historial.setItem(row, 2, QTableWidgetItem(str(fila_datos[2])))