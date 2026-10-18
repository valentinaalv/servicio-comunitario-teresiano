import sqlite3

def poblar_datos():
    conexion = sqlite3.connect("semana_deportiva.db")
    cursor = conexion.cursor()

    # 1. Catálogo de Deportes Oficiales
    lista_deportes = [('Fútbol Sala',), ('Baloncesto',), ('Voleibol',), ('Kikimbol',), ('Atletismo',)]
    for dep in lista_deportes:
        existe = cursor.execute("SELECT 1 FROM deportes WHERE nombre = ?", dep).fetchone()
        if not existe:
            cursor.execute("INSERT INTO deportes (nombre) VALUES (?)", dep)

    # 2. Catálogo de Niveles con Secciones A y B
    niveles_base = [
        '1er Grado', '2do Grado', '3er Grado', '4to Grado', '5to Grado', '6to Grado',
        '1er Año', '2do Año', '3er Año', '4to Año', '5to Año'
    ]
    for nb in niveles_base:
        for sec in ['A', 'B']:
            nombre_nivel = f"{nb} {sec}"
            existe = cursor.execute("SELECT 1 FROM niveles WHERE nombre = ?", (nombre_nivel,)).fetchone()
            if not existe:
                cursor.execute("INSERT INTO niveles (nombre) VALUES (?)", (nombre_nivel,))

    # 3. Inscripciones de prueba realistas para Primaria y Bachillerato
    # Proporciona múltiples secciones y disciplinas para generar un torneo completo
    inscripciones_muestra = [
        # --- PRIMARIA: FÚTBOL SALA ---
        ('Sofía Gómez', '33001001', '1er Grado A', 'Fútbol Sala'),
        ('Mateo Rodríguez', '33001002', '2do Grado B', 'Fútbol Sala'),
        ('Lucas Morales', '33001003', '3er Grado A', 'Fútbol Sala'),
        ('Diego Fernández', '33001004', '4to Grado B', 'Fútbol Sala'),

        # --- PRIMARIA: BALONCESTO ---
        ('Valentina Ramos', '33001005', '3er Grado B', 'Baloncesto'),
        ('Tomás Castillo', '33001006', '4to Grado A', 'Baloncesto'),
        ('Camila Torres', '33001007', '5to Grado B', 'Baloncesto'),
        ('Sebastián Peña', '33001008', '6to Grado A', 'Baloncesto'),

        # --- PRIMARIA: KIKIMBOL ---
        ('Isabella Mendoza', '33001009', '1er Grado B', 'Kikimbol'),
        ('Mariana Herrera', '33001010', '2do Grado A', 'Kikimbol'),
        ('Valeria Rivas', '33001011', '5to Grado A', 'Kikimbol'),
        ('Gabriela Castro', '33001012', '6to Grado B', 'Kikimbol'),

        # --- BACHILLERATO: FÚTBOL SALA ---
        ('Luis Angeli', '31002001', '1er Año A', 'Fútbol Sala'),
        ('Santiago Méndez', '31002002', '2do Año B', 'Fútbol Sala'),
        ('Alejandro Vargas', '31002003', '3er Año A', 'Fútbol Sala'),
        ('Gabriel Rojas', '31002004', '4to Año B', 'Fútbol Sala'),

        # --- BACHILLERATO: BALONCESTO ---
        ('Manuel Duarte', '31002005', '1er Año B', 'Baloncesto'),
        ('Javier Ortiz', '31002006', '2do Año A', 'Baloncesto'),
        ('David Salazar', '31002007', '3er Año B', 'Baloncesto'),
        ('Leonardo Navarro', '31002008', '5to Año A', 'Baloncesto'),

        # --- BACHILLERATO: VOLEIBOL ---
        ('Daniela Fuentes', '31002009', '1er Año A', 'Voleibol'),
        ('Paula Romero', '31002010', '2do Año B', 'Voleibol'),
        ('Ana Martínez', '31002011', '3er Año A', 'Voleibol'),
        ('Valentina Landazabal', '31002012', '5to Año B', 'Voleibol'),

        # --- BACHILLERATO: KIKIMBOL ---
        ('Victoria Gil', '31002013', '2do Año B', 'Kikimbol'),
        ('Andrea Paredes', '31002014', '3er Año A', 'Kikimbol'),
        ('Lucía Delgado', '31002015', '4to Año A', 'Kikimbol'),
        ('Fabiana Blanco', '31002016', '5to Año B', 'Kikimbol'),
    ]

    for nom, ced, niv, dep in inscripciones_muestra:
        existe = cursor.execute(
            "SELECT 1 FROM inscripciones WHERE cedula = ? AND deporte = ?", (ced, dep)
        ).fetchone()
        if not existe:
            cursor.execute(
                "INSERT INTO inscripciones (nombre, cedula, nivel, deporte, fecha) VALUES (?,?,?,?, '2026-10-12 08:00')",
                (nom, ced, niv, dep)
            )

    conexion.commit()
    conexion.close()
    print("¡Base de datos poblada con éxito con deportes, secciones e inscripciones completas!")

if __name__ == '__main__':
    poblar_datos()