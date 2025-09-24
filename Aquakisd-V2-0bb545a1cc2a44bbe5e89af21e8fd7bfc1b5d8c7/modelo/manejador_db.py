# modelo/manejador_db.py
# Aquí irá la clase para manejar la base de datos
import sqlite3
from datetime import datetime, timedelta
import math
import re

class ManejadorDB:
    def __init__(self, db_path='aquakids.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.conectar()

    def conectar(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        # Asegurar que la columna NIVEL exista en la tabla ALUMNOS (migración ligera)
        try:
            self._ensure_nivel_column()
        except Exception:
            pass
        # Asegurar existencia de tabla INSCRIPCIONES para gestionar inscripciones y expiraciones
        try:
            self._ensure_inscripciones_table()
            self._ensure_clases_restantes_column()
            self._ensure_fecha_fin_column()  
        except Exception:
            pass

    def _ensure_nivel_column(self):
        """Agrega la columna NIVEL a ALUMNOS si no existe."""
        self.cursor.execute("PRAGMA table_info(ALUMNOS)")
        cols = [r[1] for r in self.cursor.fetchall()]
        if 'NIVEL' not in cols:
            try:
                self.cursor.execute('ALTER TABLE ALUMNOS ADD COLUMN NIVEL TEXT')
                self.conn.commit()
            except Exception:
                # Si no se puede alterar (por permisos o sqlite antiguo), ignorar y seguir
                pass

    def _ensure_clases_restantes_column(self):
        """Agrega la columna CLASES_RESTANTES a INSCRIPCIONES si no existe."""
        self.cursor.execute("PRAGMA table_info(INSCRIPCIONES)")
        cols = [r[1] for r in self.cursor.fetchall()]
        if 'CLASES_RESTANTES' not in cols:
            try:
                self.cursor.execute('ALTER TABLE INSCRIPCIONES ADD COLUMN CLASES_RESTANTES INTEGER')
                self.conn.commit()
            except Exception:
                pass

    def _ensure_inscripciones_table(self):
        """Crea la tabla INSCRIPCIONES si no existe.

        Campos mínimos: ID_INSCRIPCION, ID_ALUMNO, ID_PROGRAMA, ID_CLASE, FECHA_INICIO, NUM_CLASES, ESTADO
        """
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS INSCRIPCIONES (
                    ID_INSCRIPCION INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_ALUMNO INTEGER NOT NULL,
                    ID_PROGRAMA INTEGER,
                    ID_CLASE INTEGER,
                    FECHA_INICIO TEXT NOT NULL,
                    NUM_CLASES INTEGER,
                    CLASES_RESTANTES INTEGER,
                    ESTADO TEXT DEFAULT 'Activo',
                    FOREIGN KEY(ID_ALUMNO) REFERENCES ALUMNOS(ID_ALUMNO),
                    FOREIGN KEY(ID_CLASE) REFERENCES CLASES(ID_CLASE)
                )
            """)
            self.conn.commit()
        except Exception:
            # Si falla la migración, no interrumpir la ejecución principal
            pass

    def calcular_fecha_vencimiento(self, fecha_inicio_str, num_clases, dias_str):
        """Calcula la fecha de vencimiento (ISO yyyy-MM-dd) de una inscripción.

        - fecha_inicio_str: string en formato 'yyyy-MM-dd' o compatible con datetime.fromisoformat
        - num_clases: int (número total de clases contratadas)
        - dias_str: string con días separados por comas (ej: 'Lunes,Miercoles')
        """
        try:
            if not fecha_inicio_str:
                return None
            # parse date
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio_str)
            except Exception:
                # fallback: try parsing date only
                fecha_inicio = datetime.strptime(fecha_inicio_str.split(' ')[0], '%Y-%m-%d')

            sesiones = 1
            if dias_str:
                try:
                    # soportar varios separadores: comas, ' y ', 'and', '/', '&'
                    partes = self._split_days(dias_str)
                    sesiones = max(1, len(partes))
                except Exception:
                    sesiones = 1

            if not num_clases or int(num_clases) <= 0:
                return None

            semanas = math.ceil(int(num_clases) / sesiones)
            fecha_venc = fecha_inicio + timedelta(weeks=semanas)
            return fecha_venc.date().isoformat()
        except Exception:
            return None

    def obtener_alumnos_vencimiento_proximo(self, dias_avisar=7):
        """Devuelve lista de inscripciones activas cuyo vencimiento cae en los próximos `dias_avisar` días.

        Retorna lista de dicts con keys: id_alumno, nombre_completo, id_inscripcion, id_programa, id_clase,
        fecha_inicio, num_clases, sesiones_semana, fecha_vencimiento
        """
        results = []
        try:
            # Seleccionar inscripciones activas y datos relacionados
            self.cursor.execute('''
                SELECT I.ID_INSCRIPCION, I.ID_ALUMNO, I.ID_PROGRAMA, I.ID_CLASE, I.FECHA_INICIO, I.NUM_CLASES,
                       A.NOMBRE, A.APELLIDO, C.DIAS_DE_CLASES
                FROM INSCRIPCIONES I
                LEFT JOIN ALUMNOS A ON A.ID_ALUMNO = I.ID_ALUMNO
                LEFT JOIN CLASES C ON C.ID_CLASE = I.ID_CLASE
                WHERE (I.ESTADO IS NULL OR I.ESTADO = 'Activo')
                      AND (A.ESTADO IS NULL OR A.ESTADO = 'Activo')
            ''')
            rows = self.cursor.fetchall()
            now = datetime.now().date()
            limite = now + timedelta(days=dias_avisar)
            for id_ins, id_alum, id_prog, id_clase, fecha_inicio, num_clases, nombre, apellido, dias_clase in rows:
                fecha_venc = self.calcular_fecha_vencimiento(fecha_inicio, num_clases, dias_clase)
                if not fecha_venc:
                    continue
                try:
                    fv = datetime.fromisoformat(fecha_venc).date()
                except Exception:
                    continue
                if now <= fv <= limite:
                    sesiones = 1
                    try:
                        sesiones = max(1, len(self._split_days(dias_clase)))
                    except Exception:
                        sesiones = 1
                    results.append({
                        'id_alumno': id_alum,
                        'nombre_completo': (nombre or '') + ' ' + (apellido or ''),
                        'id_inscripcion': id_ins,
                        'id_programa': id_prog,
                        'id_clase': id_clase,
                        'fecha_inicio': fecha_inicio,
                        'num_clases': num_clases,
                        'sesiones_semana': sesiones,
                        'fecha_vencimiento': fecha_venc
                    })
        except Exception:
            # en caso de fallo, devolver lista vacía
            return []
        return results

 # En modelo/manejador_db.py

# En modelo/manejador_db.py

    def reinscribir_inscripcion(self, id_inscripcion):
        """
        Reinscribe al alumno, actualizando la fecha de inicio a hoy,
        sumando el número de clases del programa y recalculando la fecha de fin.
        """
        try:
        # 1. Obtener datos de la inscripción y clase asociada
            self.cursor.execute("""
                SELECT I.ID_PROGRAMA, I.ID_CLASE, C.DIAS_DE_CLASES
                FROM INSCRIPCIONES I
                JOIN CLASES C ON I.ID_CLASE = C.ID_CLASE
                WHERE I.ID_INSCRIPCION = ?
            """, (id_inscripcion,))
            resultado_inscripcion = self.cursor.fetchone()
            if not resultado_inscripcion:
                raise ValueError(f"No se encontró la inscripción con ID {id_inscripcion}")

            id_programa, id_clase, dias_clase = resultado_inscripcion

            # 2. Obtener el NUM_CLASES del programa
            self.cursor.execute("SELECT NUM_CLASES FROM PROGRAMA WHERE ID_PROGRAMA = ?", (id_programa,))
            resultado_programa = self.cursor.fetchone()
        
            # Si el programa no tiene un número de clases, usamos 10 como valor por defecto
            if not resultado_programa or resultado_programa[0] is None:
                num_clases_a_sumar = 10
                print(f"Advertencia: El programa con ID {id_programa} no tiene un número de clases definido. Se usarán 10 clases por defecto.")
            else:
                num_clases_a_sumar = resultado_programa[0]

            # 3. Calcular la nueva fecha de fin
            fecha_inicio_hoy = datetime.now().strftime('%Y-%m-%d')
            nueva_fecha_fin = self.calcular_fecha_vencimiento(fecha_inicio_hoy, num_clases_a_sumar, dias_clase)

            # 4. Actualizar la inscripción con los nuevos valores
            self.cursor.execute("""
                UPDATE INSCRIPCIONES
                SET FECHA_INICIO = ?,
                    CLASES_RESTANTES = COALESCE(CLASES_RESTANTES, 0) + ?,
                    FECHA_FIN = ?
                WHERE ID_INSCRIPCION = ?
            """, (fecha_inicio_hoy, num_clases_a_sumar, nueva_fecha_fin, id_inscripcion))
        
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error al reinscribir la inscripción: {e}")
            self.conn.rollback() # Revertir cambios en caso de error
            return False

    def baja_alumno(self, id_alumno):
        """Marca al alumno como Inactivo y cierra sus inscripciones activas."""
        try:
        # Ambas actualizaciones son parte de una misma transacción
            self.cursor.execute("UPDATE ALUMNOS SET ESTADO = 'Inactivo' WHERE ID_ALUMNO = ?", (id_alumno,))
            self.cursor.execute("UPDATE INSCRIPCIONES SET ESTADO = 'Baja' WHERE ID_ALUMNO = ? AND (ESTADO IS NULL OR ESTADO = 'Activo')", (id_alumno,))
        
        # Si todo sale bien, guarda los cambios
            self.conn.commit()
            return True
        except Exception as e:
        # Si algo falla, imprime el error real y revierte los cambios
            print(f"ERROR al dar de baja al alumno ID {id_alumno}: {e}")
            self.conn.rollback() # Revierte cualquier cambio parcial para no dejar la DB inconsistente
        return False

    def cerrar(self):
        if self.conn:
            self.conn.close()

    def insertar_alumno(self, nombre, apellido, edad, telefono, telefono2, fecha_nacimiento, observaciones, estado, nivel, id_clase):
        """Inserta un nuevo alumno en la base de datos."""
        if id_clase is None:
            raise ValueError("Debe proporcionarse un id_clase para registrar al alumno.")

        # Insertar usando la FK hacia CLASES (ID_CLASEFK)
        # Insertar incluyendo NIVEL (columna añadida si es necesario por _ensure_nivel_column)
        self.cursor.execute('''
            INSERT INTO ALUMNOS (NOMBRE, APELLIDO, EDAD, TELEFONO, TELEFONO2, FECHA_DE_NACIMIENTO, OBSERVACIONES, ESTADO, NIVEL, ID_CLASEFK)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, apellido, edad, telefono, telefono2, fecha_nacimiento, observaciones, estado, nivel, id_clase))
        self.conn.commit()
        return self.cursor.lastrowid

    def obtener_programas(self):
        self.cursor.execute('SELECT ID_PROGRAMA, NOMBRE_PROGRAMA FROM PROGRAMA')
        return self.cursor.fetchall()

    def obtener_dias_para_programa(self, id_programa):
        """Devuelve la lista de días (texto) disponibles para un programa dado."""
        # Algunos programas (3 y 6) deben tomar las clases/días de los programas 7 y 8.
        # Normalizar la consulta para devolver los días asociados a 7 y 8 si se solicita 3 o 6.
        if id_programa in (3, 6):
            # Usar IN (7,8)
            self.cursor.execute('''
                SELECT DISTINCT DIAS_DE_CLASES FROM CLASES WHERE ID_PROGRAMAFK IN (?, ?)
            ''', (7, 8))
        else:
            self.cursor.execute('''
                SELECT DISTINCT DIAS_DE_CLASES FROM CLASES WHERE ID_PROGRAMAFK = ?
            ''', (id_programa,))
        return [row[0] for row in self.cursor.fetchall()]

    def obtener_clases_por_programa_y_dia(self, id_programa, dias):
        """Devuelve filas de clases para un programa y día: (ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD)."""
        # Si piden los datos para 3 o 6, devolver las clases que pertenecen a 7 y 8
        if id_programa in (3, 6):
            self.cursor.execute('''
                SELECT ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD FROM CLASES
                WHERE ID_PROGRAMAFK IN (?, ?) AND DIAS_DE_CLASES = ?
            ''', (7, 8, dias))
        else:
            self.cursor.execute('''
                SELECT ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD FROM CLASES
                WHERE ID_PROGRAMAFK = ? AND DIAS_DE_CLASES = ?
            ''', (id_programa, dias))
        return self.cursor.fetchall()

    def obtener_rango_edad_clase(self, id_clase):
        """Devuelve una tupla (EDAD_MIN, EDAD_MAX) para la clase especificada en meses.

        Retorna None si la clase no existe o no tiene esos campos.
        """
        self.cursor.execute('SELECT EDAD_MIN, EDAD_MAX FROM CLASES WHERE ID_CLASE = ?', (id_clase,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return (row[0], row[1])

    def contar_alumnos_en_clase(self, id_clase):
                # Contar sólo los alumnos activos o no en estado de lista de espera/prioridad.
                # De esta manera los alumnos en 'Lista De Espera' o 'Prioridad' no ocupan cupo.
                self.cursor.execute('''
                        SELECT COUNT(*) FROM ALUMNOS
                        WHERE ID_CLASEFK = ?
                            AND (ESTADO IS NULL OR ESTADO NOT IN ('Lista De Espera', 'Prioridad'))
                ''', (id_clase,))
                row = self.cursor.fetchone()
                return row[0] if row else 0

    def obtener_capacidad_clase(self, id_clase):
        self.cursor.execute('SELECT CAPACIDAD FROM CLASES WHERE ID_CLASE = ?', (id_clase,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def restar_capacidad_clase(self, id_clase, cantidad):
        """Resta la cantidad indicada a la columna CAPACIDAD de la clase.

        No valida límites (puede quedar negativa si así se requiere por la regla).
        """
        try:
            self.cursor.execute('UPDATE CLASES SET CAPACIDAD = CAPACIDAD - ? WHERE ID_CLASE = ?', (cantidad, id_clase))
            self.conn.commit()
        except Exception:
            # Si falla, no interrumpir el flujo principal; levantaré la excepción arriba si es crítico.
            pass

    # Métodos para manejar maestros
    def listar_maestros(self):
        """Devuelve lista de maestros: (ID_MAESTRO, NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO)"""
        self.cursor.execute('SELECT ID_MAESTRO, NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO FROM MAESTROS')
        return self.cursor.fetchall()

    def buscar_maestros_por_nombre(self, query):
        """Busca maestros por nombre (LIKE) y retorna filas como listar_maestros."""
        like = f"%{query}%"
        self.cursor.execute('''
            SELECT ID_MAESTRO, NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO FROM MAESTROS
            WHERE NOMBRE_MAESTRO LIKE ?
        ''', (like,))
        return self.cursor.fetchall()

    def insertar_maestro(self, nombre, telefono, estado='Activo'):
        self.cursor.execute('''
            INSERT INTO MAESTROS (NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO)
            VALUES (?, ?, ?)
        ''', (nombre, telefono, estado))
        self.conn.commit()
        return self.cursor.lastrowid

    def actualizar_maestro(self, id_maestro, nombre, telefono, estado):
        self.cursor.execute('''
            UPDATE MAESTROS SET NOMBRE_MAESTRO = ?, NUMERO_DE_TELEFONO = ?, ESTADO = ?
            WHERE ID_MAESTRO = ?
        ''', (nombre, telefono, estado, id_maestro))
        self.conn.commit()

    # Métodos para manejar alumnos (consultas/filtrado)
    def listar_alumnos(self, estado=None):
        """Devuelve lista de alumnos con información básica, incluyendo Observaciones.
        Si estado es 'Activo' o 'Inactivo' filtra por ese estado; None devuelve todos.
        Retorna filas: (ID_ALUMNO, NOMBRE, APELLIDO, EDAD, TELEFONO, TELEFONO2, FECHA_DE_NACIMIENTO, NOMBRE_PROGRAMA, OBSERVACIONES, ESTADO)
        """
        # Código Corregido
        sql = '''
            SELECT A.ID_ALUMNO,
                A.NOMBRE,
                A.APELLIDO,
                A.EDAD,
                A.TELEFONO,
                A.TELEFONO2,
                A.FECHA_DE_NACIMIENTO,
                P.NOMBRE_PROGRAMA,
                A.OBSERVACIONES,
                A.ESTADO,
                I.FECHA_INICIO,
                I.FECHA_FIN
            FROM ALUMNOS A
            LEFT JOIN CLASES C ON A.ID_CLASEFK = C.ID_CLASE
            LEFT JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
            LEFT JOIN INSCRIPCIONES I ON A.ID_ALUMNO = I.ID_ALUMNO AND I.ESTADO = 'Activo'
        '''
        params = []
        if estado in ('Activo', 'Inactivo'):
            sql += ' WHERE ESTADO = ?'
            params.append(estado)
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def buscar_alumnos(self, query=None, estado=None, id_programa=None, id_clase=None, edad=None):
        sql = '''
            SELECT A.ID_ALUMNO,
                   A.NOMBRE,
                   A.APELLIDO,
                   A.EDAD,
                   A.TELEFONO,
                   A.TELEFONO2,
                   A.FECHA_DE_NACIMIENTO,
                   P.NOMBRE_PROGRAMA,
                   A.OBSERVACIONES,
                   A.ESTADO,
                   I.FECHA_INICIO,
                   I.FECHA_FIN
            FROM ALUMNOS A
            LEFT JOIN CLASES C ON A.ID_CLASEFK = C.ID_CLASE
            LEFT JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
            LEFT JOIN INSCRIPCIONES I ON A.ID_ALUMNO = I.ID_ALUMNO AND I.ESTADO = 'Activo'
        '''
        where = []
        params = []
        if query:
            like = f"%{query}%"
            where.append('(CAST(A.ID_ALUMNO AS TEXT) LIKE ? OR A.NOMBRE LIKE ? OR A.APELLIDO LIKE ? OR A.TELEFONO LIKE ?)')
            params.extend([like, like, like, like])
        if estado:
            if isinstance(estado, (list, tuple)):
                if len(estado) > 0:
                    placeholders = ','.join('?' for _ in estado)
                    where.append(f'A.ESTADO IN ({placeholders})')
                    params.extend(estado)
            else:
                where.append('A.ESTADO = ?')
                params.append(estado)
        if id_programa:
            where.append('C.ID_PROGRAMAFK = ?')
            params.append(id_programa)
        if id_clase:
            where.append('A.ID_CLASEFK = ?')
            params.append(id_clase)
        if edad is not None:
            edad_min = edad * 12
            edad_max = edad_min + 11
            where.append('A.EDAD BETWEEN ? AND ?')
            params.extend([edad_min, edad_max])
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        
        # LÍNEA CORREGIDA: Se eliminó GROUP BY A.ID_ALUMNO
        sql += ' ORDER BY CASE WHEN A.ESTADO = \'Prioridad\' THEN 1 WHEN A.ESTADO = \'Lista De Espera\' THEN 2 ELSE 3 END, A.NOMBRE, A.APELLIDO'
        
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()
    
    def obtener_alumno_por_id(self, alumno_id):
        """
        Obtiene todos los datos de un alumno por su ID y los devuelve en un diccionario.
        """
        self.cursor.execute('SELECT * FROM ALUMNOS WHERE ID_ALUMNO = ?', (alumno_id,))
        row = self.cursor.fetchone()
        if row:
            column_names = [description[0] for description in self.cursor.description]
            return dict(zip(column_names, row))
        return None

    def actualizar_alumno(self, alumno_id, datos_actualizados):
        id_clase_actual = None
        self.cursor.execute('SELECT ID_CLASEFK FROM ALUMNOS WHERE ID_ALUMNO = ?', (alumno_id,))
        row = self.cursor.fetchone()
        if row:
            id_clase_actual = row[0]

        if datos_actualizados['estado'] == 'Inactivo' and id_clase_actual:
            datos_actualizados['id_clasefk'] = None

        """
        Actualiza los datos de un alumno en la base de datos.
        """
        sql = '''
            UPDATE ALUMNOS SET
                NOMBRE = ?, APELLIDO = ?, EDAD = ?,
                TELEFONO = ?, TELEFONO2 = ?, FECHA_DE_NACIMIENTO = ?, OBSERVACIONES = ?,
                ESTADO = ?, NIVEL = ?, ID_CLASEFK = ?
            WHERE ID_ALUMNO = ?
        '''
        self.cursor.execute(sql, (
            datos_actualizados['nombre'],
            datos_actualizados['apellido'],
            datos_actualizados['edad'],
            datos_actualizados['telefono'],
            datos_actualizados['telefono2'],
            datos_actualizados['fecha_de_nacimiento'],
            datos_actualizados['observaciones'],
            datos_actualizados['estado'],
            datos_actualizados.get('nivel'),
            datos_actualizados['id_clasefk'],
            alumno_id
        ))
        self.conn.commit()

    def actualizar_estado_alumno(self, alumno_id, nuevo_estado):
        """Actualiza el estado de un alumno específico."""
        self.cursor.execute('UPDATE ALUMNOS SET ESTADO = ? WHERE ID_ALUMNO = ?', (nuevo_estado, alumno_id))
        self.conn.commit()
    

    def obtener_clases_y_descripcion(self):
        self.cursor.execute('SELECT ID_CLASE, DIAS_DE_CLASES || " - " || HORA_INICIO, ID_PROGRAMAFK FROM CLASES')
        return self.cursor.fetchall()

    def mapear_programa_a_ids(self, id_prog=None, nombre_prog=''):
        """Devuelve una tupla de id_programa a usar para consultas, aplicando reglas de mapeo.

        Reglas actuales:
        - Si el nombre coincide con 'PROGRAMA BEBÉS PERSONALIZADO ENTRE SEMANA' -> usar (2,)
        - Si id_prog es 3 -> usar (7,8)
        - Si id_prog es 6 -> usar (7,8)
        - En otro caso devolver (id_prog,) si no es None, o () si es None
        """
        try:
            nombre = (nombre_prog or '').strip().upper()
        except Exception:
            nombre = ''
        if nombre == 'PROGRAMA BEBÉS PERSONALIZADO ENTRE SEMANA':
            return (2,)
        try:
            pid = int(id_prog)
        except Exception:
            pid = id_prog
        if pid in (3, 6):
            return (7, 8)
        if pid is None:
            return ()
        return (pid,)

    def obtener_dias_para_programas(self, program_ids):
        """Devuelve lista de días distintos para los programas indicados (program_ids debe ser iterable)."""
        if not program_ids:
            return []
        placeholders = ','.join(['?'] * len(program_ids))
        sql = f'SELECT DISTINCT DIAS_DE_CLASES FROM CLASES WHERE ID_PROGRAMAFK IN ({placeholders})'
        self.cursor.execute(sql, tuple(program_ids))
        return [row[0] for row in self.cursor.fetchall()]

    def obtener_clases_por_programas_y_dia(self, program_ids, dias):
        """Devuelve filas de clases para los programas indicados y el día dado.

        Retorna tuplas (ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD, ID_PROGRAMAFK)
        """
        if not program_ids:
            return []
        placeholders = ','.join(['?'] * len(program_ids))
        sql = f'''
            SELECT ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD, ID_PROGRAMAFK FROM CLASES
            WHERE ID_PROGRAMAFK IN ({placeholders}) AND DIAS_DE_CLASES = ?
        '''
        params = tuple(program_ids) + (dias,)
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def _split_days(self, dias_str):
        """Normaliza y separa el texto de días en una lista.

        Acepta formatos como 'Lunes, Miércoles', 'Lunes y Miércoles', 'Lunes/Miércoles',
        y mezcla de separadores. Devuelve lista limpia de días.
        """
        if not dias_str:
            return []
        # Reemplazar conectores comunes por coma
        s = re.sub(r"\s*(?:,|y|and|&|/)\s*", ",", dias_str, flags=re.IGNORECASE)
        parts = [p.strip() for p in s.split(',') if p.strip()]
        return parts

    def obtener_clases_por_programas(self, program_ids):
        """Devuelve clases (ID_CLASE, 'DIAS - HORA', ID_PROGRAMAFK) para los programas indicados."""
        if not program_ids:
            return []
        placeholders = ','.join(['?'] * len(program_ids))
        sql = f'SELECT ID_CLASE, DIAS_DE_CLASES || " - " || HORA_INICIO AS DESCRIP, ID_PROGRAMAFK FROM CLASES WHERE ID_PROGRAMAFK IN ({placeholders})'
        self.cursor.execute(sql, tuple(program_ids))
        return self.cursor.fetchall()

    def obtener_clases_detalle_por_programas(self, program_ids):
        """Devuelve clases detalladas para los programas indicados:
        (ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK)
        """
        if not program_ids:
            return []
        placeholders = ','.join(['?'] * len(program_ids))
        sql = f'''
            SELECT ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK
            FROM CLASES
            WHERE ID_PROGRAMAFK IN ({placeholders})
        '''
        self.cursor.execute(sql, tuple(program_ids))
        return self.cursor.fetchall()

    def obtener_primera_clase_para_programa(self, id_programa):
        """Devuelve el ID_CLASE de la primera clase asociada a un programa dado,
        o None si no existe ninguna clase para ese programa.
        """
        self.cursor.execute('SELECT ID_CLASE FROM CLASES WHERE ID_PROGRAMAFK = ? LIMIT 1', (id_programa,))
        row = self.cursor.fetchone()
        return row[0] if row else None
    
    def crear_inscripcion(self, id_alumno, id_programa, id_clase, fecha_inicio):
        self.cursor.execute("SELECT NUM_CLASES FROM PROGRAMA WHERE ID_PROGRAMA = ?", (id_programa,))
        resultado = self.cursor.fetchone()
        if not resultado:
            raise ValueError(f"El programa con ID {id_programa} no existe o no tiene un número de clases definido.")
        
        num_clases_total = resultado[0]

        self.cursor.execute("SELECT DIAS_DE_CLASES FROM CLASES WHERE ID_CLASE = ?", (id_clase,))
        dias_clase_row = self.cursor.fetchone()
        dias_clase = dias_clase_row[0] if dias_clase_row else ""

        fecha_fin = self.calcular_fecha_vencimiento(fecha_inicio, num_clases_total, dias_clase)

        self.cursor.execute('''
            INSERT INTO INSCRIPCIONES (ID_ALUMNO, ID_PROGRAMA, ID_CLASE, FECHA_INICIO, FECHA_FIN, NUM_CLASES, CLASES_RESTANTES, ESTADO)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Activo')
        ''', (id_alumno, id_programa, id_clase, fecha_inicio, fecha_fin, num_clases_total, num_clases_total))
        
        self.conn.commit()
        return self.cursor.lastrowid

    def descontar_clases_asistidas(self):
        """
        Función clave para descontar clases. Se debe ejecutar una vez al día.
        Busca alumnos activos que tienen clase hoy, verifica que no se haya descontado
        la clase de hoy y actualiza sus clases restantes.
        """
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        hoy_str = datetime.now().strftime('%Y-%m-%d')
        dia_de_hoy = dias_semana[datetime.now().weekday()]

        # 1. Buscar inscripciones activas que tienen clase hoy
        query_alumnos_con_clase_hoy = f"""
            SELECT I.ID_INSCRIPCION, I.ID_ALUMNO, I.CLASES_RESTANTES
            FROM INSCRIPCIONES I
            JOIN CLASES C ON I.ID_CLASE = C.ID_CLASE
            WHERE I.ESTADO = 'Activo' AND C.DIAS_DE_CLASES LIKE '%{dia_de_hoy}%'
        """
        self.cursor.execute(query_alumnos_con_clase_hoy)
        inscripciones_a_procesar = self.cursor.fetchall()

        for id_inscripcion, id_alumno, clases_restantes in inscripciones_a_procesar:
            if clases_restantes is None or clases_restantes <= 0:
                continue

            # 2. Verificar que no se haya registrado asistencia hoy para esta inscripción
            self.cursor.execute(
                "SELECT ID_ASISTENCIA FROM ASISTENCIAS WHERE ID_INSCRIPCION = ? AND FECHA = ?",
                (id_inscripcion, hoy_str)
            )
            if self.cursor.fetchone():
                # Ya se descontó la clase de hoy, no hacer nada.
                continue

            # 3. Descontar la clase y registrar la asistencia
            nuevas_clases_restantes = clases_restantes - 1
            self.cursor.execute(
                "UPDATE INSCRIPCIONES SET CLASES_RESTANTES = ? WHERE ID_INSCRIPCION = ?",
                (nuevas_clases_restantes, id_inscripcion)
            )
            self.cursor.execute(
                "INSERT INTO ASISTENCIAS (ID_INSCRIPCION, FECHA) VALUES (?, ?)",
                (id_inscripcion, hoy_str)
            )
        
        self.conn.commit()
        print(f"Proceso de descuento de clases para el {hoy_str} completado.")

    def _ensure_fecha_fin_column(self):
        """Asegura que la columna FECHA_FIN exista en la tabla INSCRIPCIONES."""
        self.cursor.execute("PRAGMA table_info(INSCRIPCIONES)")
        cols = [r[1] for r in self.cursor.fetchall()]
        if 'FECHA_FIN' not in cols:
            try:
                self.cursor.execute('ALTER TABLE INSCRIPCIONES ADD COLUMN FECHA_FIN TEXT')
                self.conn.commit()
            except Exception as e:
                print(f"No se pudo agregar la columna FECHA_FIN: {e}")
    
    def obtener_alumnos_con_pocas_clases(self, umbral=4):
        """
        Obtiene los alumnos a quienes les quedan `umbral` o menos clases.
        Esta función alimentará la tabla de la ventana de inicio.
        """
        self.cursor.execute('''
            SELECT A.NOMBRE, A.APELLIDO, A.ID_ALUMNO, I.ID_INSCRIPCION, P.NOMBRE_PROGRAMA, I.CLASES_RESTANTES, C.DIAS_DE_CLASES
            FROM INSCRIPCIONES I
            JOIN ALUMNOS A ON I.ID_ALUMNO = A.ID_ALUMNO
            LEFT JOIN PROGRAMA P ON I.ID_PROGRAMA = P.ID_PROGRAMA
            LEFT JOIN CLASES C ON I.ID_CLASE = C.ID_CLASE
            WHERE I.ESTADO = 'Activo' AND I.CLASES_RESTANTES <= ?
            ORDER BY I.CLASES_RESTANTES ASC
        ''', (umbral,))
        return self.cursor.fetchall()