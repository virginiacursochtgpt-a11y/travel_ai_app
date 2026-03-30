import sqlite3
import os
import time

# 👉 Ruta absoluta de la base de datos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "travel_ai.db")


# 🔧 CONEXIÓN CENTRALIZADA (con WAL)
def get_db():
    conexion = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30
    )
    conexion.execute("PRAGMA journal_mode=WAL;")
    conexion.execute("PRAGMA synchronous=NORMAL;")
    return conexion


# 🔁 RETRY PARA EVITAR LOCK
def ejecutar_con_retry(func, retries=5):
    for _ in range(retries):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                time.sleep(0.5)
            else:
                raise
    raise Exception("Database bloqueada tras varios intentos")


# 🏗️ CREAR BASE DE DATOS
def crear_base_datos():

    def operacion():
        conexion = get_db()
        cursor = conexion.cursor()

        # 👉 Tabla de usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            plan TEXT DEFAULT 'free'
        )
        """)

        # 👉 Tabla de uso
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS uso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            consultas INTEGER DEFAULT 0
        )
        """)

        conexion.commit()
        conexion.close()

    ejecutar_con_retry(operacion)