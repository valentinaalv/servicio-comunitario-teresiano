from flask import Flask, render_template, request, redirect, session, flash, Response, jsonify
import sqlite3
import csv
import io
import random
import re
import unicodedata
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta_super_segura'

CUPO_MAXIMO = 30

ICONOS = {
    'Fútbol Sala': '⚽', 'Fútbol': '⚽', 'Baloncesto': '🏀',
    'Básquet': '🏀', 'Voleibol': '🏐', 'Kikimbol': '⚾', 'Atletismo': '🏃'
}

DESCRIPCIONES = {
    'Fútbol Sala': 'Cancha techada • Torneo intercursos 5vs5',
    'Fútbol': 'Cancha de grama • Torneo de fútbol',
    'Baloncesto': 'Cancha múltiple • Categoría masculina y femenina',
    'Básquet': 'Cancha múltiple • Categoría masculina y femenina',
    'Voleibol': 'Cancha central • Sistema todos contra todos',
    'Kikimbol': 'Campo deportivo • Tradición colegial teresiana',
    'Atletismo': 'Pista de velocidad • 100m planos y carreras de relevo'
}

CANCHAS = {
    'Fútbol Sala': 'Cancha Techada',
    'Fútbol': 'Cancha de Grama',
    'Baloncesto': 'Cancha Múltiple',
    'Básquet': 'Cancha Múltiple',
    'Voleibol': 'Cancha Central',
    'Kikimbol': 'Campo Deportivo',
    'Atletismo': 'Pista de Velocidad'
}

DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

# ============================================================
# BLOQUES HORARIOS OFICIALES POR ETAPA ESCOLAR
# REGLA 2 ESTRICTA:
# - PRIMARIA (1er a 6to Grado): SOLO 07:45 AM a 10:30 AM
# - BACHILLERATO (1er a 5to Año): SOLO 11:00 AM a 01:45 PM
# ============================================================
BLOQUES_HORARIOS = [
    # --- FRANJA EXCLUSIVA PRIMARIA (07:45 AM - 10:30 AM) ---
    {
        'id': 'bloque_p1',
        'hora_inicio': '07:45 AM',
        'hora_fin': '08:40 AM',
        'etiqueta': '07:45 AM - 08:40 AM',
        'etapa': 'Primaria',
        'tipo': 'primaria',
        'badge': 'Primaria (07:45 AM - 10:30 AM)',
        'nombre_bloque': 'Bloque 1 Primaria'
    },
    {
        'id': 'bloque_p2',
        'hora_inicio': '08:40 AM',
        'hora_fin': '09:35 AM',
        'etiqueta': '08:40 AM - 09:35 AM',
        'etapa': 'Primaria',
        'tipo': 'primaria',
        'badge': 'Primaria (07:45 AM - 10:30 AM)',
        'nombre_bloque': 'Bloque 2 Primaria'
    },
    {
        'id': 'bloque_p3',
        'hora_inicio': '09:35 AM',
        'hora_fin': '10:30 AM',
        'etiqueta': '09:35 AM - 10:30 AM',
        'etapa': 'Primaria',
        'tipo': 'primaria',
        'badge': 'Primaria (07:45 AM - 10:30 AM)',
        'nombre_bloque': 'Bloque 3 Primaria'
    },
    # --- RECESO INSTITUCIONAL / CAMBIO DE JORNADA ---
    {
        'id': 'bloque_receso',
        'hora_inicio': '10:30 AM',
        'hora_fin': '11:00 AM',
        'etiqueta': '10:30 AM - 11:00 AM',
        'etapa': 'Receso',
        'tipo': 'receso',
        'badge': 'Receso / Transición',
        'nombre_bloque': 'Receso Institucional'
    },
    # --- FRANJA EXCLUSIVA BACHILLERATO (11:00 AM - 01:45 PM) ---
    {
        'id': 'bloque_b1',
        'hora_inicio': '11:00 AM',
        'hora_fin': '11:55 AM',
        'etiqueta': '11:00 AM - 11:55 AM',
        'etapa': 'Bachillerato',
        'tipo': 'bachillerato',
        'badge': 'Bachillerato (11:00 AM - 01:45 PM)',
        'nombre_bloque': 'Bloque 1 Bachillerato'
    },
    {
        'id': 'bloque_b2',
        'hora_inicio': '11:55 AM',
        'hora_fin': '12:50 PM',
        'etiqueta': '11:55 AM - 12:50 PM',
        'etapa': 'Bachillerato',
        'tipo': 'bachillerato',
        'badge': 'Bachillerato (11:00 AM - 01:45 PM)',
        'nombre_bloque': 'Bloque 2 Bachillerato'
    },
    {
        'id': 'bloque_b3',
        'hora_inicio': '12:50 PM',
        'hora_fin': '01:45 PM',
        'etiqueta': '12:50 PM - 01:45 PM',
        'etapa': 'Bachillerato',
        'tipo': 'bachillerato',
        'badge': 'Bachillerato (11:00 AM - 01:45 PM)',
        'nombre_bloque': 'Bloque 3 Bachillerato'
    },
]

NORMALIZACION_NIVELES = {
    '1_grado': '1er Grado', '1er grado': '1er Grado', '1er_grado': '1er Grado',
    '2_grado': '2do Grado', '2do grado': '2do Grado', '2do_grado': '2do Grado',
    '3_grado': '3er Grado', '3er grado': '3er Grado', '3er_grado': '3er Grado',
    '4_grado': '4to Grado', '4to grado': '4to Grado', '4to_grado': '4to Grado',
    '5_grado': '5to Grado', '5to grado': '5to Grado', '5to_grado': '5to Grado',
    '6_grado': '6to Grado', '6to grado': '6to Grado', '6to_grado': '6to Grado',
    '1_ano': '1er Año', '1er ano': '1er Año', '1er_ano': '1er Año', '1er año': '1er Año',
    '2_ano': '2do Año', '2do ano': '2do Año', '2do_ano': '2do Año', '2do año': '2do Año',
    '3_ano': '3er Año', '3er ano': '3er Año', '3er_ano': '3er Año', '3er año': '3er Año',
    '4_ano': '4to Año', '4to ano': '4to Año', '4to_ano': '4to Año', '4to año': '4to Año',
    '5_ano': '5to Año', '5to ano': '5to Año', '5to_ano': '5to Año', '5to año': '5to Año',
}

# ============================================================
# FUNCIONES DE APOYO Y VALIDACIÓN
# ============================================================
def get_db():
    con = sqlite3.connect("semana_deportiva.db")
    con.row_factory = sqlite3.Row
    return con

def asegurar_esquema_bd(con):
    cursor = con.cursor()
    cursor.execute("PRAGMA table_info(cronogramas)")
    columnas = [info[1] for info in cursor.fetchall()]
    if 'ganador' not in columnas:
        cursor.execute("ALTER TABLE cronogramas ADD COLUMN ganador TEXT DEFAULT ''")
    if 'fase' not in columnas:
        cursor.execute("ALTER TABLE cronogramas ADD COLUMN fase TEXT DEFAULT 'Fase 1'")
    if 'etapa' not in columnas:
        cursor.execute("ALTER TABLE cronogramas ADD COLUMN etapa TEXT DEFAULT ''")

    # Tabla de configuración para estado de publicación y ajustes generales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('cronograma_publicado', '0')")
    con.commit()

def obtener_configuracion(con, clave, default=''):
    try:
        r = con.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
        return r['valor'] if r else default
    except Exception:
        return default

def establecer_configuracion(con, clave, valor):
    con.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, str(valor)))
    con.commit()

def hora_a_minutos(h_str):
    if not h_str:
        return 0
    h_str = h_str.strip().upper()
    try:
        dt = datetime.strptime(h_str, "%I:%M %p")
        return dt.hour * 60 + dt.minute
    except Exception:
        try:
            dt = datetime.strptime(h_str, "%H:%M")
            return dt.hour * 60 + dt.minute
        except Exception:
            return 0

def clasificar_etapa(nivel_str):
    if not nivel_str:
        return 'Primaria'
    n = str(nivel_str).lower()
    if 'grado' in n:
        return 'Primaria'
    elif 'año' in n or 'ano' in n:
        return 'Bachillerato'
    return 'Primaria'

def validar_franja_etapa(etapa, hora_inicio, hora_fin):
    """
    Primaria: 07:45 AM (465 min) a 10:30 AM (630 min).
    Bachillerato: 11:00 AM (660 min) a 01:45 PM (825 min).
    """
    ini = hora_a_minutos(hora_inicio)
    fin = hora_a_minutos(hora_fin)
    if etapa == 'Primaria':
        return (ini >= 465 and fin <= 630 and ini < fin)
    elif etapa == 'Bachillerato':
        return (ini >= 660 and fin <= 825 and ini < fin)
    return True

# ============================================================
# VALIDACIÓN ESTRICTA ANTI-COLISIONES (REGLA 2)
# - Regla de Cancha: Dos partidos nunca pueden compartir la misma cancha en el mismo bloque y día.
# - Regla de Grupo: Un mismo año/sección NUNCA puede estar asignado a dos partidos a la misma hora.
# ============================================================
def normalizar_cadena(s):
    if not s:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return ' '.join(s.split())

def extraer_equipos(texto):
    if not texto:
        return []
    partes = re.split(r'\s+vs\.?\s+|\s+-\s+', str(texto), flags=re.IGNORECASE)
    return [p.strip() for p in partes if p.strip()]

def hay_conflicto_partido(con, dia, cancha, hora_inicio, hora_fin, equipo1=None, equipo2=None, exclude_id=None):
    min_ini = hora_a_minutos(hora_inicio)
    min_fin = hora_a_minutos(hora_fin)

    query = "SELECT id, hora_inicio, hora_fin, cancha, enfrentamiento FROM cronogramas WHERE dia = ?"
    params = [dia]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    filas = con.execute(query, params).fetchall()

    norm_eqs = set()
    if equipo1:
        norm_eqs.add(normalizar_cadena(equipo1))
    if equipo2:
        norm_eqs.add(normalizar_cadena(equipo2))

    cancha_norm = normalizar_cadena(cancha)

    for f in filas:
        f_ini = hora_a_minutos(f['hora_inicio'])
        f_fin = hora_a_minutos(f['hora_fin'])

        # Hay solapamiento de bloque horario
        if max(min_ini, f_ini) < min(min_fin, f_fin):
            # 1. Conflicto de cancha
            if normalizar_cadena(f['cancha']) == cancha_norm:
                return True, f"Cancha ocupada: La {cancha} ya está reservada el {dia} de {f['hora_inicio']} a {f['hora_fin']}."

            # 2. Conflicto de grupo (año/sección)
            ocupados = [normalizar_cadena(x) for x in extraer_equipos(f['enfrentamiento'])]
            for eq in norm_eqs:
                if eq in ocupados:
                    return True, f"Conflicto de grupo: '{eq.title()}' ya tiene otro partido el {dia} a las {f['hora_inicio']} en {f['cancha']}."

    return False, None

def buscar_horario_disponible(con, etapa, cancha, dias_permitidos, equipo1=None, equipo2=None, preferir_dia=None, start_offset=0):
    """
    Busca bloque y día disponible que cumpla estrictamente:
    - Franja horaria de la etapa.
    - Cancha desocupada.
    - Ninguno de los dos equipos ocupados en otro deporte a esa misma hora.
    - Distribución equilibrada entre los días permitidos.
    """
    bloques_etapa = [b for b in BLOQUES_HORARIOS if b['etapa'] == etapa]

    slots = []
    for b in bloques_etapa:
        for d in dias_permitidos:
            slots.append((d, b))

    if preferir_dia and preferir_dia in dias_permitidos:
        slots_ordenados = sorted(slots, key=lambda x: (0 if x[0] == preferir_dia else 1))
    else:
        slots_ordenados = slots

    n = len(slots_ordenados)
    for offset in range(n):
        dia, b = slots_ordenados[(start_offset + offset) % n]
        conflicto, _ = hay_conflicto_partido(
            con, dia, cancha, b['hora_inicio'], b['hora_fin'], equipo1, equipo2
        )
        if not conflicto:
            return dia, b['hora_inicio'], b['hora_fin']

    return None, None, None

def construir_matriz_cronograma(filas):
    matriz = []
    for b in BLOQUES_HORARIOS:
        fila = {
            'id': b['id'],
            'hora_inicio': b['hora_inicio'],
            'hora_fin': b['hora_fin'],
            'etiqueta': b['etiqueta'],
            'etapa': b['etapa'],
            'tipo': b['tipo'],
            'badge': b['badge'],
            'nombre_bloque': b['nombre_bloque'],
            'celdas': {d: [] for d in DIAS_SEMANA}
        }
        b_ini = hora_a_minutos(b['hora_inicio'])
        b_fin = hora_a_minutos(b['hora_fin'])

        for item in filas:
            dia = item['dia']
            if dia not in fila['celdas']:
                continue
            item_bloque = f"{item['hora_inicio']} - {item['hora_fin']}"
            if item_bloque == b['etiqueta'] or item['hora_inicio'] == b['hora_inicio']:
                fila['celdas'][dia].append(dict(item))
            else:
                p_ini = hora_a_minutos(item['hora_inicio'])
                p_fin = hora_a_minutos(item['hora_fin'])
                if (b_ini <= p_ini < b_fin) or (max(b_ini, p_ini) < min(b_fin, p_fin)):
                    item_dict = dict(item)
                    if item_dict not in fila['celdas'][dia]:
                        fila['celdas'][dia].append(item_dict)
        matriz.append(fila)
    return matriz

# ============================================================
# RUTA LOGIN
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        try:
            con = get_db()
            usuario = con.execute(
                "SELECT * FROM usuarios WHERE username = ? AND password = ?",
                (username, password)
            ).fetchone()
            con.close()
        except Exception:
            flash('Error al conectar con la base de datos.', 'error')
            return redirect('/login')

        if usuario:
            session['admin'] = True
            session['username'] = username
            flash(f'¡Bienvenido(a), {username}! Acceso concedido al panel docente.', 'success')
            return redirect('/admin')
        else:
            flash('Usuario o contraseña incorrectos. Verifica tus credenciales.', 'error')
            return redirect('/login')
    return render_template('login.html')

# ============================================================
# RUTA PRINCIPAL (PORTAL PÚBLICO - REGLA 3: SIN CRONOGRAMA)
# ============================================================
@app.route('/')
def index():
    try:
        con = get_db()
        asegurar_esquema_bd(con)
        deportes_db = con.execute("SELECT nombre FROM deportes").fetchall()
        inscritos_raw = con.execute(
            "SELECT deporte, COUNT(*) FROM inscripciones GROUP BY deporte"
        ).fetchall()
        inscritos_por_deporte = {r[0]: r[1] for r in inscritos_raw}

        deportes = []
        for d in deportes_db:
            nombre_dep = d['nombre']
            inscritos = inscritos_por_deporte.get(nombre_dep, 0)
            deportes.append({
                'nombre': nombre_dep,
                'icono': ICONOS.get(nombre_dep, '🏅'),
                'descripcion': DESCRIPCIONES.get(nombre_dep, 'Disciplina deportiva oficial'),
                'inscritos': inscritos,
                'cupos': max(0, CUPO_MAXIMO - inscritos),
                'total_cupos': CUPO_MAXIMO
            })

        todos_niveles = con.execute("SELECT nombre FROM niveles").fetchall()
        primaria = [n for n in todos_niveles if "Grado" in n['nombre']]
        bachillerato = [n for n in todos_niveles if "Año" in n['nombre']]
        total_inscritos = con.execute("SELECT COUNT(*) FROM inscripciones").fetchone()[0]
        cronograma = con.execute(
            "SELECT * FROM cronogramas ORDER BY CASE dia "
            "WHEN 'Lunes' THEN 1 WHEN 'Martes' THEN 2 WHEN 'Miércoles' THEN 3 "
            "WHEN 'Jueves' THEN 4 WHEN 'Viernes' THEN 5 END, hora_inicio"
        ).fetchall()
        matriz_cronograma = construir_matriz_cronograma(cronograma)
        cronograma_publicado = (obtener_configuracion(con, 'cronograma_publicado', '0') == '1')
        con.close()
    except Exception:
        deportes, primaria, bachillerato, total_inscritos = [], [], [], 0
        cronograma, matriz_cronograma = [], []
        cronograma_publicado = False

    return render_template(
        'index.html',
        deportes=deportes,
        primaria=primaria,
        bachillerato=bachillerato,
        total_inscritos=total_inscritos,
        cronograma=cronograma,
        matriz_cronograma=matriz_cronograma,
        cronograma_publicado=cronograma_publicado,
        dias=DIAS_SEMANA
    )

# ============================================================
# RUTA REGISTRAR INSCRIPCIÓN
# ============================================================
@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form.get('nombre', '').strip()
    cedula = request.form.get('cedula', '').strip()
    nivel_raw = request.form.get('nivel', '').strip()
    deporte = request.form.get('deporte', '').strip()

    if not (nombre and cedula and nivel_raw and deporte):
        flash('Por favor completa todos los campos del formulario.', 'error')
        return redirect('/')

    nivel = NORMALIZACION_NIVELES.get(nivel_raw.lower().replace(' ', '_'), nivel_raw)
    if deporte == 'Fútbol':
        deporte = 'Fútbol Sala'

    try:
        con = get_db()
        dup = con.execute(
            "SELECT 1 FROM inscripciones WHERE cedula = ? AND deporte = ?",
            (cedula, deporte)
        ).fetchone()
        if dup:
            flash(f'Ya posees una inscripción registrada en {deporte}.', 'error')
            con.close()
            return redirect('/')

        total = con.execute(
            "SELECT COUNT(*) FROM inscripciones WHERE deporte = ?", (deporte,)
        ).fetchone()[0]
        if total >= CUPO_MAXIMO:
            flash(f'Lo sentimos, los cupos para {deporte} ya están completos.', 'error')
            con.close()
            return redirect('/')

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
        con.execute(
            "INSERT INTO inscripciones (nombre, cedula, nivel, deporte, fecha) VALUES (?,?,?,?,?)",
            (nombre, cedula, nivel, deporte, fecha_actual)
        )
        con.commit()
        con.close()
        flash(f'¡Inscripción exitosa! Te has registrado en {deporte}.', 'success')
    except Exception:
        flash('Ocurrió un error al procesar tu inscripción.', 'error')

    return redirect('/')

# ============================================================
# RUTA ADMIN (PANEL DOCENTE - GESTIÓN Y CRONOGRAMA EXCLUSIVO)
# ============================================================
@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash('Acceso restringido. Inicia sesión como docente.', 'error')
        return redirect('/login')

    tab_activa = request.args.get('tab', 'inscritos')

    try:
        con = get_db()
        asegurar_esquema_bd(con)
        datos = con.execute(
            "SELECT id, nombre, cedula, nivel, deporte, fecha FROM inscripciones ORDER BY id DESC"
        ).fetchall()
        total_inscritos = len(datos)

        top_row = con.execute(
            "SELECT deporte, COUNT(*) as c FROM inscripciones GROUP BY deporte ORDER BY c DESC LIMIT 1"
        ).fetchone()
        top_deporte = top_row['deporte'] if top_row else "Ninguno"
        top_deporte_count = top_row['c'] if top_row else 0

        deportes_db = [d['nombre'] for d in con.execute("SELECT nombre FROM deportes").fetchall()]
        total_capacidad = len(deportes_db) * CUPO_MAXIMO
        cupos_restantes = max(0, total_capacidad - total_inscritos)

        niveles_db = [n['nombre'] for n in con.execute("SELECT nombre FROM niveles").fetchall()]

        cronograma = con.execute(
            "SELECT * FROM cronogramas ORDER BY CASE dia "
            "WHEN 'Lunes' THEN 1 WHEN 'Martes' THEN 2 WHEN 'Miércoles' THEN 3 "
            "WHEN 'Jueves' THEN 4 WHEN 'Viernes' THEN 5 END, hora_inicio"
        ).fetchall()
        matriz_cronograma = construir_matriz_cronograma(cronograma)
        cronograma_publicado = (obtener_configuracion(con, 'cronograma_publicado', '0') == '1')

        con.close()
    except Exception:
        datos, total_inscritos = [], 0
        top_deporte, top_deporte_count = "Ninguno", 0
        deportes_db, niveles_db = [], []
        total_capacidad, cupos_restantes = 0, 0
        cronograma, matriz_cronograma = [], []
        cronograma_publicado = False

    return render_template(
        'admin.html',
        lista=datos,
        total=total_inscritos,
        top_deporte=top_deporte,
        top_deporte_count=top_deporte_count,
        total_capacidad=total_capacidad,
        cupos_restantes=cupos_restantes,
        deportes=deportes_db,
        niveles=niveles_db,
        cronograma=cronograma,
        matriz_cronograma=matriz_cronograma,
        cronograma_publicado=cronograma_publicado,
        bloques_horarios=BLOQUES_HORARIOS,
        dias=DIAS_SEMANA,
        usuario_actual=session.get('username', 'Profesor'),
        tab_activa=tab_activa
    )

# ============================================================
# ELIMINAR INSCRIPCIÓN (PROTEGIDA)
# ============================================================
@app.route('/admin/eliminar/<int:id>', methods=['POST', 'GET'])
def eliminar_inscripcion(id):
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')
    try:
        con = get_db()
        alumno = con.execute("SELECT nombre, deporte FROM inscripciones WHERE id = ?", (id,)).fetchone()
        if alumno:
            con.execute("DELETE FROM inscripciones WHERE id = ?", (id,))
            con.commit()
            flash(f'Inscripción de {alumno["nombre"]} eliminada. Cupo liberado en {alumno["deporte"]}.', 'success')
        else:
            flash('Registro no encontrado.', 'error')
        con.close()
    except Exception:
        flash('Error al eliminar la inscripción.', 'error')
    return redirect('/admin?tab=inscritos')

# ============================================================
# EXPORTAR INSCRIPCIONES CSV
# ============================================================
@app.route('/admin/exportar')
def exportar_csv():
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')
    try:
        con = get_db()
        filas = con.execute(
            "SELECT id, cedula, nombre, nivel, deporte, fecha FROM inscripciones ORDER BY id ASC"
        ).fetchall()
        con.close()
    except Exception:
        flash('Error al generar el archivo CSV.', 'error')
        return redirect('/admin?tab=inscritos')

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Nro', 'Cédula', 'Nombre Completo', 'Grado / Año', 'Disciplina', 'Fecha y Hora'])
    for f in filas:
        writer.writerow([f['id'], f['cedula'], f['nombre'], f['nivel'], f['deporte'], f['fecha']])

    csv_bytes = output.getvalue().encode('utf-8-sig')

    return Response(
        csv_bytes,
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": "attachment; filename=Inscripciones_Semana_Deportiva.csv"
        }
    )

# ============================================================
# EXPORTAR CRONOGRAMA CSV
# ============================================================
@app.route('/admin/exportar_cronograma')
def exportar_cronograma_csv():
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')
    try:
        con = get_db()
        asegurar_esquema_bd(con)
        filas = con.execute(
            "SELECT * FROM cronogramas ORDER BY CASE dia "
            "WHEN 'Lunes' THEN 1 WHEN 'Martes' THEN 2 WHEN 'Miércoles' THEN 3 "
            "WHEN 'Jueves' THEN 4 WHEN 'Viernes' THEN 5 END, hora_inicio"
        ).fetchall()
        con.close()
    except Exception:
        flash('Error al exportar el cronograma.', 'error')
        return redirect('/admin?tab=cronograma')

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Nro', 'Día', 'Hora Inicio', 'Hora Fin', 'Disciplina', 'Enfrentamiento', 'Cancha Asignada', 'Fase', 'Etapa', 'Estado', 'Ganador'])
    for f in filas:
        writer.writerow([
            f['id'],
            f['dia'],
            f['hora_inicio'],
            f['hora_fin'],
            f['disciplina'],
            f['enfrentamiento'],
            f['cancha'],
            f['fase'] if f['fase'] else 'Fase 1',
            f['etapa'] if f['etapa'] else '',
            f['estado'] if f['estado'] else 'pendiente',
            f['ganador'] if f['ganador'] else 'Por definir'
        ])

    csv_bytes = output.getvalue().encode('utf-8-sig')

    return Response(
        csv_bytes,
        headers={
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": "attachment; filename=Cronograma_Semana_Deportiva.csv"
        }
    )

# ============================================================
# AGREGAR PARTIDO MANUAL AL CRONOGRAMA (PROTEGIDA - REGLA 2)
# ============================================================
@app.route('/admin/cronograma/agregar', methods=['POST'])
def agregar_partido():
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')

    disciplina = request.form.get('disciplina', '').strip() or 'Fútbol Sala'
    cancha = request.form.get('cancha', '').strip() or CANCHAS.get(disciplina, 'Cancha Múltiple')
    dia = request.form.get('dia', '').strip()
    bloque = request.form.get('bloque_horario', '').strip()
    equipo1 = request.form.get('equipo1', '').strip()
    equipo2 = request.form.get('equipo2', '').strip()
    enfrentamiento_raw = request.form.get('enfrentamiento', '').strip()

    if equipo1 and equipo2:
        enfrentamiento = f"{equipo1} vs {equipo2}"
    elif enfrentamiento_raw:
        enfrentamiento = enfrentamiento_raw
    elif equipo1:
        enfrentamiento = equipo1
    else:
        enfrentamiento = "Encuentro Deportivo"

    etapa = clasificar_etapa(equipo1 or equipo2 or enfrentamiento)

    if dia in ('', 'aleatorio'):
        dia = random.choice(DIAS_SEMANA)

    bloques_etapa = [b for b in BLOQUES_HORARIOS if b['etapa'] == etapa]
    if not bloques_etapa:
        bloques_etapa = [b for b in BLOQUES_HORARIOS if b['etapa'] != 'Receso']

    if bloque == 'aleatorio':
        elegido = random.choice(bloques_etapa)
        h_ini, h_fin = elegido['hora_inicio'], elegido['hora_fin']
    elif ' - ' in bloque:
        partes = bloque.split(' - ')
        h_ini, h_fin = partes[0].strip(), partes[1].strip()
    else:
        elegido = bloques_etapa[0]
        h_ini, h_fin = elegido['hora_inicio'], elegido['hora_fin']

    # REGLA 2: Verificación estricta de franja horaria
    if not validar_franja_etapa(etapa, h_ini, h_fin):
        if etapa == 'Primaria':
            flash('Restricción horaria violada: Los juegos de Primaria SOLO pueden disputarse entre 07:45 AM y 10:30 AM.', 'error')
        else:
            flash('Restricción horaria violada: Los juegos de Bachillerato SOLO pueden disputarse entre 11:00 AM y 01:45 PM.', 'error')
        return redirect('/admin?tab=cronograma')

    try:
        con = get_db()
        asegurar_esquema_bd(con)
        conflicto, motivo = hay_conflicto_partido(con, dia, cancha, h_ini, h_fin, equipo1, equipo2)
        if conflicto:
            flash(f'Conflicto de programación: {motivo}', 'error')
            con.close()
            return redirect('/admin?tab=cronograma')

        con.execute(
            "INSERT INTO cronogramas (disciplina, dia, hora_inicio, hora_fin, enfrentamiento, cancha, estado, ganador, fase, etapa) "
            "VALUES (?,?,?,?,?,?, 'pendiente', '', 'Manual', ?)",
            (disciplina, dia, h_ini, h_fin, enfrentamiento, cancha, etapa)
        )
        con.commit()
        con.close()
        flash(f'Juego de {disciplina} ({enfrentamiento}) asignado el {dia} ({h_ini} - {h_fin}).', 'success')
    except Exception as e:
        flash(f'Error al agregar el partido al horario: {str(e)}', 'error')

    return redirect('/admin?tab=cronograma')

# ============================================================
# ELIMINAR PARTIDO DEL CRONOGRAMA (PROTEGIDA)
# ============================================================
@app.route('/admin/cronograma/eliminar/<int:id>', methods=['POST', 'GET'])
def eliminar_partido(id):
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')
    try:
        con = get_db()
        partido = con.execute("SELECT disciplina, dia FROM cronogramas WHERE id = ?", (id,)).fetchone()
        if partido:
            con.execute("DELETE FROM cronogramas WHERE id = ?", (id,))
            con.commit()
            flash(f'Juego de {partido["disciplina"]} del {partido["dia"]} eliminado del cronograma.', 'success')
        else:
            flash('Juego no encontrado.', 'error')
        con.close()
    except Exception:
        flash('Error al eliminar el partido.', 'error')
    return redirect('/admin?tab=cronograma')

# ============================================================
# TOGGLE PUBLICACIÓN DEL CRONOGRAMA (PROTEGIDA - REGLA DE VISIBILIDAD)
# ============================================================
@app.route('/toggle_publicacion', methods=['POST', 'GET'])
@app.route('/admin/cronograma/toggle_publicacion', methods=['POST', 'GET'])
def toggle_publicacion():
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')

    try:
        con = get_db()
        asegurar_esquema_bd(con)
        estado_actual = obtener_configuracion(con, 'cronograma_publicado', '0')
        nuevo_estado = '0' if estado_actual == '1' else '1'
        establecer_configuracion(con, 'cronograma_publicado', nuevo_estado)
        con.close()

        if nuevo_estado == '1':
            flash('El cronograma ha sido PUBLICADO oficialmente y ahora es visible en el portal para estudiantes y representantes.', 'success')
        else:
            flash('El cronograma ha sido OCULTADO del portal público (guardado en modo Borrador Privado).', 'info')
    except Exception as e:
        flash(f'Error al cambiar el estado de publicación: {str(e)}', 'error')

    return redirect('/admin?tab=cronograma')

# ============================================================
# GENERACIÓN DE FIXTURE - FASE INICIAL (LUNES Y MARTES)
# REGLA 1: Programa la fase inicial equilibrada en AL MENOS 2 DÍAS (Lunes y Martes).
#          - Primaria: llena los bloques de 07:45 AM a 10:30 AM entre Lunes y Martes.
#          - Bachillerato: llena los bloques de 11:00 AM a 01:45 PM entre Lunes y Martes.
# REGLA 2: Anti-colisiones estrictas de cancha y de grupo/sección.
# ============================================================
@app.route('/generar_cronograma', methods=['POST', 'GET'])
def generar_cronograma():
    if not session.get('admin'):
        return redirect('/login')

    try:
        con = get_db()
        asegurar_esquema_bd(con)

        # 1. Limpiar cronograma existente
        con.execute("DELETE FROM cronogramas")

        # 2. Consultar inscripciones REALES
        inscripciones_db = con.execute(
            "SELECT DISTINCT deporte, nivel FROM inscripciones WHERE deporte IS NOT NULL AND nivel IS NOT NULL ORDER BY deporte, nivel"
        ).fetchall()

        deportes_equipos = {}
        for row in inscripciones_db:
            dep = row['deporte']
            niv = row['nivel'].strip()
            if not dep or not niv:
                continue
            etapa = clasificar_etapa(niv)
            if dep not in deportes_equipos:
                deportes_equipos[dep] = {'Primaria': [], 'Bachillerato': []}
            if niv not in deportes_equipos[dep][etapa]:
                deportes_equipos[dep][etapa].append(niv)

        # 3. Construir lista de todos los primeros enfrentamientos por etapa
        partidos_primaria = []
        partidos_bachillerato = []

        for dep, etapas in deportes_equipos.items():
            cancha = CANCHAS.get(dep, 'Cancha Múltiple')

            for etapa, equipos in etapas.items():
                if len(equipos) < 2:
                    continue

                # Emparejamiento de equipos reales
                for i in range(0, len(equipos) - 1, 2):
                    eq1 = equipos[i]
                    eq2 = equipos[i+1]
                    item_partido = {
                        'disciplina': dep,
                        'etapa': etapa,
                        'equipo1': eq1,
                        'equipo2': eq2,
                        'enfrentamiento': f"{eq1} vs {eq2}",
                        'cancha': cancha
                    }
                    if etapa == 'Primaria':
                        partidos_primaria.append(item_partido)
                    else:
                        partidos_bachillerato.append(item_partido)

                # Si hay número impar de equipos (>= 3), cruzar al último con el primero en triangular
                if len(equipos) % 2 == 1 and len(equipos) >= 3:
                    item_partido = {
                        'disciplina': dep,
                        'etapa': etapa,
                        'equipo1': equipos[-1],
                        'equipo2': equipos[0],
                        'enfrentamiento': f"{equipos[-1]} vs {equipos[0]}",
                        'cancha': cancha
                    }
                    if etapa == 'Primaria':
                        partidos_primaria.append(item_partido)
                    else:
                        partidos_bachillerato.append(item_partido)

        partidos_generados = 0
        partidos_lunes = 0
        partidos_martes = 0

        dias_fase_1 = ['Lunes', 'Martes']
        bloques_primaria = [b for b in BLOQUES_HORARIOS if b['etapa'] == 'Primaria']
        bloques_bachillerato = [b for b in BLOQUES_HORARIOS if b['etapa'] == 'Bachillerato']

        # Slots balanceados alternando días y bloques de la jornada
        slots_p = []
        for b in bloques_primaria:
            slots_p.append(('Lunes', b))
            slots_p.append(('Martes', b))

        slots_b = []
        for b in bloques_bachillerato:
            slots_b.append(('Lunes', b))
            slots_b.append(('Martes', b))

        # 4. Programar Primaria: distribuidos en Lunes y Martes (07:45 AM - 10:30 AM)
        for idx, m in enumerate(partidos_primaria):
            for offset in range(len(slots_p)):
                dia_cand, b_cand = slots_p[(idx + offset) % len(slots_p)]
                conflicto, _ = hay_conflicto_partido(
                    con, dia_cand, m['cancha'], b_cand['hora_inicio'], b_cand['hora_fin'],
                    equipo1=m['equipo1'], equipo2=m['equipo2']
                )
                if not conflicto:
                    con.execute(
                        "INSERT INTO cronogramas (disciplina, dia, hora_inicio, hora_fin, enfrentamiento, cancha, estado, ganador, fase, etapa) "
                        "VALUES (?,?,?,?,?,?, 'pendiente', '', 'Fase 1', 'Primaria')",
                        (m['disciplina'], dia_cand, b_cand['hora_inicio'], b_cand['hora_fin'], m['enfrentamiento'], m['cancha'])
                    )
                    partidos_generados += 1
                    if dia_cand == 'Lunes': partidos_lunes += 1
                    elif dia_cand == 'Martes': partidos_martes += 1
                    break

        # 5. Programar Bachillerato: distribuidos en Lunes y Martes (11:00 AM - 01:45 PM)
        for idx, m in enumerate(partidos_bachillerato):
            for offset in range(len(slots_b)):
                dia_cand, b_cand = slots_b[(idx + offset) % len(slots_b)]
                conflicto, _ = hay_conflicto_partido(
                    con, dia_cand, m['cancha'], b_cand['hora_inicio'], b_cand['hora_fin'],
                    equipo1=m['equipo1'], equipo2=m['equipo2']
                )
                if not conflicto:
                    con.execute(
                        "INSERT INTO cronogramas (disciplina, dia, hora_inicio, hora_fin, enfrentamiento, cancha, estado, ganador, fase, etapa) "
                        "VALUES (?,?,?,?,?,?, 'pendiente', '', 'Fase 1', 'Bachillerato')",
                        (m['disciplina'], dia_cand, b_cand['hora_inicio'], b_cand['hora_fin'], m['enfrentamiento'], m['cancha'])
                    )
                    partidos_generados += 1
                    if dia_cand == 'Lunes': partidos_lunes += 1
                    elif dia_cand == 'Martes': partidos_martes += 1
                    break

        con.commit()
        con.close()

        if partidos_generados > 0:
            flash(
                f'¡Fixture inicial generado con éxito! Se programaron {partidos_generados} encuentros repartidos entre Lunes ({partidos_lunes} juegos) y Martes ({partidos_martes} juegos), llenando los bloques de Primaria (07:45 - 10:30 AM) y Bachillerato (11:00 AM - 01:45 PM) sin colisiones de cancha ni grupos.',
                'success'
            )
        else:
            flash(
                'No se generaron partidos: Se requieren al menos 2 secciones o grados inscritos en la misma disciplina y etapa para poder crear un juego.',
                'error'
            )
    except Exception as e:
        flash(f'Error al generar el fixture: {str(e)}', 'error')

    return redirect('/admin?tab=cronograma')

# ============================================================
# PERSISTENCIA DE GANADOR (REGLAS 3 Y 4)
# Guarda de inmediato en la base de datos: estado = 'finalizado' y ganador = '[Equipo]'.
# Soporta tanto respuesta JSON inmediata para AJAX como redirect tradicional.
# ============================================================
@app.route('/admin/cronograma/marcar_ganador/<int:id>', methods=['POST'])
def marcar_ganador(id):
    if not session.get('admin'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')

    ganador = request.form.get('ganador', '').strip()
    if not ganador and request.is_json:
        data = request.get_json(silent=True) or {}
        ganador = data.get('ganador', '').strip()

    if not ganador:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Debes especificar el equipo ganador.'}), 400
        flash('Debes especificar el equipo ganador.', 'error')
        return redirect('/admin?tab=cronograma')

    try:
        con = get_db()
        asegurar_esquema_bd(con)
        partido = con.execute("SELECT * FROM cronogramas WHERE id = ?", (id,)).fetchone()
        if not partido:
            con.close()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'error': 'Partido no encontrado.'}), 404
            flash('Partido no encontrado.', 'error')
            return redirect('/admin?tab=cronograma')

        con.execute(
            "UPDATE cronogramas SET ganador = ?, estado = 'finalizado' WHERE id = ?",
            (ganador, id)
        )
        con.commit()
        con.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({
                'success': True,
                'id': id,
                'ganador': ganador,
                'disciplina': partido['disciplina'],
                'mensaje': f'¡Ganador registrado! {ganador}'
            })

        flash(f'¡Victoria registrada! Ganador: {ganador} ({partido["disciplina"]}).', 'success')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error al registrar el ganador: {str(e)}', 'error')

    return redirect('/admin?tab=cronograma')

# ============================================================
# REVERTIR GANADOR A PENDIENTE (CONTROL DE ERRORES)
# ============================================================
@app.route('/admin/cronograma/revertir_resultado/<int:id>', methods=['POST'])
def revertir_resultado(id):
    if not session.get('admin'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')

    try:
        con = get_db()
        con.execute(
            "UPDATE cronogramas SET ganador = '', estado = 'pendiente' WHERE id = ?",
            (id,)
        )
        con.commit()
        con.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'id': id, 'mensaje': 'Resultado revertido a pendiente.'})

        flash('Resultado revertido. El partido vuelve a estar en estado pendiente.', 'info')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error al revertir el resultado: {str(e)}', 'error')

    return redirect('/admin?tab=cronograma')

# ============================================================
# GENERAR SIGUIENTE RONDA (MIÉRCOLES A VIERNES - REGLA 3)
# - Toma a los equipos clasificados tras definirse los ganadores de la fase inicial (Lunes y Martes).
# - Programa los cruces de Semifinal / Final / Repechaje estrictamente para MIÉRCOLES, JUEVES O VIERNES.
# - Valida franjas horarias y anti-colisiones de cancha y grupo.
# ============================================================
@app.route('/admin/cronograma/siguiente_fase', methods=['POST'])
def siguiente_fase():
    if not session.get('admin'):
        flash('Acceso no autorizado.', 'error')
        return redirect('/login')

    try:
        con = get_db()
        asegurar_esquema_bd(con)

        dias_siguiente_fase = ['Miércoles', 'Jueves', 'Viernes']

        disciplinas_en_juego = [r[0] for r in con.execute("SELECT DISTINCT disciplina FROM cronogramas").fetchall()]

        partidos_creados_total = 0
        disciplinas_pendientes = []
        mensajes_torneo = []

        bloques_primaria = [b for b in BLOQUES_HORARIOS if b['etapa'] == 'Primaria']
        bloques_bachillerato = [b for b in BLOQUES_HORARIOS if b['etapa'] == 'Bachillerato']

        slots_p = []
        for b in bloques_primaria:
            for d in dias_siguiente_fase:
                slots_p.append((d, b))

        slots_b = []
        for b in bloques_bachillerato:
            for d in dias_siguiente_fase:
                slots_b.append((d, b))

        for dep in disciplinas_en_juego:
            cancha = CANCHAS.get(dep, 'Cancha Múltiple')

            for etapa in ['Primaria', 'Bachillerato']:
                partidos_etapa = con.execute(
                    "SELECT * FROM cronogramas WHERE disciplina = ? AND etapa = ? ORDER BY id ASC",
                    (dep, etapa)
                ).fetchall()

                if not partidos_etapa:
                    continue

                # Determinar la fase más reciente
                fases_existentes = set(p['fase'] for p in partidos_etapa if p['fase'])
                ult_fase_num = 1
                for f in fases_existentes:
                    dig = ''.join(c for c in f if c.isdigit())
                    if dig and int(dig) > ult_fase_num:
                        ult_fase_num = int(dig)

                partidos_fase_actual = [p for p in partidos_etapa if f"Fase {ult_fase_num}" in (p['fase'] or '')]
                if not partidos_fase_actual:
                    partidos_fase_actual = partidos_etapa

                # Verificar si todos los partidos de esa fase están finalizados
                pendientes = [p for p in partidos_fase_actual if p['estado'] != 'finalizado' or not p['ganador']]
                if pendientes:
                    disciplinas_pendientes.append(f"{dep} ({etapa}): {len(pendientes)} juego(s) pendiente(s)")
                    continue

                siguiente_num = ult_fase_num + 1
                ya_creada = [p for p in partidos_etapa if f"Fase {siguiente_num}" in (p['fase'] or '')]
                if ya_creada:
                    continue

                # Extraer ganadores y perdedores
                ganadores = [p['ganador'] for p in partidos_fase_actual if p['ganador']]
                perdedores = []
                for p in partidos_fase_actual:
                    enf = p['enfrentamiento']
                    g = p['ganador']
                    if ' vs ' in enf and g:
                        partes = [eq.strip() for eq in enf.split(' vs ')]
                        perd = partes[1] if g == partes[0] else partes[0]
                        perdedores.append(perd)

                nuevos_encuentros = []
                nombre_fase = f"Fase {siguiente_num}"

                if len(ganadores) == 2:
                    nuevos_encuentros.append({
                        'equipo1': ganadores[0],
                        'equipo2': ganadores[1],
                        'enfrentamiento': f"{ganadores[0]} vs {ganadores[1]}",
                        'etiqueta_fase': f"{nombre_fase} - Gran Final"
                    })
                elif len(ganadores) == 3:
                    nuevos_encuentros.append({
                        'equipo1': ganadores[0],
                        'equipo2': ganadores[1],
                        'enfrentamiento': f"{ganadores[0]} vs {ganadores[1]}",
                        'etiqueta_fase': f"{nombre_fase} - Semifinal"
                    })
                    nuevos_encuentros.append({
                        'equipo1': ganadores[2],
                        'equipo2': ganadores[0],
                        'enfrentamiento': f"{ganadores[2]} vs {ganadores[0]}",
                        'etiqueta_fase': f"{nombre_fase} - Triangular Final"
                    })
                elif len(ganadores) >= 4:
                    for i in range(0, len(ganadores) - 1, 2):
                        nuevos_encuentros.append({
                            'equipo1': ganadores[i],
                            'equipo2': ganadores[i+1],
                            'enfrentamiento': f"{ganadores[i]} vs {ganadores[i+1]}",
                            'etiqueta_fase': f"{nombre_fase} - Semifinal"
                        })
                elif len(ganadores) == 1 and len(perdedores) == 1:
                    nuevos_encuentros.append({
                        'equipo1': ganadores[0],
                        'equipo2': perdedores[0],
                        'enfrentamiento': f"{ganadores[0]} vs {perdedores[0]}",
                        'etiqueta_fase': f"{nombre_fase} - Gran Final"
                    })
                elif len(ganadores) == 1:
                    mensajes_torneo.append(f"{ganadores[0]} se ha coronado CAMPEON de {dep} ({etapa}).")

                # Cuadro de Repechaje (Doble Eliminación)
                if len(perdedores) >= 2:
                    for i in range(0, len(perdedores) - 1, 2):
                        nuevos_encuentros.append({
                            'equipo1': perdedores[i],
                            'equipo2': perdedores[i+1],
                            'enfrentamiento': f"{perdedores[i]} vs {perdedores[i+1]}",
                            'etiqueta_fase': f"{nombre_fase} - Repechaje"
                        })

                # Programar los nuevos cruces en Miércoles, Jueves o Viernes
                slots_act = slots_p if etapa == 'Primaria' else slots_b
                for idx_m, enc in enumerate(nuevos_encuentros):
                    for offset in range(len(slots_act)):
                        dia_asig, b_asig = slots_act[(partidos_creados_total + offset) % len(slots_act)]
                        conflicto, _ = hay_conflicto_partido(
                            con, dia_asig, cancha, b_asig['hora_inicio'], b_asig['hora_fin'],
                            equipo1=enc['equipo1'], equipo2=enc['equipo2']
                        )
                        if not conflicto:
                            con.execute(
                                "INSERT INTO cronogramas (disciplina, dia, hora_inicio, hora_fin, enfrentamiento, cancha, estado, ganador, fase, etapa) "
                                "VALUES (?,?,?,?,?,?, 'pendiente', '', ?, ?)",
                                (dep, dia_asig, b_asig['hora_inicio'], b_asig['hora_fin'], enc['enfrentamiento'], cancha, enc['etiqueta_fase'], etapa)
                            )
                            partidos_creados_total += 1
                            break

        con.commit()
        con.close()

        if partidos_creados_total > 0:
            flash(
                f'¡Siguiente Ronda generada con éxito! Se programaron {partidos_creados_total} cruces (Semifinales/Finales/Repechaje) programados entre Miércoles, Jueves y Viernes.',
                'success'
            )
        elif disciplinas_pendientes:
            flash(
                'No se pudo generar la siguiente ronda para algunas disciplinas porque faltan ganadores: ' + ' • '.join(disciplinas_pendientes),
                'warning'
            )
        elif mensajes_torneo:
            flash(' • '.join(mensajes_torneo), 'info')
        else:
            flash('No hay nuevos cruces pendientes por programar para la siguiente ronda.', 'info')

    except Exception as e:
        flash(f'Error al generar la siguiente ronda: {str(e)}', 'error')

    return redirect('/admin?tab=cronograma')

# ============================================================
# LOGOUT
# ============================================================
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect('/login')

# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)