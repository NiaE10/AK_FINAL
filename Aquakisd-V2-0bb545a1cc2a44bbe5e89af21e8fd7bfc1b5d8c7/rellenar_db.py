import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'aquakids.db'

# --- DATOS INICIALES ---
programas = [
	"PROGRAMA ESCOLAR SEMI-PRIVADO ENTRE SEMANA",
	"PROGRAMA BEBÉS SEMI-PERSONALIZADO ENTRE SEMANA",
	"PROGRAMA BEBÉS PERSONALIZADO ENTRE SEMANA",
	"PROGRAMA DE ESCOLAR VERANO",
	"PROGRAMA DE BEBES VERANO",
	"PROGRAMA PRIVADO SABATINOS",
	"PROGRAMA SEMI-PRIVADO ESCOLAR SABATINOS",
	"PROGRAMA SEMI-PRIVADO BEBÉS SABATINOS",
    "PROGRAMA MATRONATACION"
]

# Inserta los programas iniciales en la tabla PROGRAMA si no existen
def rellenar_programas():
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for nombre in programas:
		cursor.execute("SELECT COUNT(*) FROM PROGRAMA WHERE NOMBRE_PROGRAMA = ?", (nombre,))
		if cursor.fetchone()[0] == 0:
			try:
				cursor.execute("INSERT INTO PROGRAMA (NOMBRE_PROGRAMA, NUM_CLASES) VALUES (?, ?)", (nombre, 10))
			except sqlite3.OperationalError:
				# Fallback for older databases without NUM_CLASES column
				try:
					cursor.execute("INSERT INTO PROGRAMA (NOMBRE_PROGRAMA) VALUES (?)", (nombre,))
				except Exception:
					# If that also fails, re-raise the original error to surface it
					raise
		else:
			print(f"El programa '{nombre}' ya existe, no se crea de nuevo.")
	conn.commit()
	conn.close()
	print("Programas iniciales insertados correctamente.")


# Función para crear PROGRAMA matronatacion (ID 9)
def matro_id9():
	DIA = "Sábados"
	EDAD_MIN = 3  # 3 años en meses
	EDAD_MAX = 47 # 3.11 años en meses
	CAPACIDAD = 9  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('14:15', '%H:%M')
	HORA_FINAL = datetime.strptime('17:15', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 9  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(1):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 1:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases PROGRAMA matronatacion insertadas correctamente.")

# Función para crear PROGRAMA SEMI-PRIVADO bebés SABATINOS (ID 8)
def bebe_s_id8():
	DIA = "Sábados"
	EDAD_MIN = 24  # 2 años en meses
	EDAD_MAX = 47 # 3.11 años en meses
	CAPACIDAD = 2  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('9:00', '%H:%M')
	HORA_FINAL = datetime.strptime('14:15', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 8  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(2):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 2:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases PROGRAMA SEMI-PRIVADO bebe SABATINOS insertadas correctamente.")

# Función para crear PROGRAMA SEMI-PRIVADO ESCOLAR SABATINOS (ID 7)
def escolar_s_id7():
	DIA = "Sábados"
	EDAD_MIN = 48  # 4 años en meses
	EDAD_MAX = 144 # 12 años en meses
	CAPACIDAD = 2  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('9:00', '%H:%M')
	HORA_FINAL = datetime.strptime('14:15', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 7  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(5):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 5:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases PROGRAMA SEMI-PRIVADO ESCOLAR SABATINOS insertadas correctamente.")
 
# Función para crear clases semi-privadas bebe entre semana (ID 2)
def bebe_mj_id2():
	DIA = "Martes y Jueves"
	EDAD_MIN = 24  # 2 años en meses
	EDAD_MAX = 47 # 3.11 años en meses
	CAPACIDAD = 2  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('15:00', '%H:%M')
	HORA_FINAL = datetime.strptime('20:00', '%H:%M')
	INTERVALO = timedelta(minutes=30)
	ID_PROGRAMAFK = 2  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(4):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 4:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases mj mat bebe insertadas correctamente.")
 
# Función para crear clases verano bebe (ID 5)
def bebe_verano_mj_id5():
	DIA = "Martes  y Jueves"
	EDAD_MIN = 24  # 2 años en meses
	EDAD_MAX = 47 # 3.11 años en meses
	CAPACIDAD = 2  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('09:00', '%H:%M')
	HORA_FINAL = datetime.strptime('13:00', '%H:%M')
	INTERVALO = timedelta(minutes=30)
	ID_PROGRAMAFK = 5  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(4):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 4:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases verano bebe insertadas correctamente.")
 
# Función para crear clases lmv vesp bebe (ID 2)
def bebe_lmv_vesp_id2():
	DIA = "Lunes, Miércoles y Viernes"
	EDAD_MIN = 24  # 2 años en meses
	EDAD_MAX = 47 # 3.11 años en meses
	CAPACIDAD = 2  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('15:00', '%H:%M')
	HORA_FINAL = datetime.strptime('20:00', '%H:%M')
	INTERVALO = timedelta(minutes=30)
	ID_PROGRAMAFK = 2  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(4):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 4:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases lmv vesp bebe insertadas correctamente.")
 
# Función para crear clases lmv mat bebe (ID 2)
def bebe_lmv_mat_id2():
	DIA = "Lunes, Miércoles y Viernes"
	EDAD_MIN = 24  # 2 años en meses
	EDAD_MAX = 47 # 3.11 años en meses
	CAPACIDAD = 2  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('09:00', '%H:%M')
	HORA_FINAL = datetime.strptime('13:00', '%H:%M')
	INTERVALO = timedelta(minutes=30)
	ID_PROGRAMAFK = 2  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(4):  # Cuatro clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 4:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases lmv mat bebe insertadas correctamente.")

# Función para crear clases verano escolar mj (ID 4)
def escolar_verano_mj_id4():
	DIA = "Martes y Jueves"
	EDAD_MIN = 48  # 4 años en meses
	EDAD_MAX = 144 # 12 años en meses
	CAPACIDAD = 4  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('9:00', '%H:%M')
	HORA_FINAL = datetime.strptime('13:00', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 4  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(3):  # Dos clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 3:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases martes y jueves verano (4-12 años, 2 maestros por horario, maestro sin asignar) insertadas correctamente.")

# Función para crear clases verano escolar lmv (ID 4)
def escolar_verano_lmv_id4():
	DIA = "Lunes, Miércoles y Viernes"
	EDAD_MIN = 48  # 4 años en meses
	EDAD_MAX = 144 # 12 años en meses
	CAPACIDAD = 4  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('9:00', '%H:%M')
	HORA_FINAL = datetime.strptime('13:00', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 4  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(3):  # Dos clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 3:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases LMV VERANO (4-12 años, 2 maestros por horario, maestro sin asignar) insertadas correctamente.")

# Función para crear clases escolar semi-privado entre semana (ID 1)
def escolar_mj_id1():
	DIA = "Martes y jueves"
	EDAD_MIN = 48  # 4 años en meses
	EDAD_MAX = 144 # 12 años en meses
	CAPACIDAD = 4  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('14:45', '%H:%M')
	HORA_FINAL = datetime.strptime('20:00', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 1  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(2):  # Dos clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 2:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases martes y jueves (4-12 años, 2 maestros por horario, maestro sin asignar) insertadas correctamente.")

# Función para crear clases escolar semi-privado entre semana (ID 1)
def escolar_lmv_id1():
	DIA = "Lunes, Miércoles y Viernes"
	EDAD_MIN = 48  # 4 años en meses
	EDAD_MAX = 144 # 12 años en meses
	CAPACIDAD = 4  # Capacidad por maestro
	HORA_INICIO = datetime.strptime('14:45', '%H:%M')
	HORA_FINAL = datetime.strptime('20:00', '%H:%M')
	INTERVALO = timedelta(minutes=45)
	ID_PROGRAMAFK = 1  # Cambia si corresponde a otro programa

	clases = []
	hora_actual = HORA_INICIO
	while hora_actual + INTERVALO <= HORA_FINAL:
		for _ in range(2):  # Dos clases por horario (para dos maestros)
			clases.append({
				'hora_inicio': hora_actual.strftime('%H:%M'),
				'hora_fin': (hora_actual + INTERVALO).strftime('%H:%M'),
				'capacidad': CAPACIDAD,
				'dias': DIA,
				'id_programa': ID_PROGRAMAFK,
				'edad_min': EDAD_MIN,
				'edad_max': EDAD_MAX
				# No se asigna id_maestrofk aquí
			})
		hora_actual += INTERVALO

	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	for clase in clases:
		cursor.execute('''
			SELECT COUNT(*) FROM CLASES
			WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
		''', (clase['hora_inicio'], clase['dias'], clase['id_programa'], clase['capacidad']))
		if cursor.fetchone()[0] < 2:
			cursor.execute('''
				INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
				VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
			''', (
				clase['hora_inicio'], clase['hora_fin'], clase['capacidad'], clase['dias'], clase['id_programa'], clase['edad_min'], clase['edad_max']
			))
	conn.commit()
	conn.close()
	print("Clases lunes, miércoles y viernes (4-12 años, 2 maestros por horario, maestro sin asignar) insertadas correctamente.")
 

def rellenar_todos_los_datos():
    rellenar_programas()
    escolar_lmv_id1()
    escolar_mj_id1()
    escolar_verano_lmv_id4()
    escolar_verano_mj_id4()
    bebe_lmv_mat_id2()
    bebe_lmv_vesp_id2()
    bebe_mj_id2()
    bebe_verano_mj_id5()
    escolar_s_id7()
    bebe_s_id8()
    matro_id9()

if __name__ == "__main__":
    rellenar_todos_los_datos()