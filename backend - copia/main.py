from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.recomendador import recomendar_destinos
from backend.auth import router as auth_router
from backend.database import crear_base_datos
from backend.uso import obtener_uso, incrementar_uso

import sqlite3
import os

# 👉 Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

DB_PATH = os.path.join(ROOT_DIR, "travel_ai.db")
FRONTEND_PATH = os.path.join(ROOT_DIR, "frontend", "index.html")

app = FastAPI(title="Travel AI API")

crear_base_datos()
app.include_router(auth_router)

# 👉 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ FRONTEND DIRECTO (SIN JINJA)
@app.get("/")
def home():
    return FileResponse(FRONTEND_PATH)


# 🔥 PLAN
def obtener_plan(email):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    cursor.execute("SELECT plan FROM usuarios WHERE email=?", (email,))
    resultado = cursor.fetchone()

    conexion.close()

    if resultado:
        return resultado[0]
    return "free"


# 👉 API
@app.get("/recomendar")
def recomendar(presupuesto: int, tipo: str, email: str = "demo@demo.com"):

    plan = obtener_plan(email)

    if plan == "free":
        uso_actual = obtener_uso(email)

        if uso_actual >= 3:
            return {"error": "Has alcanzado el límite FREE (3 consultas). Pásate a PRO 🚀"}

        incrementar_uso(email)

        resultados = recomendar_destinos(presupuesto, tipo)

        return {
            "plan": "free",
            "consultas_usadas": uso_actual + 1,
            "recomendaciones": resultados
        }

    resultados = recomendar_destinos(presupuesto, tipo)

    return {
        "plan": "pro",
        "recomendaciones": resultados
    }