from modelo.manejador_db import ManejadorDB
from PySide6.QtCore import Signal, QObject 
class ControladorMaestros(QObject):
    maestro_actualizado = Signal()
    def __init__(self, vista, modelo=None):
        super().__init__()
        self.vista = vista
        self.modelo = modelo if modelo else ManejadorDB()
        try:
            self.vista.set_controlador(self)
        except Exception:
            try:
                self.vista.controlador = self
            except Exception:
                pass
        self._conectar()
        self.cargar_maestros()

    def _conectar(self):
        # la vista conecta búsqueda y abrir diálogo; controlador implementa las acciones
        try:
            # conecta doble protección si la vista ya enlazó por su cuenta
            pass
        except Exception:
            pass

    def cargar_maestros(self):
        self.vista.limpiar_lista()
        filas = self.modelo.listar_maestros()
        for id_m, nombre, telefono, estado in filas:
            self.vista.agregar_item_lista(id_m, nombre, telefono, estado)

    def buscar_maestros(self, texto):
        if not texto:
            self.cargar_maestros()
            return
        filas = self.modelo.buscar_maestros_por_nombre(texto)
        self.vista.limpiar_lista()
        for id_m, nombre, telefono, estado in filas:
            self.vista.agregar_item_lista(id_m, nombre, telefono, estado)

    def agregar_maestro(self, nombre, telefono, estado='Activo'):
        if not nombre:
            self.vista.mostrar_mensaje('El nombre es obligatorio.')
            return
        try:
            self.modelo.insertar_maestro(nombre, telefono, estado)
            self.vista.mostrar_mensaje('Instructor agregado correctamente.')
            self.cargar_maestros()
            self.maestro_actualizado.emit()
        except Exception as e:
            self.vista.mostrar_mensaje(f'Error al agregar: {e}')

    def editar_maestro(self, id_maestro):
        # Obtener datos actuales
        try:
            filas = [r for r in self.modelo.listar_maestros() if r[0] == id_maestro]
            if not filas:
                self.vista.mostrar_mensaje('Instructor no encontrado.')
                return
            _, nombre, telefono, estado = filas[0]

            # Crear diálogo similar al de creación pero precargado
            from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton
            dlg = QDialog()
            dlg.setWindowTitle('Editar Instructor')
            form = QFormLayout(dlg)
            nombre_input = QLineEdit(nombre)
            telefono_input = QLineEdit(telefono)
            estado_combo = QComboBox()
            estado_combo.addItems(['Activo', 'Inactivo'])
            estado_combo.setCurrentText(estado)
            form.addRow('Nombre Completo', nombre_input)
            form.addRow('Numero De Telefono', telefono_input)
            form.addRow('Estado', estado_combo)
            btn_save = QPushButton('Guardar')
            form.addWidget(btn_save)

            def on_save():
                new_nombre = nombre_input.text().strip()
                new_tel = telefono_input.text().strip()
                new_estado = estado_combo.currentText()
                try:
                    self.modelo.actualizar_maestro(id_maestro, new_nombre, new_tel, new_estado)
                    self.vista.mostrar_mensaje('Instructor actualizado.')
                    self.cargar_maestros()
                    self.maestro_actualizado.emit()
                    dlg.accept()
                except Exception as e:
                    self.vista.mostrar_mensaje(f'Error al actualizar: {e}')
            btn_save.clicked.connect(on_save)
            dlg.exec()
        except Exception as e:
            self.vista.mostrar_mensaje(f'Error: {e}')
