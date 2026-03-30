import sqlite3
import os
import time
from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "travel_ai.db")


# 🔧 CONEXIÓN CENTRALIZADA (WAL)
def get_db():
    conexion = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30
    )
    conexion.execute("PRAGMA journal_mode=WAL;")
    conexion.execute("PRAGMA synchronous=NORMAL;")
    return conexion


# 🔁 RETRY PARA BLOQUEOS
def ejecutar_con_retry(func, retries=5):
    for _ in range(retries):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                time.sleep(0.5)
            else:
                raise
    raise HTTPException(status_code=500, detail="Base de datos bloqueada")


# 🔐 REGISTRO
@router.post("/registro")
def registro(email: str, password: str):

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña obligatorios")

    def operacion():
        conexion = get_db()
        cursor = conexion.cursor()

        cursor.execute(
            "INSERT INTO usuarios (email, password) VALUES (?, ?)",
            (email, password)
        )

        conexion.commit()
        conexion.close()

    try:
        ejecutar_con_retry(operacion)
        return {"mensaje": "Usuario creado correctamente"}

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El usuario ya existe")


# 🔐 LOGIN
@router.post("/login")
def login(email: str, password: str):

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña obligatorios")

    conexion = None

    try:
        conexion = get_db()
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE email=? AND password=?",
            (email, password)
        )

        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        return {
            "mensaje": "Login correcto",
            "usuario": {
                "id": usuario[0],
                "email": usuario[1],
                "plan": usuario[3]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conexion:
            conexion.close()


# 🚀 UPGRADE A PRO
@router.post("/upgrade")
def upgrade(email: str):

    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")

    def operacion():
        conexion = get_db()
        cursor = conexion.cursor()

        cursor.execute(
            "UPDATE usuarios SET plan='pro' WHERE email=?",
            (email,)
        )

        conexion.commit()
        conexion.close()

    try:
        ejecutar_con_retry(operacion)
        return {"mensaje": "Usuario actualizado a PRO"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 👤 PERFIL USUARIO
@router.get("/perfil")
def perfil(email: str):

    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")

    conexion = None

    try:
        conexion = get_db()
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT plan FROM usuarios WHERE email=?",
            (email,)
        )
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cursor.execute(
            "SELECT consultas FROM uso WHERE email=?",
            (email,)
        )
        uso = cursor.fetchone()

        consultas = uso[0] if uso else 0

        return {
            "email": email,
            "plan": usuario[0],
            "consultas": consultas
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conexion:
            conexion.close()