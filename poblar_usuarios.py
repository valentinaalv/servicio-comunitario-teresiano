import sqlite3

def crear_admin():
    conexion = sqlite3.connect("semana_deportiva.db")
    cursor = conexion.cursor()
    
    # Insertamos el usuario admin
    # OJO: En un sistema real esto se hace con contraseñas encriptadas (hashing),
    # pero para tu proyecto de servicio comunitario, esto funcionará perfecto.
    cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", 
                   ("admin", "1234"))
    
    conexion.commit()
    conexion.close()
    print("Usuario 'admin' creado correctamente.")

if __name__ == "__main__":
    crear_admin()