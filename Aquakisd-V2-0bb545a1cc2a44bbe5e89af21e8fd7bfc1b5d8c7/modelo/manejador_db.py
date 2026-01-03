# modelo/manejador_db.py
# Aquí irá la clase para manejar la base de datos
import sqlite3
from datetime import datetime, timedelta
import math
import re

from certifi import where

class ManejadorDB:
    def __init__(self, db_path='aquakids.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.conectar()

    def conectar(self):
        self.conn = sqlite3.connect(self.db_path, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
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
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_alumno_estado ON INSCRIPCIONES(ID_ALUMNO, ESTADO)")
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

    def reinscribir_inscripcion(self, id_inscripcion):
        """
        Reinscribe al alumno, sumando el número de clases del programa
        y recalculando la fecha de fin a partir de la fecha de fin existente o de hoy.
        """
        try:
            # 1. Obtener datos de la inscripción, incluyendo la fecha de fin actual
            self.cursor.execute("""
                SELECT I.ID_PROGRAMA, I.ID_CLASE, C.DIAS_DE_CLASES, I.FECHA_FIN
                FROM INSCRIPCIONES I
                JOIN CLASES C ON I.ID_CLASE = C.ID_CLASE
                WHERE I.ID_INSCRIPCION = ?
            """, (id_inscripcion,))
            resultado_inscripcion = self.cursor.fetchone()
            if not resultado_inscripcion:
                raise ValueError(f"No se encontró la inscripción con ID {id_inscripcion}")

            id_programa, id_clase, dias_clase, fecha_fin_actual_str = resultado_inscripcion

            # 2. Obtener el NUM_CLASES del programa
            self.cursor.execute("SELECT NUM_CLASES FROM PROGRAMA WHERE ID_PROGRAMA = ?", (id_programa,))
            resultado_programa = self.cursor.fetchone()

            if not resultado_programa or resultado_programa[0] is None:
                num_clases_a_sumar = 10
                print(f"Advertencia: El programa con ID {id_programa} no tiene un número de clases definido. Se usarán 10 clases por defecto.")
            else:
                num_clases_a_sumar = resultado_programa[0]

            # 3. Determinar la fecha de partida para el cálculo
            hoy = datetime.now().date()
            fecha_de_partida = hoy

            if fecha_fin_actual_str:
                try:
                    fecha_fin_actual = datetime.fromisoformat(fecha_fin_actual_str).date()
                    if fecha_fin_actual > hoy:
                        fecha_de_partida = fecha_fin_actual
                except (ValueError, TypeError):
                    # Si la fecha_fin_actual no es válida, simplemente usamos hoy
                    pass
        
            # 4. Calcular la nueva fecha de fin
            nueva_fecha_fin = self.calcular_fecha_vencimiento(
                fecha_de_partida.isoformat(), 
                num_clases_a_sumar, 
                dias_clase
            )

            # 5. Actualizar la inscripción
            self.cursor.execute("""
                UPDATE INSCRIPCIONES
                SET CLASES_RESTANTES = COALESCE(CLASES_RESTANTES, 0) + ?,
                    FECHA_FIN = ?
                WHERE ID_INSCRIPCION = ?
            """, (num_clases_a_sumar, nueva_fecha_fin, id_inscripcion))

            self.conn.commit()
            self.cursor.execute("SELECT ID_ALUMNO FROM INSCRIPCIONES WHERE ID_INSCRIPCION = ?", (id_inscripcion,))
            id_alumno_res = self.cursor.fetchone()
            if id_alumno_res:
                self.cursor.execute("SELECT NOMBRE_PROGRAMA FROM PROGRAMA WHERE ID_PROGRAMA = ?", (id_programa,))
                nombre_programa_res = self.cursor.fetchone()
                nombre_programa = nombre_programa_res[0] if nombre_programa_res else f"ID {id_programa}"
    
                self.cursor.execute("SELECT DIAS_DE_CLASES, HORA_INICIO FROM CLASES WHERE ID_CLASE = ?", (id_clase,))
                clase_res = self.cursor.fetchone()
                horario_clase = f"{clase_res[0]} - {clase_res[1]}" if clase_res else f"ID {id_clase}"
                
                detalles = f"Reinscrito en {nombre_programa}, horario: {horario_clase}."
                self.agregar_historial(id_alumno_res[0], "Reinscripción", detalles, fecha_inicio=fecha_de_partida.isoformat(), fecha_fin=nueva_fecha_fin)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error al reinscribir la inscripción: {e}")
            self.conn.rollback()
            return False

    def baja_alumno(self, id_alumno):
        """
        Marca 'Baja Pendiente' si tiene clases. Si no, 'Inactivo' directo.
        """
        try:
            # 1. Verificar si tiene clases pagadas pendientes
            self.cursor.execute("""
                SELECT SUM(CLASES_RESTANTES) FROM INSCRIPCIONES 
                WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'
            """, (id_alumno,))
            row = self.cursor.fetchone()
            total_clases = row[0] if row and row[0] else 0

            if total_clases > 0:
                # CASO A: Tiene saldo -> Baja Pendiente (Sigue entrando, sigue ocupando lugar)
                print(f"[Info] Alumno {id_alumno} tiene {total_clases} clases. Se marca como 'Baja Pendiente'.")
                self.cursor.execute("UPDATE ALUMNOS SET ESTADO = 'Baja Pendiente' WHERE ID_ALUMNO = ?", (id_alumno,))
                self.agregar_historial(id_alumno, "Baja Pendiente", f"Solicitó baja pero conserva {total_clases} clases.")
            else:
                # CASO B: No tiene saldo -> Baja Definitiva (Libera lugar inmediatamente)
                print(f"[Info] Alumno {id_alumno} sin clases. Baja definitiva.")
                self.cursor.execute("UPDATE ALUMNOS SET ESTADO = 'Inactivo' WHERE ID_ALUMNO = ?", (id_alumno,))
                self.cursor.execute("UPDATE INSCRIPCIONES SET ESTADO = 'Baja' WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'", (id_alumno,))
                self.agregar_historial(id_alumno, "Baja", "Baja definitiva (Sin clases pendientes).")
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"ERROR al dar de baja: {e}")
            self.conn.rollback()
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
        # 1. Verificar si la clase pertenece a un programa Privado (3 o 6) para contar doble
        self.cursor.execute("SELECT ID_PROGRAMAFK FROM CLASES WHERE ID_CLASE = ?", (id_clase,))
        prog_row = self.cursor.fetchone()
        factor = 2 if prog_row and prog_row[0] in (3, 6) else 1

        # 2. Contar alumnos físicos (Activos + Baja Pendiente)
        self.cursor.execute('''
                SELECT COUNT(*) FROM ALUMNOS
                WHERE ID_CLASEFK = ?
                    AND ESTADO IN ('Activo', 'Baja Pendiente')
        ''', (id_clase,))
        row = self.cursor.fetchone()
        
        # 3. Retornar ocupación real (Cantidad * Factor)
        return (row[0] if row else 0) * factor

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
    def listar_maestros(self, solo_activos=False): 
            """Devuelve lista de maestros: (ID_MAESTRO, NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO)"""
            sql = 'SELECT ID_MAESTRO, NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO FROM MAESTROS'
            params = []
            if solo_activos:
                sql += ' WHERE ESTADO = ?'
                params.append('Activo')
            sql += ' ORDER BY NOMBRE_MAESTRO' 
            self.cursor.execute(sql, params)
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
        """Devuelve lista de alumnos calculando la EDAD en tiempo real."""
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
                A.ESTADO
            FROM ALUMNOS A
            LEFT JOIN CLASES C ON A.ID_CLASEFK = C.ID_CLASE
            LEFT JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
            LEFT JOIN INSCRIPCIONES I ON A.ID_ALUMNO = I.ID_ALUMNO AND I.ESTADO = 'Activo'
        '''
        params = []
        if estado in ('Activo', 'Inactivo'):
            sql += ' WHERE A.ESTADO = ?'
            params.append(estado)
        else:
            sql += " WHERE A.ESTADO NOT IN ('Lista De Espera', 'Prioridad')"
        sql += ' ORDER BY A.ID_ALUMNO DESC LIMIT 50'
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        
        # --- PROCESAMIENTO DINÁMICO DE EDAD ---
        resultados_reales = []
        for row in rows:
            lista = list(row) # Convertimos tupla a lista para poder editar
            fecha_nac = lista[6] # El índice 6 es FECHA_DE_NACIMIENTO
            
            # Recalculamos la edad real en meses
            lista[3] = self._calcular_edad_meses(fecha_nac) # El índice 3 es EDAD
            
            resultados_reales.append(tuple(lista))
        
        return resultados_reales
    
    def _sql_normalizado(self, columna):
        """
        Genera SQL para eliminar acentos y mayúsculas en búsqueda.
        Versión BLINDADA: Incluye minúsculas para mayor compatibilidad.
        """
        col = f"UPPER({columna})"
        # Reemplazos exhaustivos (Mayúsculas y Minúsculas)
        replacements = [
            ('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U'), ('Ñ', 'N'),
            ('á', 'A'), ('é', 'E'), ('í', 'I'), ('ó', 'O'), ('ú', 'U'), ('ñ', 'N')
        ]
        for char_con, char_sin in replacements:
            col = f"REPLACE({col}, '{char_con}', '{char_sin}')"
        return col

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
                   A.ESTADO
            FROM ALUMNOS A
            LEFT JOIN CLASES C ON A.ID_CLASEFK = C.ID_CLASE
            LEFT JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
            LEFT JOIN INSCRIPCIONES I ON A.ID_ALUMNO = I.ID_ALUMNO AND I.ESTADO = 'Activo'
        '''
        where = []
        params = []
        if query:
            # 1. Normalizar query (Mayúsculas y sin acentos) en Python
            trans_table = str.maketrans("ÁÉÍÓÚÑáéíóúñ", "AEIOUNAEIOUN")
            query_limpia = query.upper().translate(trans_table)
            
            # 2. Separar por palabras para buscar "Juan Perez" cruzado
            for palabra in query_limpia.split():
                like = f"%{palabra}%"
                col_nombre = self._sql_normalizado("A.NOMBRE")
                col_apellido = self._sql_normalizado("A.APELLIDO")
                
                bloque_or = [
                    "CAST(A.ID_ALUMNO AS TEXT) LIKE ?",
                    f"{col_nombre} LIKE ?",
                    f"{col_apellido} LIKE ?",
                    "A.TELEFONO LIKE ?"
                ]
                where.append(f"({' OR '.join(bloque_or)})")
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
        else:
            where.append("A.ESTADO NOT IN ('Lista De Espera', 'Prioridad')")
        if id_programa:
            where.append('C.ID_PROGRAMAFK = ?')
            params.append(id_programa)
        if id_clase:
            where.append('A.ID_CLASEFK = ?')
            params.append(id_clase)
            
        # Nota: El filtro por edad en base de datos seguirá usando el valor guardado, 
        # pero para visualización usaremos el calculado. Si necesitas filtrar exacto por edad calculada,
        # habría que filtrar en Python, pero por rendimiento lo dejamos así en SQL por ahora.
        if edad is not None:
            edad_min = edad * 12
            edad_max = edad_min + 11
            where.append('A.EDAD BETWEEN ? AND ?')
            params.extend([edad_min, edad_max])
            
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        
        sql += ' ORDER BY CASE WHEN A.ESTADO = \'Prioridad\' THEN 1 WHEN A.ESTADO = \'Lista De Espera\' THEN 2 ELSE 3 END, A.NOMBRE, A.APELLIDO LIMIT 100'
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()

        # --- PROCESAMIENTO DINÁMICO DE EDAD ---
        resultados_reales = []
        for row in rows:
            lista = list(row)
            fecha_nac = lista[6] # Index 6: FECHA_DE_NACIMIENTO
            
            # Sobreescribimos la edad (Index 3) con el cálculo fresco
            lista[3] = self._calcular_edad_meses(fecha_nac)
            
            resultados_reales.append(tuple(lista))

        return resultados_reales
    
    def obtener_alumno_por_id(self, alumno_id):
        """
        Obtiene todos los datos de un alumno por su ID calculando la EDAD real.
        """
        self.cursor.execute('SELECT * FROM ALUMNOS WHERE ID_ALUMNO = ?', (alumno_id,))
        row = self.cursor.fetchone()
        if row:
            column_names = [description[0] for description in self.cursor.description]
            data = dict(zip(column_names, row))
            
            # --- CORRECCIÓN DE EDAD ---
            if 'FECHA_DE_NACIMIENTO' in data:
                data['EDAD'] = self._calcular_edad_meses(data['FECHA_DE_NACIMIENTO'])
            # --------------------------
            
            return data
        return None

    def actualizar_alumno(self, alumno_id, datos_actualizados):
        
        id_clase_actual = None
        estado_actual = None
        
        # 1. Obtener datos actuales
        self.cursor.execute('SELECT ID_CLASEFK, ESTADO FROM ALUMNOS WHERE ID_ALUMNO = ?', (alumno_id,))
        row = self.cursor.fetchone()
        if row:
            id_clase_actual = row[0]
            estado_actual = row[1]

        # 2. Determinar Clase Destino
        id_clase_destino = datos_actualizados.get('id_clasefk')
        # Si no viene en el update, usamos la que ya tenía
        if id_clase_destino is None:
            id_clase_destino = id_clase_actual

        # 3. RESTRICCIÓN DE NEGOCIO (EL CANDADO)
        nuevo_estado = datos_actualizados.get('estado')
        
        # Si quiere ser ACTIVO, DEBE tener una clase (destino o actual)
        if nuevo_estado == 'Activo' and not id_clase_destino:
            raise ValueError("No se puede activar al alumno sin asignarle un Programa y una Clase.")
        
        verificar_cupo = False
        if nuevo_estado == 'Activo':
            if estado_actual != 'Activo':
                verificar_cupo = True # Está entrando de fuera
            elif id_clase_actual != id_clase_destino:
                verificar_cupo = True # Se está cambiando de grupo
        
            # VALIDACIÓN: RANGO DE EDAD
            rango_edad = self.obtener_rango_edad_clase(id_clase_destino)
            if rango_edad:
                edad_min, edad_max = rango_edad
                fecha_nac_str = datos_actualizados.get('fecha_de_nacimiento')
                edad_real_meses = self._calcular_edad_meses(fecha_nac_str)
                
                if not (edad_min <= edad_real_meses <= edad_max):
                    # Función interna para formatear "X años y Y meses"
                    def fmt_edad(meses_totales):
                        anios = meses_totales // 12
                        meses = meses_totales % 12
                        partes = []
                        if anios > 0: partes.append(f"{anios} año{'s' if anios != 1 else ''}")
                        if meses > 0 or anios == 0: partes.append(f"{meses} mes{'es' if meses != 1 else ''}")
                        return " y ".join(partes)

                    txt_alumno = fmt_edad(edad_real_meses)
                    txt_min = fmt_edad(edad_min)
                    txt_max = fmt_edad(edad_max)
                    
                    raise ValueError(f"No se puede asignar: El alumno tiene {txt_alumno} y este grupo es para niños de {txt_min} a {txt_max}.")
                
        if verificar_cupo and id_clase_destino:
            capacidad = self.obtener_capacidad_clase(id_clase_destino) or 0
            ocupados = self.contar_alumnos_en_clase(id_clase_destino)
            if ocupados >= capacidad:
                raise ValueError(f"La clase seleccionada está llena ({ocupados}/{capacidad}). No se puede guardar.")
        
        # --- INTERCEPCIÓN: PROTECCIÓN DE SALDO (Baja Pendiente) ---
        if nuevo_estado == 'Inactivo':
             # Verificamos si tiene clases pagadas antes de permitir la muerte civil del alumno
             self.cursor.execute("SELECT SUM(CLASES_RESTANTES) FROM INSCRIPCIONES WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'", (alumno_id,))
             row_saldo = self.cursor.fetchone()
             saldo = row_saldo[0] if row_saldo and row_saldo[0] else 0
             
             if saldo > 0:
                 print(f"[Sistema] Alumno {alumno_id} intenta Baja pero tiene {saldo} clases. Se fuerza 'Baja Pendiente'.")
                 nuevo_estado = 'Baja Pendiente'
                 datos_actualizados['estado'] = 'Baja Pendiente'
                 # Al cambiar el estado a 'Baja Pendiente':
                 # 1. No entrará en el bloque siguiente de limpiar clase (seguirá teniendo cupo).
                 # 2. No entrará en el CASO C (Baja) de las inscripciones, por lo que su contrato seguirá 'Activo' y descontando clases.

        # Si pasa a Inactivo, limpiamos la clase
        if nuevo_estado == 'Inactivo':
            datos_actualizados['id_clasefk'] = None
            id_clase_destino = None

        # --- LÓGICA DE HISTORIAL ---
        if estado_actual and nuevo_estado and estado_actual != nuevo_estado:
            detalles = f"Estado: {estado_actual} a {nuevo_estado}."
            f_ini = None
            f_fin = None
            
            # Si pasó el candado de arriba, seguro tiene clase, así que calculamos sin miedo
            if estado_actual in ('Inactivo', 'Lista De Espera', 'Prioridad') and nuevo_estado == 'Activo':
                    self.cursor.execute('''
                        SELECT C.DIAS_DE_CLASES, P.NUM_CLASES
                        FROM CLASES C
                        JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
                        WHERE C.ID_CLASE = ?
                    ''', (id_clase_destino,))
                    datos_calc = self.cursor.fetchone()
                    
                    if datos_calc:
                        fecha_manual = datos_actualizados.get('fecha_inicio_actividad')
                        f_ini = fecha_manual if fecha_manual else datetime.now().date().isoformat()
                        f_fin = self.calcular_fecha_vencimiento(f_ini, datos_calc[1], datos_calc[0])

            self.agregar_historial(alumno_id, "Cambio de Estado", detalles, fecha_inicio=f_ini, fecha_fin=f_fin)
        # ---------------------------

        # 4. ACTUALIZAR TABLA ALUMNOS (Perfil)
        sql = '''
            UPDATE ALUMNOS SET
                NOMBRE = ?, APELLIDO = ?, EDAD = ?,
                TELEFONO = ?, TELEFONO2 = ?, FECHA_DE_NACIMIENTO = ?, OBSERVACIONES = ?,
                ESTADO = ?, NIVEL = ?, ID_CLASEFK = ?
            WHERE ID_ALUMNO = ?
        '''
        
        # Definir la clase final a guardar en ALUMNOS
        clase_final_alumnos = id_clase_destino if nuevo_estado == 'Activo' else None
        
        # MEJORA: Si es Lista de Espera/Prioridad, mantenemos la clase de interés para no perder el dato
        if nuevo_estado in ('Lista De Espera', 'Prioridad'):
            clase_final_alumnos = id_clase_destino

        self.cursor.execute(sql, (
            datos_actualizados.get('nombre'),
            datos_actualizados.get('apellido'),
            datos_actualizados.get('edad'),
            datos_actualizados.get('telefono'),
            datos_actualizados.get('telefono2'),
            datos_actualizados.get('fecha_de_nacimiento'),
            datos_actualizados.get('observaciones'),
            datos_actualizados.get('estado'),
            datos_actualizados.get('nivel'),
            clase_final_alumnos,
            alumno_id
        ))

        # 5. --- LÓGICA DE TRANSICIÓN DE ESTADO (EL CEREBRO DEL CAMBIO) ---
        
        # CASO A: EL ALUMNO SE ESTÁ ACTIVANDO (Viene de Espera, Inactivo o Prioridad -> ACTIVO)
        # Acción: ¡Debemos crearle su contrato (Inscripción) inmediatamente!
        if nuevo_estado == 'Activo' and estado_actual != 'Activo':
            print(f"[Info] Promoviendo alumno {alumno_id} a Activo. Generando inscripción...")
            
            # 1. Necesitamos el ID_PROGRAMA asociado a la clase destino
            self.cursor.execute("SELECT ID_PROGRAMAFK FROM CLASES WHERE ID_CLASE = ?", (id_clase_destino,))
            row_prog = self.cursor.fetchone()
            
            if row_prog:
                id_programa_asociado = row_prog[0]
                # Usamos la fecha que viene del formulario o HOY por defecto
                fecha_inicio = datos_actualizados.get('fecha_inicio_actividad', datetime.now().strftime('%Y-%m-%d'))
                
                # Verificar que no tenga ya una inscripción activa (por seguridad)
                self.cursor.execute("SELECT ID_INSCRIPCION FROM INSCRIPCIONES WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'", (alumno_id,))
                if not self.cursor.fetchone():
                    # CREAR LA INSCRIPCIÓN (Llamamos a tu método existente)
                    self.crear_inscripcion(alumno_id, id_programa_asociado, id_clase_destino, fecha_inicio)
                else:
                    print("[Aviso] El alumno ya tenía inscripción activa. No se duplicó.")

        # CASO B: EL ALUMNO YA ERA ACTIVO Y SOLO CAMBIÓ DE CLASE
        # Acción: Actualizar su inscripción existente para que apunte a la nueva clase.
        elif nuevo_estado == 'Activo' and estado_actual == 'Activo' and id_clase_actual != id_clase_destino:
             # 1. Buscamos a qué programa pertenece la NUEVA clase
             self.cursor.execute("SELECT ID_PROGRAMAFK FROM CLASES WHERE ID_CLASE = ?", (id_clase_destino,))
             row_prog_nuevo = self.cursor.fetchone()
             
             if row_prog_nuevo:
                 id_programa_nuevo = row_prog_nuevo[0]
                 print(f"[Info] Migrando inscripción de alumno {alumno_id} a Clase {id_clase_destino} / Programa {id_programa_nuevo}.")
                 
                 # 2. Actualizamos AMBOS punteros (Clase y Programa)
                 self.cursor.execute("""
                    UPDATE INSCRIPCIONES 
                    SET ID_CLASE = ?, ID_PROGRAMA = ?
                    WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'
                 """, (id_clase_destino, id_programa_nuevo, alumno_id))
        
        # CASO C: BAJA DEL ALUMNO (Pasa a Inactivo)
        # Acción: Cancelar inscripciones.
        elif nuevo_estado in ('Inactivo', 'Lista De Espera', 'Prioridad') and estado_actual == 'Activo':
             print(f"[Info] Dando de baja inscripciones del alumno {alumno_id}.")
             self.cursor.execute("""
                UPDATE INSCRIPCIONES 
                SET ESTADO = 'Baja' 
                WHERE ID_ALUMNO = ? AND ESTADO = 'Activo'
             """, (alumno_id,))
        
        self.conn.commit()      
    
    def actualizar_estado_alumno(self, alumno_id, nuevo_estado):
        """Actualiza el estado. RESTRICCIÓN: Requiere clase para activar."""
        
        # 1. Obtener datos actuales
        self.cursor.execute('SELECT ESTADO, ID_CLASEFK FROM ALUMNOS WHERE ID_ALUMNO = ?', (alumno_id,))
        row = self.cursor.fetchone()
        estado_anterior = row[0] if row else 'Desconocido'
        id_clase_actual = row[1] if row else None
        
        # 2. RESTRICCIÓN DE NEGOCIO (EL CANDADO)
        if nuevo_estado == 'Activo' and not id_clase_actual:
            # Lanzamos error para que el Controlador avise al usuario
            raise ValueError("El alumno no tiene clase asignada. Edite el perfil completo para asignarle una clase antes de activarlo.")
        
        if nuevo_estado == 'Activo' and estado_anterior != 'Activo' and id_clase_actual:
            capacidad = self.obtener_capacidad_clase(id_clase_actual) or 0
            ocupados = self.contar_alumnos_en_clase(id_clase_actual)
            if ocupados >= capacidad:
                raise ValueError(f"No se puede activar: La clase está llena ({ocupados}/{capacidad}).")

        # 3. Verificar cambio
        if estado_anterior != nuevo_estado:
            detalles = f"Estado: {estado_anterior} -> {nuevo_estado}."
            f_ini = None
            f_fin = None
            # Cálculo de fechas (Seguro porque ya validamos que hay clase)
            if estado_anterior in ('Inactivo', 'Lista De Espera', 'Prioridad') and nuevo_estado == 'Activo':
                    self.cursor.execute('''
                        SELECT C.DIAS_DE_CLASES, P.NUM_CLASES
                        FROM CLASES C
                        JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
                        WHERE C.ID_CLASE = ?
                    ''', (id_clase_actual,))
                    datos_calc = self.cursor.fetchone()
                    if datos_calc:
                        f_ini = datetime.now().date().isoformat()
                        f_fin = self.calcular_fecha_vencimiento(f_ini, datos_calc[1], datos_calc[0])
                    
            
            self.agregar_historial(alumno_id, "Cambio de Estado", detalles, fecha_inicio=f_ini, 
                fecha_fin=f_fin)
        
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

    def obtener_clases_detalle_por_programas(self, program_ids, nombre_instructor_filtro=None):
        """Devuelve clases detalladas para los programas indicados:
        (ID_CLASE, HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, NOMBRE_MAESTRO_ACTIVO)
        """
        if not program_ids:
            return []

        placeholders = ','.join(['?'] * len(program_ids))
        params = list(program_ids) # Convertir a lista para poder añadir más parámetros

        # Construcción base de la consulta SQL
        sql = f'''
            SELECT C.ID_CLASE, C.HORA_INICIO, C.HORA_FIN, C.CAPACIDAD, C.DIAS_DE_CLASES, C.ID_PROGRAMAFK,
                   CASE
                       WHEN M.ESTADO = 'Activo' THEN M.NOMBRE_MAESTRO
                       ELSE NULL
                   END AS NOMBRE_MAESTRO_ACTIVO
            FROM CLASES C
            LEFT JOIN MAESTROS M ON C.ID_MAESTROFK = M.ID_MAESTRO
            WHERE C.ID_PROGRAMAFK IN ({placeholders})
        '''

        if nombre_instructor_filtro:
            sql += " AND (M.ESTADO = 'Activo' AND M.NOMBRE_MAESTRO LIKE ?)"
            params.append(f"%{nombre_instructor_filtro}%") 
        # -------------------------------------------------------------

        self.cursor.execute(sql, tuple(params)) 
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

        self.cursor.execute("SELECT DIAS_DE_CLASES, HORA_INICIO FROM CLASES WHERE ID_CLASE = ?", (id_clase,))
        dias_clase_row = self.cursor.fetchone()
        dias_clase = dias_clase_row[0] if dias_clase_row else ""
        horario_clase_str = f"{dias_clase} - {dias_clase_row[1]}" if dias_clase_row else f"ID {id_clase}"

        self.cursor.execute("SELECT NOMBRE_PROGRAMA FROM PROGRAMA WHERE ID_PROGRAMA = ?", (id_programa,))
        nombre_programa_row = self.cursor.fetchone()
        nombre_programa = nombre_programa_row[0] if nombre_programa_row else f"ID {id_programa}"

        fecha_fin = self.calcular_fecha_vencimiento(fecha_inicio, num_clases_total, dias_clase)

        self.cursor.execute('''
            INSERT INTO INSCRIPCIONES (ID_ALUMNO, ID_PROGRAMA, ID_CLASE, FECHA_INICIO, FECHA_FIN, NUM_CLASES, CLASES_RESTANTES, ESTADO)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Activo')
        ''', (id_alumno, id_programa, id_clase, fecha_inicio, fecha_fin, num_clases_total, num_clases_total))
    
        self.conn.commit()
        id_inscripcion = self.cursor.lastrowid
    
        # Detalle mejorado para el historial
        detalles = f"Inscrito en {nombre_programa}, horario: {horario_clase_str}."
        self.agregar_historial(id_alumno, "Inscripción", detalles, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    
        return id_inscripcion

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
            
        # --- AUTO-FINALIZAR BAJA ---
            if nuevas_clases_restantes == 0:
                self.cursor.execute("SELECT ESTADO FROM ALUMNOS WHERE ID_ALUMNO = ?", (id_alumno,))
                row_est = self.cursor.fetchone()
                if row_est and row_est[0] == 'Baja Pendiente':
                    print(f"[Sistema] El alumno {id_alumno} terminó sus clases. Pasando a Inactivo.")
                    # Ahora sí liberamos el lugar y cerramos la inscripción
                    self.cursor.execute("UPDATE ALUMNOS SET ESTADO = 'Inactivo' WHERE ID_ALUMNO = ?", (id_alumno,))
                    self.cursor.execute("UPDATE INSCRIPCIONES SET ESTADO = 'Baja' WHERE ID_INSCRIPCION = ?", (id_inscripcion,))
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
    
    def agregar_historial(self, id_alumno, tipo_modificacion, detalles='', fecha_inicio=None, fecha_fin=None):
        """Agrega un registro al historial de modificaciones del alumno."""
        try:
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('''
                INSERT INTO HISTORIAL_MODIFICACIONES (ID_ALUMNO, FECHA, TIPO_MODIFICACION, DETALLES, FECHA_INICIO, FECHA_FIN)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (id_alumno, fecha_actual, tipo_modificacion, detalles, fecha_inicio, fecha_fin))
            self.conn.commit()
        except Exception as e:
            print(f"Error al agregar al historial: {e}")
            self.conn.rollback()
    
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
    
    def asignar_instructor_a_clase(self, id_clase, id_maestro):
        """Asigna un ID_MAESTROFK a una clase específica, validando cruces de horario."""
        # 1. Validación de disponibilidad (Si es para quitar instructor, id_maestro es None y saltamos validación)
        if id_maestro is not None:
            hay_conflicto, mensaje = self._verificar_cruce_horarios(id_maestro, id_clase)
            if hay_conflicto:
                print(f"No se pudo asignar: {mensaje}")
                return False, mensaje 

        try:
            # 2. Asignación si no hay conflicto
            self.cursor.execute("UPDATE CLASES SET ID_MAESTROFK = ? WHERE ID_CLASE = ?", (id_maestro, id_clase))
            self.conn.commit()
            return True, "Instructor asignado correctamente."

        except Exception as e:
            print(f"Error al asignar instructor a clase: {e}")
            self.conn.rollback()
            return False

    def agregar_clase_extra_grupo(self, id_clase, motivo="Clase cancelada por instructor"):
        
        """
        Incrementa clases restantes y recalcula FECHA_FIN para inscripciones activas 
        VALIDANDO que el alumno siga perteneciendo a la clase (Sincronización Perfil-Inscripción).
        """
        inscripciones_actualizadas = 0
        try:
            # 1. Obtener inscripciones FILTRADAS por ID_CLASE en ambas tablas (Inscripción y Alumno)
            self.cursor.execute("""
                SELECT I.ID_INSCRIPCION, I.ID_ALUMNO, I.FECHA_FIN, C.DIAS_DE_CLASES
                FROM INSCRIPCIONES I
                JOIN CLASES C ON I.ID_CLASE = C.ID_CLASE
                JOIN ALUMNOS A ON I.ID_ALUMNO = A.ID_ALUMNO
                WHERE I.ID_CLASE = ? 
                  AND I.ESTADO = 'Activo' 
                  AND A.ID_CLASEFK = ? 
                  AND A.ESTADO = 'Activo'
            """, (id_clase, id_clase))
            
            inscripciones = self.cursor.fetchall()

            if not inscripciones:
                print(f"Advertencia: No se encontraron alumnos válidos en la clase ID {id_clase}.")
                return True 

            # 2. Iterar sobre cada alumno para calcular SU propia fecha de fin
            for id_inscripcion, id_alumno, fecha_fin_actual, dias_clases_str in inscripciones:
                
                nueva_fecha_fin = self._calcular_siguiente_dia_clase(fecha_fin_actual, dias_clases_str)

                self.cursor.execute("""
                    UPDATE INSCRIPCIONES
                    SET CLASES_RESTANTES = COALESCE(CLASES_RESTANTES, 0) + 1,
                        FECHA_FIN = ?
                    WHERE ID_INSCRIPCION = ?
                """, (nueva_fecha_fin, id_inscripcion))
                
                if self.cursor.rowcount > 0:
                    inscripciones_actualizadas += 1
                    detalles_historial = f"Clase ID {id_clase}. Motivo: {motivo}."
                    
                    self.agregar_historial(
                        id_alumno, 
                        "Clase Extra Grupo", 
                        detalles_historial,
                        fecha_inicio=fecha_fin_actual,
                        fecha_fin=nueva_fecha_fin
                    )

            self.conn.commit()
            print(f"Proceso grupal completado. Se actualizaron {inscripciones_actualizadas} alumnos de la clase {id_clase}.")
            return True

        except Exception as e:
            print(f"Error al agregar clase extra grupal: {e}")
            self.conn.rollback()
            return False
        
    def agregar_clase_extra_individual(self, id_inscripcion, motivo="Reposición"):
        """Incrementa clases restantes y extiende la FECHA_FIN al siguiente día de clase real."""
        try:
            # 1. Obtener fecha fin actual y los días que cursa el alumno
            self.cursor.execute("""
                SELECT I.FECHA_FIN, C.DIAS_DE_CLASES
                FROM INSCRIPCIONES I
                JOIN CLASES C ON I.ID_CLASE = C.ID_CLASE
                WHERE I.ID_INSCRIPCION = ? AND I.ESTADO = 'Activo'
            """, (id_inscripcion,))
            
            resultado = self.cursor.fetchone()
            if not resultado:
                print(f"Advertencia: No se encontró inscripción activa para ID {id_inscripcion}")
                return False

            fecha_fin_actual = resultado[0]
            dias_clases_str = resultado[1]

            # 2. Calcular la nueva fecha de fin (el siguiente día hábil de su clase)
            nueva_fecha_fin = self._calcular_siguiente_dia_clase(fecha_fin_actual, dias_clases_str)

            # 3. Actualizar en BD: +1 clase y Nueva Fecha Fin
            self.cursor.execute("""
                UPDATE INSCRIPCIONES
                SET CLASES_RESTANTES = COALESCE(CLASES_RESTANTES, 0) + 1,
                    FECHA_FIN = ?
                WHERE ID_INSCRIPCION = ?
            """, (nueva_fecha_fin, id_inscripcion))

            if self.cursor.rowcount > 0:
                # Registrar en historial
                self.cursor.execute("SELECT ID_ALUMNO FROM INSCRIPCIONES WHERE ID_INSCRIPCION = ?", (id_inscripcion,))
                res_alumno = self.cursor.fetchone()
                if res_alumno:
                    detalles = f"Motivo: {motivo}."
                    # Usamos: fecha_inicio = Fin Anterior | fecha_fin = Nuevo Fin
                    self.agregar_historial(
                        res_alumno[0], 
                        "Clase Extra Individual", 
                        detalles, 
                        fecha_inicio=fecha_fin_actual, 
                        fecha_fin=nueva_fecha_fin
                    )
            
            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error al agregar clase extra individual: {e}")
            self.conn.rollback()
            return False

    def _calcular_siguiente_dia_clase(self, fecha_base_str, dias_str):
        """Busca la siguiente fecha calendario que coincida con los días de clase del alumno."""
        try:
            fecha = datetime.strptime(fecha_base_str, '%Y-%m-%d').date()
            
            mapa_dias = {
                'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
                'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
            }
            
            dias_validos = []
            if dias_str:
                partes = dias_str.replace(',', ' ').split()
                for p in partes:
                    limpio = p.lower().strip()
                    if limpio in mapa_dias:
                        dias_validos.append(mapa_dias[limpio])
            
            if not dias_validos:
                return (fecha + timedelta(days=1)).strftime('%Y-%m-%d')

            while True:
                fecha += timedelta(days=1)
                if fecha.weekday() in dias_validos:
                    return fecha.strftime('%Y-%m-%d')
                    
        except Exception as e:
            print(f"Error calculando siguiente fecha: {e}")
            return fecha_base_str

    def obtener_historial_alumno(self, alumno_id): 

        """Obtiene el historial de modificaciones para un alumno específico."""
        self.cursor.execute('''
            SELECT FECHA, TIPO_MODIFICACION, FECHA_INICIO, FECHA_FIN, DETALLES 
            FROM HISTORIAL_MODIFICACIONES 
            WHERE ID_ALUMNO = ? 
            ORDER BY FECHA DESC
        ''', (alumno_id,))
        return self.cursor.fetchall()
    
    def _verificar_cruce_horarios(self, id_maestro, id_clase_nueva):
        """Verifica si el maestro ya tiene una clase que se solape en día y hora."""
        try:
            self.cursor.execute("SELECT HORA_INICIO, HORA_FIN, DIAS_DE_CLASES FROM CLASES WHERE ID_CLASE = ?", (id_clase_nueva,))
            clase_nueva = self.cursor.fetchone()
            if not clase_nueva:
                return True, "La clase a asignar no existe."

            # Parseo de horas de la nueva clase
            fmt = '%H:%M'
            try:
                nueva_inicio = datetime.strptime(clase_nueva[0].strip(), fmt)
                nueva_fin = datetime.strptime(clase_nueva[1].strip(), fmt)
            except ValueError:
                return False, "" # Si hay error de formato, asumimos que no hay cruce (fallback)

            conjunto_dias_nuevos = set(self._split_days(clase_nueva[2]))

            # Buscar otras clases del maestro
            self.cursor.execute("""
                SELECT C.ID_CLASE, C.HORA_INICIO, C.HORA_FIN, C.DIAS_DE_CLASES, P.NOMBRE_PROGRAMA
                FROM CLASES C
                LEFT JOIN PROGRAMA P ON C.ID_PROGRAMAFK = P.ID_PROGRAMA
                WHERE C.ID_MAESTROFK = ? AND C.ID_CLASE != ?
            """, (id_maestro, id_clase_nueva))
            
            clases_existentes = self.cursor.fetchall()

            for _, inicio_str, fin_str, dias_str, nombre_prog in clases_existentes:
                conjunto_dias_existentes = set(self._split_days(dias_str))
                
                # Si no coinciden los días, no hay problema
                if not conjunto_dias_nuevos.intersection(conjunto_dias_existentes):
                    continue 

                try:
                    existente_inicio = datetime.strptime(inicio_str.strip(), fmt)
                    existente_fin = datetime.strptime(fin_str.strip(), fmt)
                except ValueError:
                    continue

                # Lógica de solapamiento
                if (nueva_inicio < existente_fin) and (existente_inicio < nueva_fin):
                    dias_comunes = ", ".join(conjunto_dias_nuevos.intersection(conjunto_dias_existentes))
                    return True, f"Conflicto con '{nombre_prog}' ({dias_comunes} {inicio_str}-{fin_str})."

            return False, "Horario disponible."

        except Exception as e:
            print(f"Error validando cruce: {e}")
            return True, f"Error técnico: {e}"
        
    def _calcular_edad_meses(self, fecha_nac_str):
        """Calcula la edad en meses dinámicamente basándose en la fecha de nacimiento."""
        if not fecha_nac_str:
            return 0
        try:
            # Intenta parsear YYYY-MM-DD
            nac = datetime.strptime(fecha_nac_str, '%Y-%m-%d').date()
            hoy = datetime.now().date()
            
            edad_meses = (hoy.year - nac.year) * 12 + hoy.month - nac.month
            
            # Ajuste si el día actual es anterior al día de nacimiento
            if hoy.day < nac.day:
                edad_meses -= 1
                
            return max(0, edad_meses)
        except Exception:
            return max(0, edad_meses)