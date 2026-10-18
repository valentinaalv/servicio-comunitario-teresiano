import sqlite3
import os

# Esto busca el archivo en la misma carpeta donde está este script
db_path = os.path.join(os.path.dirname(__file__), "semana_deportiva.db")
print(f"Buscando base de datos en: {db_path}")

conexion = sqlite3.connect(db_path)
cursor = conexion.cursor()

# Insertamos el usuario
try:
    cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", ("admin", "1234"))
    conexion.commit()
    print("¡Inserción exitosa!")
except Exception as e:
    print(f"Error al insertar: {e}")

# Verificamos qué hay realmente dentro
cursor.execute("SELECT * FROM usuarios")
datos = cursor.fetchall()
print(f"Contenido actual de la tabla usuarios: {datos}")

conexion.close()