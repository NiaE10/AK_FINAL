import os
import sqlite3

DB_NAME = 'aquakids.db'

# Verifica si la base de datos ya existe
if not os.path.exists(DB_NAME):
    # Crea la base de datos y las tablas
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla PROGRAMA con NUM_CLASES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PROGRAMA (
            ID_PROGRAMA INTEGER PRIMARY KEY AUTOINCREMENT,
            NOMBRE_PROGRAMA TEXT NOT NULL,
            NUM_CLASES INTEGER 
        )
    ''')
    
    # Tabla MAESTROS (sin cambios)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MAESTROS (
            ID_MAESTRO INTEGER PRIMARY KEY AUTOINCREMENT,
            NOMBRE_MAESTRO TEXT NOT NULL,
            NUMERO_DE_TELEFONO TEXT NOT NULL,
            ESTADO TEXT NOT NULL
        )
    ''')
    
    # Tabla CLASES (sin cambios)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CLASES (
            ID_CLASE INTEGER PRIMARY KEY AUTOINCREMENT,
            HORA_INICIO TEXT NOT NULL,
            HORA_FIN TEXT NOT NULL,
            EDAD_MIN INTEGER NOT NULL,
            EDAD_MAX INTEGER NOT NULL,
            CAPACIDAD INTEGER NOT NULL,
            DIAS_DE_CLASES TEXT NOT NULL,
            ID_MAESTROFK INTEGER,  
            ID_PROGRAMAFK INTEGER,
            FOREIGN KEY (ID_PROGRAMAFK) REFERENCES PROGRAMA (ID_PROGRAMA),
            FOREIGN KEY (ID_MAESTROFK) REFERENCES MAESTROS (ID_MAESTRO)
        )
    ''')
    
    # Tabla ALUMNOS (sin cambios)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ALUMNOS (
            ID_ALUMNO INTEGER PRIMARY KEY AUTOINCREMENT,
            NOMBRE TEXT NOT NULL,
            APELLIDO TEXT NOT NULL,
            EDAD INTEGER NOT NULL,
            TELEFONO TEXT NOT NULL,
            TELEFONO2 TEXT NOT NULL,
            FECHA_DE_NACIMIENTO TEXT NOT NULL,
            OBSERVACIONES TEXT,
            ESTADO TEXT NOT NULL,
            NIVEL TEXT NOT NULL,
            ID_CLASEFK INTEGER,
            FOREIGN KEY (ID_CLASEFK) REFERENCES CLASES (ID_CLASE)
        )
    ''')

    # Tabla INSCRIPCIONES con CLASES_RESTANTES
    cursor.execute('''
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
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ASISTENCIAS (
            ID_ASISTENCIA INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_INSCRIPCION INTEGER NOT NULL,
            FECHA TEXT NOT NULL,
            FOREIGN KEY(ID_INSCRIPCION) REFERENCES INSCRIPCIONES(ID_INSCRIPCION)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Base de datos '{DB_NAME}' creada correctamente con la nueva estructura.")
else:
    print(f"La base de datos '{DB_NAME}' ya existe. Deberás aplicar las modificaciones manualmente.")