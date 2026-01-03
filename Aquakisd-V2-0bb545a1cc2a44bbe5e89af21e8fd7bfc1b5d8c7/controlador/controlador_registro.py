# controlador/controlador_registro.py
from modelo.manejador_db import ManejadorDB
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QObject
from datetime import datetime
import re
class ControladorRegistro(QObject):
    alumno_registrado = Signal() # <-- Declarar la señal aquí

    def __init__(self, vista, modelo=None):
        super().__init__()
        self.vista = vista
        try:
            self.vista.controlador = self
        except Exception:
            pass
        self.modelo = modelo if modelo else ManejadorDB()
        self._conectar_eventos()
        self._cargar_programas()

    def _conectar_eventos(self):
        # Conecta el botón de guardar de la vista con el método registrar_alumno
        self.vista.guardar_btn.clicked.connect(self.registrar_alumno)
        # Conectar cambios en selección de programa y días para poblar dependencias
        try:
            self.vista.programa_combo.currentIndexChanged.connect(self._programa_cambiado)
            self.vista.dias_combo.currentIndexChanged.connect(self._dias_cambiado)
        except Exception:
            # Si los widgets no existen aún, conexiones se harán después de cargar programas
            pass

    def _cargar_programas(self):
        programas = self.modelo.obtener_programas()
        self.vista.programa_combo.clear()
        for id_prog, nombre in programas:
            self.vista.programa_combo.addItem(nombre, id_prog)

        # Si hay programas, disparar la carga inicial de días
        if self.vista.programa_combo.count() > 0:
            # Forzar carga para el primer índice
            self._programa_cambiado(0)

    def registrar_alumno(self):
        # --- 1. OBTENER DATOS Y VALIDACIONES INICIALES ---
        datos = self.vista.obtener_datos_formulario()
        
        if datos['nivel'] == "-- Seleccione Nivel --":
            self.vista.mostrar_mensaje("Error: Debes seleccionar un Nivel para el alumno.")
            return
        
        if not datos['nombre'] or not datos['apellido']:
            self.vista.mostrar_mensaje("Nombre y apellido son obligatorios.")
            return

        id_clase = self.vista.horario_combo.currentData()
        if id_clase is None:
            self.vista.mostrar_mensaje("Debe seleccionar un horario/clase.")
            return
        try:
            fecha_nac = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
            if fecha_nac > datetime.now().date():
                self.vista.mostrar_mensaje("Error: La fecha de nacimiento no puede ser una fecha futura.")
                return
        except ValueError:
            self.vista.mostrar_mensaje("Error: Formato de fecha inválido.")
            return
        if len(datos['nombre']) > 50 or len(datos['apellido']) > 50:
            self.vista.mostrar_mensaje("Error: El nombre o apellido exceden el límite permitido (50 caracteres).")
            return
        
        patron_nombre = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\']+$"
        
        if not re.match(patron_nombre, datos['nombre']) or not re.match(patron_nombre, datos['apellido']):
            self.vista.mostrar_mensaje("Error: Nombre o Apellido contienen caracteres inválidos (solo letras, guiones y apóstrofes).")
            return
        
        patron_tel = r"^[\d\s\-\(\)]+$"
        
        # Validamos Teléfono 1 (Si tiene datos, debe cumplir el patrón)
        if datos['telefono'] and not re.match(patron_tel, datos['telefono']):
            self.vista.mostrar_mensaje("Error: El teléfono principal contiene caracteres inválidos (use solo números).")
            return

        # Validamos Teléfono 2 (Solo si escribieron algo)
        if datos['telefono2'] and not re.match(patron_tel, datos['telefono2']):
            self.vista.mostrar_mensaje("Error: El teléfono secundario contiene caracteres inválidos.")
            return

        # --- 2. VALIDACIÓN DE EDAD ---
        try:
            edad_en_meses = int(datos.get('edad', 0))  # La vista ya lo entrega en meses
            rango = self.modelo.obtener_rango_edad_clase(id_clase)
            if rango:
                edad_min, edad_max = rango
                if not (edad_min <= edad_en_meses <= edad_max):
                    resp = QMessageBox.question(self.vista, "Edad fuera de rango", 
                                                "La edad del niño está fuera del rango para esta clase. ¿Deseas registrarlo de todos modos?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if resp != QMessageBox.Yes:
                        return
        except Exception as e:
            self.vista.mostrar_mensaje(f"No se pudo verificar la edad: {e}")
            return

        # --- 3. VALIDACIÓN DE CAPACIDAD ---
        try:
            capacidad = self.modelo.obtener_capacidad_clase(id_clase)
            if capacidad is None:
                self.vista.mostrar_mensaje("No se pudo determinar la capacidad de la clase.")
                return
                
            inscritos = self.modelo.contar_alumnos_en_clase(id_clase)
            id_programa = datos.get('id_programa')
            plazas_necesarias = 2 if id_programa in (3, 6) else 1

            if (inscritos + plazas_necesarias) > capacidad:
                self.vista.mostrar_mensaje("La clase está llena. Elija otra opción o espere.")
                return
        except Exception as e:
            self.vista.mostrar_mensaje(f"No se pudo verificar la capacidad: {e}")
            return

        # --- 4. TRANSACCIÓN CONTROLADA SEGÚN ESTADO ---
        id_alumno_nuevo = None
        try:
            # A. Insertar al alumno (Se guarda sea Activo, Lista de Espera, etc.)
            id_alumno_nuevo = self.modelo.insertar_alumno(
                nombre=datos['nombre'],
                apellido=datos['apellido'],
                edad=edad_en_meses,
                telefono=datos['telefono'],
                telefono2=datos['telefono2'],
                fecha_nacimiento=datos['fecha_nacimiento'],
                observaciones=datos['observaciones'],
                estado=datos['estado'],
                nivel=datos['nivel'],
                id_clase=id_clase
            )

            if not id_alumno_nuevo:
                raise Exception("La base de datos no devolvió el ID del nuevo alumno.")

            # B. Lógica de Inscripción (SOLO SI ES ACTIVO)
            if datos['estado'] == 'Activo':
                fecha_inicio = self.vista.fecha_inicio.date().toString('yyyy-MM-dd')
                
                try:
                    # Intentamos crear el contrato
                    self.modelo.crear_inscripcion(
                        id_alumno_nuevo,
                        id_programa,
                        id_clase,
                        fecha_inicio
                    )
                    
                    # Si es Activo y tiene programa especial, restamos cupo
                    if plazas_necesarias > 1:
                        self.modelo.restar_capacidad_clase(id_clase, plazas_necesarias)
                        
                except Exception as e_inscripcion:
                    # --- ROLLBACK SOLO PARA ACTIVOS ---
                    # Si un alumno DEBE ser activo pero falla su contrato, es un registro inválido.
                    print(f"[ERROR CRÍTICO] Falló inscripción de alumno Activo. Revirtiendo...")
                    self.modelo.cursor.execute("DELETE FROM ALUMNOS WHERE ID_ALUMNO = ?", (id_alumno_nuevo,))
                    self.modelo.conn.commit()
                    raise Exception(f"No se pudo formalizar la inscripción. El registro ha sido cancelado.\nDetalle: {e_inscripcion}")

            # C. Si es Lista de Espera o Prioridad, simplemente pasamos por aquí sin crear inscripción
            # y sin hacer rollback. El alumno queda guardado correctamente sin contrato.

            self.vista.mostrar_mensaje(f"Alumno registrado correctamente con estado: {datos['estado']}.")
            self.vista.limpiar_formulario()
            self.alumno_registrado.emit()

        except Exception as e:
            self.vista.mostrar_mensaje(f"Error en el proceso de registro: {e}")

    def _programa_cambiado(self, index):
        # Obtener id_programa y poblar dias_combo con los días disponibles para ese programa
        id_prog = self.vista.programa_combo.itemData(index)
        try:
            nombre_prog = self.vista.programa_combo.itemText(index).strip()
        except Exception:
            nombre_prog = ''
        program_ids = self.modelo.mapear_programa_a_ids(id_prog, nombre_prog)
        if not program_ids:
            self.vista.dias_combo.clear()
            return
        dias = self.modelo.obtener_dias_para_programas(program_ids)
        self.vista.dias_combo.clear()
        for d in dias:
            self.vista.dias_combo.addItem(d)
        # Forzar carga de horarios para el primer día si existe
        if self.vista.dias_combo.count() > 0:
            self._dias_cambiado(0)

    def _dias_cambiado(self, index):
        # Poblar horarios (clases) para el programa y día seleccionados
        id_prog = self.vista.programa_combo.currentData()
        dias = self.vista.dias_combo.itemText(index) if index >= 0 else None
        self.vista.horario_combo.clear()
        if id_prog is None or dias is None:
            return
        try:
            nombre_prog = self.vista.programa_combo.currentText().strip()
        except Exception:
            nombre_prog = ''
        program_ids = self.modelo.mapear_programa_a_ids(id_prog, nombre_prog)
        clases = self.modelo.obtener_clases_por_programas_y_dia(program_ids, dias)
        # clases: list of tuples (ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD, ID_PROGRAMAFK)
        for id_clase, hora_inicio, hora_fin, capacidad, id_prog_fk in clases:
            # Obtener inscritos actuales (excluyendo lista de espera/prioridad)
            try:
                inscritos = self.modelo.contar_alumnos_en_clase(id_clase)
            except Exception:
                inscritos = 0

            disponibles = None
            try:
                if capacidad is not None:
                    disponibles = int(capacidad) - int(inscritos)
                    if disponibles < 0:
                        disponibles = 0
            except Exception:
                disponibles = None

            # Determinar política de filtrado según el programa seleccionado
            id_prog_actual = id_prog

            # Para PROGRAMA 3 y 6 se requieren al menos 2 espacios disponibles
            if id_prog_actual in (3, 6):
                # Si no podemos calcular disponibles, omitimos la clase
                if disponibles is None:
                    continue
                try:
                    if int(disponibles) < 2:
                        continue
                except Exception:
                    continue
            else:
                # Para otros programas, si la capacidad es desconocida omitimos la clase
                if capacidad is None:
                    continue

            # Convertir horas a texto legible y mostrar disponibles
            if disponibles is None:
                display = f"{hora_inicio} - {hora_fin}"
            else:
                display = f"{hora_inicio} - {hora_fin}, (disponibles: {disponibles})"
            self.vista.horario_combo.addItem(display, id_clase)

    def refrescar_cupos(self):
        """Refresca la disponibilidad de cupos en los combos de programa, días y horarios."""
        self._cargar_programas()
