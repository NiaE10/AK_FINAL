# controlador/controlador_inicio.py
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QObject, QThread
from modelo.manejador_db import ManejadorDB 

# --- Worker para Tareas en Segundo Plano ---
class WorkerDescuento(QObject):
    """
    Worker que se ejecuta en un hilo separado para no bloquear la interfaz.
    """
    proceso_terminado = Signal(bool, str)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.modelo = None

    def ejecutar_descuento(self):
        """
        Llama al método del modelo que descuenta las clases del día actual.
        Crea su propia conexión a la base de datos dentro de este hilo.
        """
        try:
            # Crea una nueva instancia del manejador para este hilo
            self.modelo = ManejadorDB(self.db_path)
            print("Worker: Ejecutando el proceso diario de descuento de clases...")
            self.modelo.descontar_clases_asistidas()
            self.proceso_terminado.emit(True, "Descuento diario completado.")
        except Exception as e:
            error_msg = f"Error en el worker de descuento: {e}"
            print(error_msg)
            self.proceso_terminado.emit(False, error_msg)
        finally:
            # Cierra la conexión de la base de datos del hilo
            if self.modelo:
                self.modelo.cerrar()
                
# --- Controlador Principal ---
class ControladorInicio(QObject):
    alumno_dado_de_baja = Signal()

    def __init__(self, vista, modelo):
        super().__init__()
        self.vista = vista
        self.modelo = modelo
        
        self.vista.baja_alumno.connect(self.baja_alumno)
        self.vista.reinscribir_alumno.connect(self.reinscribir_alumno_action)

        # Lógica de descuento en segundo plano
        self.iniciar_proceso_en_segundo_plano()
        
        # Cargar el panel inmediatamente (no espera al descuento)
        self.cargar_alertas()

    def iniciar_proceso_en_segundo_plano(self):
        """
        Crea y ejecuta el worker para el descuento de asistencias en un hilo separado.
        """
        self.thread = QThread()
        self.worker = WorkerDescuento(self.modelo.db_path)
        self.worker.moveToThread(self.thread)

        # Conectar señales
        self.thread.started.connect(self.worker.ejecutar_descuento)
        self.worker.proceso_terminado.connect(self.thread.quit)
        self.worker.proceso_terminado.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Opcional: Recargar alertas cuando el proceso termine por si algo cambió
        self.worker.proceso_terminado.connect(self.cargar_alertas_post_proceso)

        # Iniciar el hilo
        self.thread.start()

    def cargar_alertas_post_proceso(self, exito, mensaje):
        print(f"Resultado del proceso en segundo plano: {mensaje}")
        if exito:
            self.cargar_alertas()

    def cargar_alertas(self):
        """
        Carga la tabla de la vista de inicio con los alumnos
        que tienen pocas clases restantes.
        """
        try:
            # He vuelto a poner el umbral en 5, ajústalo como necesites.
            alumnos_por_vencer = self.modelo.obtener_alumnos_con_pocas_clases(umbral=5)
            self.vista.mostrar_alertas(alumnos_por_vencer)
            print(f"Panel de inicio actualizado. Se encontraron {len(alumnos_por_vencer)} alertas.")
        except Exception as e:
            print(f"Error al cargar las alertas del panel de inicio: {e}")
            self.vista.clear()

    def baja_alumno(self, alumno_id):
        """
        Marca un alumno como Inactivo y refresca las alertas.
        """
        reply = QMessageBox.question(self.vista, 'Confirmar Baja',
                                     '¿Está seguro de que desea dar de baja a este alumno?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = self.modelo.baja_alumno(alumno_id)
                if success:
                    QMessageBox.information(self.vista, "Baja de Alumno", "Alumno dado de baja correctamente.")
                    self.cargar_alertas()
                    self.alumno_dado_de_baja.emit()
                else:
                    QMessageBox.warning(self.vista, "Error", "No se pudo completar la baja del alumno en la base de datos.")
            except Exception as e:
                QMessageBox.critical(self.vista, "Error", f"Ocurrió un error al intentar dar de baja al alumno: {e}")

    def reinscribir_alumno_action(self, id_inscripcion):
        """
        Reinscribe un alumno usando el ID de la inscripción.
        """
        reply = QMessageBox.question(self.vista, 'Confirmar Reinscripción',
                                     '¿Está seguro de que desea reinscribir a este alumno?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if self.modelo.reinscribir_inscripcion(id_inscripcion):
                    QMessageBox.information(self.vista, "Reinscripción", "Alumno reinscrito correctamente.")
                    self.cargar_alertas()
                else:
                    QMessageBox.warning(self.vista, "Reinscripción", "No se pudo reinscribir al alumno.")
            except Exception as e:
                QMessageBox.critical(self.vista, "Error", f"Error al reinscribir al alumno: {e}")