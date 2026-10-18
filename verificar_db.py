import sqlite3

def verificar():
    conexion = sqlite3.connect("semana_deportiva.db")
    cursor = conexion.cursor()
    
    # Intentamos leer la tabla usuarios
    try:
        cursor.execute("SELECT * FROM usuarios")
        registros = cursor.fetchall()
        
        if registros:
            print(f"¡Éxito! Encontré {len(registros)} usuario(s):")
            for r in registros:
                print(r)
        else:
            print("La tabla 'usuarios' existe, pero está vacía.")
            
    except sqlite3.OperationalError:
        print("ERROR: La tabla 'usuarios' no existe en esta base de datos.")
        
    conexion.close()

if __name__ == "__main__":
    verificar()