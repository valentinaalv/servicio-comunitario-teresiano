import sqlite3

def crear_base_de_datos():
    conexion = sqlite3.connect("semana_deportiva.db")
    cursor = conexion.cursor()

    # Tabla de inscripciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cedula TEXT NOT NULL,
            nivel TEXT NOT NULL,
            deporte TEXT NOT NULL,
            fecha TEXT DEFAULT ''
        )
    ''')

    # Tabla: Deportes (Catálogo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')

    # Tabla: Niveles/Grados (Catálogo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS niveles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
    ''')

    # Tabla: Usuarios (Panel Admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Tabla: Cronogramas / Partidos de la Semana Deportiva
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cronogramas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT NOT NULL,
            dia TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            enfrentamiento TEXT NOT NULL,
            cancha TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            ganador TEXT DEFAULT '',
            fase TEXT DEFAULT 'Fase 1',
            etapa TEXT DEFAULT ''
        )
    ''')

    # Migraciones en caliente si la tabla ya existía
    cursor.execute("PRAGMA table_info(cronogramas)")
    columnas = [info[1] for info in cursor.fetchall()]
    if 'ganador' not in columnas:
        cursor.execute("ALTER TABLE cronogramas ADD COLUMN ganador TEXT DEFAULT ''")
    if 'fase' not in columnas:
        cursor.execute("ALTER TABLE cronogramas ADD COLUMN fase TEXT DEFAULT 'Fase 1'")
    if 'etapa' not in columnas:
        cursor.execute("ALTER TABLE cronogramas ADD COLUMN etapa TEXT DEFAULT ''")

    conexion.commit()
    conexion.close()
    print("¡Base de datos actualizada con todas las tablas y columnas necesarias!")

if __name__ == '__main__':
    crear_base_de_datos()