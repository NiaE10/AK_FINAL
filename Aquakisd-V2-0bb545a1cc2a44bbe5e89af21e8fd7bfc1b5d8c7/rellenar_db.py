import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'aquakids.db'

def rellenar_programas():
    """
    Inserta o actualiza los programas con su configuración de clases fija.
    El orden de esta lista determina el ID (RowID) en una base de datos nueva.
    IDs esperados:
    1: LMV Escolar Semi, 2: MJ Escolar Semi, 3: LMV Bebés Semi, 4: MJ Bebés Semi,
    5: LMV Bebés Pers, 6: MJ Bebés Pers, 7: LMV Escolar Verano, 8: MJ Escolar Verano,
    9: LMV Bebés Verano, 10: MJ Bebés Verano, 11: Privado Sab, 12: Semi Escolar Sab,
    13: Semi Bebés Sab, 14: Matronatación.
    """
    configuracion_programas = {
        "LMV - ESCOLAR SEMI-PRIVADO ENTRE SEMANA": 12,    # ID 1
        "MJ - ESCOLAR SEMI-PRIVADO ENTRE SEMANA": 8,      # ID 2
        "LMV - BEBÉS SEMI-PERSONALIZADO ENTRE SEMANA": 12,# ID 3
        "MJ - BEBÉS SEMI-PERSONALIZADO ENTRE SEMANA": 8,  # ID 4
        "LMV - BEBÉS PERSONALIZADO ENTRE SEMANA": 12,     # ID 5 (Virtual -> usa clases ID 3)
        "MJ - BEBÉS PERSONALIZADO ENTRE SEMANA": 8,       # ID 6 (Virtual -> usa clases ID 4)
        "LMV - ESCOLAR VERANO": 12,                       # ID 7
        "MJ - ESCOLAR VERANO": 8,                         # ID 8
        "MJ - BEBÉS VERANO": 8,                           # ID 9
        "PRIVADO SABATINOS": 4,                           # ID 10
        "SEMI-PRIVADO ESCOLAR SABATINOS": 4,              # ID 11
        "SEMI-PRIVADO BEBÉS SABATINOS": 4,                # ID 12
        "MATRONATACION": 4                                # ID 13
    }

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("--- Actualizando Programas ---")
    for nombre, num_clases in configuracion_programas.items():
        cursor.execute("SELECT COUNT(*) FROM PROGRAMA WHERE NOMBRE_PROGRAMA = ?", (nombre,))
        
        if cursor.fetchone()[0] == 0:
            try:
                cursor.execute("INSERT INTO PROGRAMA (NOMBRE_PROGRAMA, NUM_CLASES) VALUES (?, ?)", (nombre, num_clases))
            except sqlite3.OperationalError:
                # Fallback para DB antigua sin columna NUM_CLASES
                cursor.execute("INSERT INTO PROGRAMA (NOMBRE_PROGRAMA) VALUES (?)", (nombre,))
        else:
            try:
                # Forzamos la actualización para asegurar integridad
                cursor.execute("UPDATE PROGRAMA SET NUM_CLASES = ? WHERE NOMBRE_PROGRAMA = ?", (num_clases, nombre))
            except sqlite3.OperationalError:
                pass

    conn.commit()
    conn.close()
    print("✅ Programas actualizados.")


def generar_clases_desde_config():
    """
    Genera todas las clases del sistema basándose en una configuración maestra.
    IMPORTANTE: No generamos clases para IDs 5 y 6 (Personalizados), ya que usan el cupo de 3 y 4.
    """
    
    # CONFIGURACIÓN MAESTRA DEL SISTEMA
    # 'sim': simultaneos (cuántos grupos/maestros se abren por horario)
    configuraciones = [
        # --- SÁBADOS ---
        # ID 13: Matronatacion
        {"id": 13, "dias": "Sábados", "inicio": "14:15", "fin": "17:15", "min": 45, "cap": 9, "emin": 3,  "emax": 47,  "sim": 1},
        # ID 12: Semi Bebés Sab
        {"id": 12, "dias": "Sábados", "inicio": "09:00", "fin": "14:15", "min": 45, "cap": 2, "emin": 24, "emax": 47,  "sim": 5},
        # ID 11: Semi Escolar Sab
        {"id": 11, "dias": "Sábados", "inicio": "09:00", "fin": "14:15", "min": 45, "cap": 2, "emin": 48, "emax": 144, "sim": 5},
        # ID 10: Privado Sab
        {"id": 10, "dias": "Sábados", "inicio": "09:00", "fin": "14:15", "min": 45, "cap": 1, "emin": 48, "emax": 144, "sim": 5},

        # --- BEBÉS ENTRE SEMANA (SEMI) ---
        # ID 4: MJ Bebés Semi (Vespertino)
        {"id": 4, "dias": "Martes y Jueves",            "inicio": "15:00", "fin": "20:00", "min": 30, "cap": 2, "emin": 24, "emax": 47, "sim": 5},
        # ID 3: LMV Bebés Semi (Vespertino)
        {"id": 3, "dias": "Lunes, Miércoles y Viernes", "inicio": "15:00", "fin": "20:00", "min": 30, "cap": 2, "emin": 24, "emax": 47, "sim": 5},
        # ID 3: LMV Bebés Semi (Matutino)
        {"id": 3, "dias": "Lunes, Miércoles y Viernes", "inicio": "09:00", "fin": "13:00", "min": 30, "cap": 2, "emin": 24, "emax": 47, "sim": 5},
        
        # --- ESCOLARES ENTRE SEMANA (SEMI) ---
        # ID 2: MJ Escolar Semi
        {"id": 2, "dias": "Martes y jueves",            "inicio": "14:45", "fin": "20:00", "min": 45, "cap": 4, "emin": 48, "emax": 144, "sim": 2},
        # ID 1: LMV Escolar Semi
        {"id": 1, "dias": "Lunes, Miércoles y Viernes", "inicio": "14:45", "fin": "20:00", "min": 45, "cap": 4, "emin": 48, "emax": 144, "sim": 2},
        
        # --- VERANO ---
        # ID 9: MJ Bebés Verano
        {"id": 9, "dias": "Martes y Jueves",          "inicio": "09:00", "fin": "13:00", "min": 30, "cap": 2, "emin": 24, "emax": 47,  "sim": 5},
        # ID 8: MJ Escolar Verano
        {"id": 8,  "dias": "Martes y Jueves",           "inicio": "09:00", "fin": "13:00", "min": 45, "cap": 4, "emin": 48, "emax": 144, "sim": 3},
        # ID 7: LMV Escolar Verano
        {"id": 7,  "dias": "Lunes, Miércoles y Viernes", "inicio": "09:00", "fin": "13:00", "min": 45, "cap": 4, "emin": 48, "emax": 144, "sim": 3},
    ]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("--- Generando Clases ---")
    total_insertadas = 0

    for config in configuraciones:
        hora_actual = datetime.strptime(config["inicio"], '%H:%M')
        hora_final = datetime.strptime(config["fin"], '%H:%M')
        intervalo = timedelta(minutes=config["min"])
        
        clases_a_insertar = []
        
        while hora_actual + intervalo <= hora_final:
            for _ in range(config["sim"]):
                clases_a_insertar.append((
                    hora_actual.strftime('%H:%M'),
                    (hora_actual + intervalo).strftime('%H:%M'),
                    config["cap"],
                    config["dias"],
                    config["id"],
                    config["emin"],
                    config["emax"]
                ))
            hora_actual += intervalo

        nuevas_del_programa = 0
        for clase in clases_a_insertar:
            cursor.execute('''
                SELECT COUNT(*) FROM CLASES
                WHERE HORA_INICIO = ? AND DIAS_DE_CLASES = ? AND ID_PROGRAMAFK = ? AND CAPACIDAD = ? AND ID_MAESTROFK IS NULL
            ''', (clase[0], clase[3], clase[4], clase[2]))
            
            if cursor.fetchone()[0] < config["sim"]:
                cursor.execute('''
                    INSERT INTO CLASES (HORA_INICIO, HORA_FIN, CAPACIDAD, DIAS_DE_CLASES, ID_PROGRAMAFK, EDAD_MIN, EDAD_MAX, ID_MAESTROFK)
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                ''', clase)
                nuevas_del_programa += 1
        
        if nuevas_del_programa > 0:
            print(f"  > Prog ID {config['id']} ({config['dias']}): +{nuevas_del_programa} clases.")
        total_insertadas += nuevas_del_programa

    conn.commit()
    conn.close()
    print(f"✅ Generación completada. Total clases nuevas: {total_insertadas}")

def rellenar_todos_los_datos():
    rellenar_programas()
    generar_clases_desde_config()

if __name__ == "__main__":
    rellenar_todos_los_datos()