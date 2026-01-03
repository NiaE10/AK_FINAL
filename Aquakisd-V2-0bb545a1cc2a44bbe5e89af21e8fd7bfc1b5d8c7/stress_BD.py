import sqlite3
import rellenar_db  # Importamos tu script original de llenado

def restaurar_sistema():
    print("⚠️  INICIANDO RESTAURACIÓN DEL SISTEMA ⚠️")
    
    conn = sqlite3.connect('aquakids.db')
    cursor = conn.cursor()
    
    # 1. Limpieza Profunda
    print("🧹 1. Eliminando datos de la prueba de estrés...")
    tablas = ['ASISTENCIAS', 'HISTORIAL_MODIFICACIONES', 'INSCRIPCIONES', 'ALUMNOS', 'CLASES', 'MAESTROS', 'PROGRAMA']
    for t in tablas:
        try:
            cursor.execute(f"DELETE FROM {t}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'") # Reiniciar contadores de ID
        except Exception as e:
            print(f"   [Aviso] Tabla {t}: {e}")
            
    conn.commit()
    
    # 2. Restaurar Infraestructura Real
    print("🏗️  2. Ejecutando rellenar_db.py (Programas y Clases reales)...")
    try:
        rellenar_db.rellenar_todos_los_datos()
    except Exception as e:
        print(f"❌ Error al ejecutar rellenar_db: {e}")
        conn.close()
        return

    # 3. Crear un Maestro por defecto (Necesario para operar)
    print("👤 3. Creando Maestro por defecto...")
    try:
        cursor.execute("INSERT INTO MAESTROS (NOMBRE_MAESTRO, NUMERO_DE_TELEFONO, ESTADO) VALUES (?, ?, ?)", 
                       ("Instructor General", "000-0000", "Activo"))
        conn.commit()
    except Exception as e:
        print(f"   Error creando maestro: {e}")

    conn.close()
    print("\n✅ ¡SISTEMA RESTAURADO! Ahora tienes los programas correctos.")
    print("   -> Ya puedes realizar la Prueba 3 (Flujo Fantasma) con datos reales.")

if __name__ == "__main__":
    restaurar_sistema()