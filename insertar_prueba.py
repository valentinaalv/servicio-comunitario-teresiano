import sqlite3

# Nos conectamos a la despensa
conexion = sqlite3.connect("semana_deportiva.db")
cursor = conexion.cursor()

# Insertamos a nuestros dos alumnos de prueba
cursor.execute("INSERT INTO inscripciones (nombre, cedula, nivel, deporte) VALUES ('Ana Martínez', '31456789', '3er Año', 'Voleibol')")
cursor.execute("INSERT INTO inscripciones (nombre, cedula, nivel, deporte) VALUES ('Carlos Silva', '32123456', '5to Grado', 'Fútbol Sala')")

# Guardamos y cerramos
conexion.commit()
conexion.close()

print("¡Datos de prueba inyectados con éxito!")