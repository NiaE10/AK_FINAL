import sys
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import unittest.mock
from controlador.controlador_maestros import ControladorMaestros
from controlador.controlador_alumnos import ControladorAlumnos
# ==========================================================================
# CONFIGURACIÓN CRÍTICA DE ENTORNO (FIX PARA ModuleNotFoundError)
# ==========================================================================
# Obtenemos la ruta absoluta donde está este archivo (la raíz del proyecto)
ruta_proyecto = os.path.dirname(os.path.abspath(__file__))

# Insertamos esta ruta en la POSICIÓN 0 del path del sistema
# Esto obliga a Python a buscar módulos aquí primero
sys.path.insert(0, ruta_proyecto)

print(f"--> Ejecutando pruebas desde: {ruta_proyecto}")
# ==========================================================================

# AHORA sí podemos importar los módulos del proyecto
try:
    from modelo.manejador_db import ManejadorDB
    from controlador.controlador_registro import ControladorRegistro
except ImportError as e:
    print(f"\n[ERROR CRÍTICO] No se pudo importar un módulo: {e}")
    print("Asegúrese de que las carpetas 'modelo' y 'controlador' tengan un archivo __init__.py (puede estar vacío).")
    sys.exit(1)

class TestRobustezAquaKids(unittest.TestCase):

    def setUp(self):
        # Inicializa la DB antes de cada test para evitar el error 'no attribute db'
        self.db = ManejadorDB()

    def tearDown(self):
        """Limpieza después de CADA prueba."""
        try:
            self.db.cerrar()
        except Exception:
            pass

    # ====================================================================
    # PRUEBAS DE LOS FIXES (Verifica que sus correcciones funcionen)
    # ====================================================================

    def test_fix_division_cero_vencimiento(self):
        """Verifica que NO explote si los días de clase están vacíos (su arreglo: max(1, ...))."""
        print("\n[TEST] Validación de división por cero en fechas...")
        
        # Caso: dias_str es una cadena vacía o None implícito en split
        try:
            # Simulamos inputs que antes rompían el sistema
            fecha = self.db.calcular_fecha_vencimiento("2024-01-01", 4, "")
            self.assertIsNotNone(fecha, "Debería retornar una fecha calculada (dividiendo entre 1 por defecto)")
            print("   -> OK: El sistema manejó dias_str vacío.")
        except ZeroDivisionError:
            self.fail("FALLÓ EL FIX: El sistema colapsó por división entre cero.")
        except Exception as e:
            self.fail(f"FALLÓ EL FIX: Ocurrió otro error inesperado: {e}")

    def test_fix_edad_negativa(self):
        """Verifica que NO retorne edades negativas para fechas futuras (su arreglo: max(0, ...))."""
        print("[TEST] Validación de edad negativa...")
        
        # Fecha futura (año 3000)
        futuro = "3000-01-01"
        edad = self.db._calcular_edad_meses(futuro)
        
        self.assertGreaterEqual(edad, 0, f"Error: La edad no puede ser negativa. Dio: {edad}")
        self.assertEqual(edad, 0, "Una fecha futura debería resultar en 0 meses.")
        print(f"   -> OK: Edad calculada para fecha futura: {edad}")

    def test_fix_strip_espacios_telefono(self):
        """Verifica que el Controlador limpie espacios (' 123 ') antes de validar."""
        print("[TEST] Validación de limpieza de espacios (strip) en inputs...")
        
        # 1. INICIALIZACIÓN: Crear las instancias de los Mocks
        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        
        # 2. CONFIGURACIÓN PREVIA (CRÍTICO PARA EL CONSTRUCTOR)
        # Esto soluciona el TypeError: '>' not supported... en _cargar_programas
        mock_vista.programa_combo.count.return_value = 0
        
        # 3. INYECCIÓN: Crear el controlador (Vista primero, Modelo después)
        # Al instanciar, el controlador usará la configuración del paso 2 inmediatamente.
        controlador = ControladorRegistro(mock_vista, mock_modelo)
        
        # 4. CONFIGURACIÓN DE REGLAS DE NEGOCIO (CRÍTICO PARA REGISTRAR)
        # Esto soluciona el TypeError: cannot unpack non-iterable NoneType object
        # Simulamos que hay cupo, la edad es válida y se seleccionó un horario.
        mock_vista.horario_combo.currentData.return_value = 1
        mock_modelo.obtener_rango_edad_clase.return_value = None  # Sin restricción estricta
        mock_modelo.obtener_capacidad_clase.return_value = 20
        mock_modelo.contar_alumnos_en_clase.return_value = 0
        
        # 5. PREPARACIÓN DE DATOS SUCIOS
        datos_sucios = {
            'nombre': 'Juan ',      
            'apellido': ' Perez',   
            'edad': '10',
            'telefono': ' 6621234567 ', # Espacios a limpiar
            'telefono2': '',
            'fecha_nacimiento': '2014-01-01',
            'observaciones': '',
            'estado': 'Activo',
            'nivel': 'Básico',
            'id_clase': 1
        }
        
        mock_vista.obtener_datos_formulario.return_value = datos_sucios
        mock_vista.validar_campos.return_value = True 
        
        # 6. EJECUCIÓN
        controlador.registrar_alumno()
        
        # 7. VERIFICACIÓN
        # El controlador usa argumentos nombrados (nombre=..., etc.), por lo que args está vacío.
        # Debemos extraer los datos desde kwargs (el segundo valor retornado por call_args).
        _, kwargs = mock_modelo.insertar_alumno.call_args
        
        telefono_enviado = kwargs['telefono']
        nombre_enviado = kwargs['nombre']
        
        self.assertEqual(telefono_enviado, "6621234567", f"FALLO: Teléfono enviado sucio: '{telefono_enviado}'")
        self.assertEqual(nombre_enviado, "Juan", f"FALLO: Nombre enviado sucio: '{nombre_enviado}'")
        print("   -> OK: Los datos fueron limpiados correctamente con .strip()")

    def test_integridad_base_datos(self):
        """Verifica inserción y recuperación básica."""
        print("[TEST] Integridad CRUD básica...")
        id_nuevo = self.db.insertar_alumno(
            "Test", "User", 10, "6620000000", "", "2014-01-01", "Obs", "Activo", "1", 1
        )
        self.assertIsNotNone(id_nuevo)
        
        alumno = self.db.obtener_alumno_por_id(id_nuevo)
        self.assertEqual(alumno['NOMBRE'], "Test")
        print("   -> OK: Inserción y lectura correctas.")
        
    # ====================================================================
    # PRUEBAS DE REGLAS DE NEGOCIO Y SEGURIDAD (Obligatorias para Proyecto Final)
    # ====================================================================

    def test_validacion_clase_llena(self):
        """Verifica que NO se registre un alumno si la clase no tiene cupo."""
        print("[TEST] Regla de Negocio: Bloqueo por cupo lleno...")
        
        # 1. Configuración
        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        mock_vista.programa_combo.count.return_value = 0
        controlador = ControladorRegistro(mock_vista, mock_modelo)
        
        # 2. Escenario: Clase LLENA (20/20)
        mock_vista.horario_combo.currentData.return_value = 1
        mock_modelo.obtener_capacidad_clase.return_value = 20
        mock_modelo.contar_alumnos_en_clase.return_value = 20  
        mock_modelo.obtener_rango_edad_clase.return_value = None 

        # Datos válidos
        datos = {
            'nombre': 'Alumno', 'apellido': 'Extra', 'edad': '10',
            'telefono': '123', 'telefono2': '', 'fecha_nacimiento': '2014-01-01',
            'observaciones': '', 'estado': 'Activo', 'nivel': 'Básico', 'id_clase': 1
        }
        mock_vista.obtener_datos_formulario.return_value = datos
        mock_vista.validar_campos.return_value = True

        # 3. Ejecución
        controlador.registrar_alumno()

        # 4. Verificación
        # NO debe guardar en BD
        mock_modelo.insertar_alumno.assert_not_called()
        
        # Debe mostrar mensaje de error de CUPO
        mock_vista.mostrar_mensaje.assert_called()
        args_msg, _ = mock_vista.mostrar_mensaje.call_args
        # Validamos que el mensaje mencione que está llena
        self.assertIn("llena", args_msg[0].lower()) 
        print("   -> OK: El sistema impidió el registro en una clase llena.")

    def test_seguridad_inyeccion_sql(self):
        """Verifica que caracteres peligrosos sean bloqueados por el Regex."""
        print("[TEST] Seguridad: Resistencia a SQL Injection en inputs...")
        
        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        mock_vista.programa_combo.count.return_value = 0
        controlador = ControladorRegistro(mock_vista, mock_modelo)

        # Escenario válido lógicamente
        mock_vista.horario_combo.currentData.return_value = 1
        mock_modelo.obtener_capacidad_clase.return_value = 20
        mock_modelo.contar_alumnos_en_clase.return_value = 0
        mock_modelo.obtener_rango_edad_clase.return_value = None

        # Payload malicioso
        nombre_hacker = "Robert'); DROP TABLE ALUMNOS; --"
        
        datos = {
            'nombre': nombre_hacker, 
            'apellido': 'Hacker', 'edad': '10', 'telefono': '123', 
            'telefono2': '', 'fecha_nacimiento': '2014-01-01',
            'observaciones': '', 'estado': 'Activo', 'nivel': 'Básico', 'id_clase': 1
        }
        mock_vista.obtener_datos_formulario.return_value = datos
        mock_vista.validar_campos.return_value = True

        controlador.registrar_alumno()

        # 4. Verificación
        # El controlador tiene un Regex que detecta ';' y ')', por lo que DEBE BLOQUEAR antes de llamar al modelo.
        mock_modelo.insertar_alumno.assert_not_called()
        
        # Debe mostrar mensaje de "caracteres inválidos"
        mock_vista.mostrar_mensaje.assert_called()
        args_msg, _ = mock_vista.mostrar_mensaje.call_args
        self.assertIn("caracteres inválidos", args_msg[0])
        
        print("   -> OK: El sistema bloqueó la inyección SQL mediante validación de Input (Regex).")

    def test_validacion_edad_advertencia(self):
        """Verifica el flujo cuando la edad no coincide con la clase (Usuario dice NO)."""
        print("[TEST] Regla de Negocio: Advertencia de rango de edad...")
        
        from PySide6.QtWidgets import QMessageBox # Necesario para el mock

        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        mock_vista.programa_combo.count.return_value = 0
        controlador = ControladorRegistro(mock_vista, mock_modelo)

        # Configurar validaciones
        mock_vista.horario_combo.currentData.return_value = 1
        
        # Simulamos que la clase es para bebés (0-3 años) pero el niño tiene 10 años
        # obtener_rango_edad_clase retorna (min, max) en meses
        mock_modelo.obtener_rango_edad_clase.return_value = (0, 36) 
        
        # El método db._calcular_edad_meses será llamado internamente o calculado en controlador.
        # Si tu controlador calcula la edad, nos aseguramos que detecte el fallo.
        
        datos = {
            'nombre': 'Juan', 'apellido': 'Perez', 
            'edad': '10', # 120 meses
            'telefono': '123', 'telefono2': '', 'fecha_nacimiento': '2014-01-01',
            'observaciones': '', 'estado': 'Activo', 'nivel': 'Básico', 'id_clase': 1
        }
        mock_vista.obtener_datos_formulario.return_value = datos
        mock_vista.validar_campos.return_value = True

        # SIMULAMOS QUE EL USUARIO DICE "NO" EN EL POPUP (QMessageBox.No)
        # Debemos "parchear" QMessageBox dentro del contexto del test si es posible,
        # o mockear la llamada en la vista si el controlador delega.
        # Dado que en tu código usas QMessageBox.question(self.vista, ...), 
        # lo ideal es mockear la clase QMessageBox globalmente o la interacción.
        # Para simplificar en este nivel sin librerías extra complejas, asumimos que
        # si falla la edad, el controlador podría abortar si el mock de question retorna No.
        
        # Truco para mockear QMessageBox importado en el controlador:
        with unittest.mock.patch('controlador.controlador_registro.QMessageBox') as MockQMB:
            MockQMB.question.return_value = MockQMB.No # El usuario rechaza
            MockQMB.Yes = 16384
            MockQMB.No = 65536
            
            controlador.registrar_alumno()
            
            # NO debe guardar
            mock_modelo.insertar_alumno.assert_not_called()
            print("   -> OK: El usuario canceló el registro por advertencia de edad.")
            
        # ====================================================================
    # PRUEBAS DE ADMINISTRACIÓN Y OPERACIONES MASIVAS
    # ====================================================================

    def test_gestion_maestros_validacion(self):
        """Verifica que NO se cree un maestro si el nombre está vacío."""
        print("[TEST] Administración: Validación de entrada en Maestros...")
        
        # Necesitamos importar la clase localmente o al inicio
        from controlador.controlador_maestros import ControladorMaestros
        
        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        
        controlador = ControladorMaestros(mock_vista, mock_modelo)
        
        # Intento de agregar sin nombre
        controlador.agregar_maestro("", "6621234567")
        
        # Verificación
        mock_modelo.insertar_maestro.assert_not_called()
        mock_vista.mostrar_mensaje.assert_called_with('El nombre es obligatorio.')
        print("   -> OK: El sistema rechazó un instructor sin nombre.")

    def test_clase_extra_individual(self):
        """Verifica la lógica de otorgar clase extra (reposición)."""
        print("[TEST] Regla de Negocio: Otorgar clase extra individual...")
        
        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        mock_vista.programa_combo.count.return_value = 0
        
        # Parcheamos QMessageBox
        with unittest.mock.patch('controlador.controlador_alumnos.QMessageBox') as MockQMB:
            # 1. Definir CONSTANTES
            MockQMB.Yes = 16384
            MockQMB.No = 65536
            
            # 2. Configurar el retorno del diálogo (Usuario dice SÍ)
            MockQMB.question.return_value = MockQMB.Yes 
            
            from controlador.controlador_alumnos import ControladorAlumnos
            controlador_alum = ControladorAlumnos(mock_vista, mock_modelo)
            
            # 3. [CORRECCIÓN CRÍTICA] Simular la respuesta de la Base de Datos
            # El controlador hace: resultado = self.modelo.cursor.fetchone()
            # resultado[0] debe ser 55. Por tanto, fetchone debe retornar una lista/tupla [55].
            mock_modelo.cursor.fetchone.return_value = [55] 
            
            # Entrenar al método de actualización para que devuelva True (éxito)
            mock_modelo.agregar_clase_extra_individual.return_value = True
            
            # Ejecución
            controlador_alum.otorgar_clase_extra(101) 
            
            # Verificación
            mock_modelo.agregar_clase_extra_individual.assert_called_with(55)
            print("   -> OK: Se procesó la reposición de clase correctamente.")

    def test_operacion_masiva_clases(self):
        """Verifica el manejo de errores parciales en operaciones grupales."""
        print("[TEST] Estrés: Operación masiva (Clases extra grupales)...")
        
        from controlador.controlador_alumnos import ControladorAlumnos
        mock_vista = MagicMock()
        mock_modelo = MagicMock()
        
        with unittest.mock.patch('controlador.controlador_alumnos.QMessageBox') as MockQMB:
            # 1. Definir CONSTANTES primero
            MockQMB.Yes = 16384
            MockQMB.warning.return_value = None # Warning no retorna nada importante
            
            # 2. Configurar retorno
            MockQMB.question.return_value = MockQMB.Yes
            
            controlador = ControladorAlumnos(mock_vista, mock_modelo)
            
            # Escenario: 3 clases
            def side_effect_agregar(id_clase, motivo):
                return id_clase != 2 # La 2 falla
            
            mock_modelo.agregar_clase_extra_grupo.side_effect = side_effect_agregar
            
            # Validaciones lógicas para que entre al bucle
            mock_modelo.existe_clase.return_value = True
            mock_modelo.contar_alumnos_en_clase.return_value = 10 
            
            # Ejecutar
            controlador.otorgar_clase_extra_grupo_multiple([1, 2, 3])
            
            # Verificar
            self.assertEqual(mock_modelo.agregar_clase_extra_grupo.call_count, 3)
            
            # Verificar mensaje de error parcial
            MockQMB.warning.assert_called()
            args_warning, _ = MockQMB.warning.call_args
            mensaje_mostrado = args_warning[2] 
            
            self.assertIn("Clases con errores: 1", mensaje_mostrado)
            print("   -> OK: El sistema manejó correctamente un fallo parcial en operación masiva.")

if __name__ == '__main__':
    unittest.main()