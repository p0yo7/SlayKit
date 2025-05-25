# Run with uvicorn app:app --reload
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import openai
import os
from dotenv import load_dotenv
from modelo_predictivo import all_predictions
import uuid
import json
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pathlib import Path

# === Seguridad con bcrypt ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === Usuarios ===
with open("users.json") as f:
    users = json.load(f)

class LoginInput(BaseModel):
    client_id: str
    password: str

class TokenInput(BaseModel):
    token: str

# === App Setup ===
app = FastAPI(title="API de Gastos Recurrentes y Resumen")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
openai.api_key = os.getenv("openai_key")

try:
    modelo = joblib.load("../modelos/modelo_gastos_recurrentes.pkl")
except FileNotFoundError:
    modelo = None

clientes_df = pd.read_csv("datos/base_clientes_final.csv", parse_dates=["fecha_nacimiento", "fecha_alta"])
transacciones_df = pd.read_csv("datos/base_transacciones_final.csv", parse_dates=["fecha"])
clientes_df.rename(columns={"id": "id_cliente"}, inplace=True)
transacciones_df.rename(columns={"id": "id_cliente"}, inplace=True)

# === Auth ===
def authenticate_token(token: str = Header(...)) -> str:
    tokens = load_tokens()
    print("🧪 Token recibido:", token)
    print("📂 Tokens disponibles:", tokens.keys())
    if token not in tokens:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return tokens[token]  # ⬅️ ya devuelve el client_id

TOKENS_FILE = Path("tokens.json")

def load_tokens():
    if TOKENS_FILE.exists():
        with TOKENS_FILE.open("r") as f:
            return json.load(f)
    return {}

def save_tokens(tokens):
    with TOKENS_FILE.open("w") as f:
        json.dump(tokens, f, indent=4)

class RegisterInput(BaseModel):
    client_id: str
    password: str
@app.post("/register")
def register(data: RegisterInput):
    users_file = Path("users.json")

    # Leer usuarios existentes
    if users_file.exists():
        with users_file.open("r") as f:
            users = json.load(f)
    else:
        users = []

    # Verificar si ya existe
    if any(u["client_id"] == data.client_id for u in users):
        raise HTTPException(status_code=400, detail="El usuario ya existe.")

    # Hashear contraseña
    hashed_password = pwd_context.hash(data.password)

    # Guardar nuevo usuario
    users.append({"client_id": data.client_id, "password": hashed_password})

    with users_file.open("w") as f:
        json.dump(users, f, indent=4)

    return {"mensaje": "Usuario registrado exitosamente"}

@app.post("/login")
def login(data: LoginInput):
    with open("users.json") as f:
        users = json.load(f)

    user = next((u for u in users if u["client_id"] == data.client_id), None)
    if not user or not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    tokens = load_tokens()
    token = str(uuid.uuid4())
    tokens[token] = user["client_id"]
    save_tokens(tokens)


    return {"token": token}

# === Endpoint 1: Predicción de gasto recurrente ===
@app.post("/predict_gastos_recurrentes")
def predict(data: TokenInput):
    tokens = load_tokens()
    if data.token not in tokens:
        raise HTTPException(status_code=401, detail="Token inválido")
    client_id = tokens[data.token]
    resultado = all_predictions(client_id)
    if resultado is None:
        return {"mensaje": "No se encontraron transacciones para este cliente"}
    return resultado

# === Endpoint 2: Wrapped personalizado ===
@app.get("/wrapped_gastos")
def wrapped_gastos(
    cliente_id: str = Depends(authenticate_token),
    desde: str = Query(...),
    hasta: str = Query(...),
    modo: str = Query("giro_comercio", enum=["giro_comercio", "comercio"])
):
    desde = pd.to_datetime(desde)
    hasta = pd.to_datetime(hasta)

    cliente_tx = transacciones_df[
        (transacciones_df["id_cliente"].astype(str) == cliente_id) &
        (transacciones_df["fecha"].between(desde, hasta))
    ]

    if cliente_tx.empty:
        return {"mensaje": "No hay transacciones en el periodo indicado"}

    resumen_gastos = (
        cliente_tx
        .groupby(modo)["monto"]
        .sum()
        .round(2)
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    resumen_categorias = (
        cliente_tx
        .groupby("tipo_venta")["monto"]
        .sum()
        .round(2)
        .to_dict()
    )

    esenciales = cliente_tx[
        cliente_tx["giro_comercio"].str.contains("SERVICIOS|SALUD|TRANSPORTE", case=False, na=False)
    ]
    esenciales_monto = esenciales["monto"].sum()
    total_monto = cliente_tx["monto"].sum()
    subs_monto = total_monto - esenciales_monto

    proporcion = [
        {"tipo": "Esenciales", "valor": round(esenciales_monto, 2)},
        {"tipo": "Suscripciones", "valor": round(subs_monto, 2)},
    ]

    predictibilidad = (
        cliente_tx
        .groupby("giro_comercio")["monto"]
        .std()
        .fillna(0)
        .apply(lambda x: 100 - min(x * 5, 100))
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
        .rename(columns={"giro_comercio": "categoria", "monto": "score"})
        .to_dict(orient="records")
    )

    compra_max = cliente_tx.loc[cliente_tx["monto"].idxmax()]
    fecha_compra = compra_max["fecha"].strftime("%-d de %B")
    monto_compra = round(compra_max["monto"], 2)
    comercio = compra_max["comercio"]

    prompt = (
        f"El usuario hizo su compra más memorable el {fecha_compra}, gastando ${monto_compra:,.2f} en {comercio}. "
        "Escribe una frase breve en español, amigable, tipo marketing, que destaque esta compra como un momento especial."
    )

    try:
        respuesta_ai = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un redactor creativo para una fintech joven."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=80,
            temperature=0.8
        )
        compra_memorable_texto = respuesta_ai["choices"][0]["message"]["content"]
    except Exception as e:
        compra_memorable_texto = f"Error al generar el mensaje: {e}"

    return {
        "cliente_id": cliente_id,
        "rango": f"{desde.date()} a {hasta.date()}",
        "moneda": "MXN",
        "total_gastado": round(total_monto, 2),
        "resumen_gastos": resumen_gastos,
        "resumen_categorias": resumen_categorias,
        "proporcion_essentials_vs_subs": proporcion,
        "predictibilidad_por_categoria": predictibilidad,
        "compra_mas_iconica": {
            "fecha": fecha_compra,
            "comercio": comercio,
            "monto": monto_compra,
            "mensaje": compra_memorable_texto
        }
    }

# === Endpoint 3: Info del Cliente ===
@app.get("/cliente_info")
def cliente_info(token: str = Depends(authenticate_token)):
    cliente_id = load_tokens()[token]
    cliente = clientes_df[clientes_df["id_cliente"] == cliente_id]

    if cliente.empty:
        return {"mensaje": "Cliente no encontrado"}

    cliente = cliente.iloc[0]
    info = {
        "id_cliente": str(cliente["id_cliente"]),
        "fecha_nacimiento": cliente["fecha_nacimiento"].date(),
        "fecha_alta": cliente["fecha_alta"].date(),
        "id_municipio": int(cliente["id_municipio"]),
        "id_estado": int(cliente["id_estado"]),
        "tipo_persona": str(cliente["tipo_persona"]),
        "genero": str(cliente["genero"]),
        "actividad_empresarial": str(cliente["actividad_empresarial"])
    }

    return info

# === Endpoint 4: Resumen de transacciones ===
@app.get("/resumen_transacciones")
def resumen_transacciones(token: str = Depends(authenticate_token), desde: str = Query(...), hasta: str = Query(...)):
    cliente_id = load_tokens()[token]
    desde = pd.to_datetime(desde)
    hasta = pd.to_datetime(hasta)

    transacciones_cliente = transacciones_df[
        (transacciones_df["id_cliente"] == cliente_id) &
        (transacciones_df["fecha"].between(desde, hasta))
    ]

    if transacciones_cliente.empty:
        return {"mensaje": "No hay transacciones en el periodo indicado"}

    resumen = {
        "total_transacciones": len(transacciones_cliente),
        "total_gastado": round(transacciones_cliente["monto"].sum(), 2),
        "promedio_gasto": round(transacciones_cliente["monto"].mean(), 2),
        "max_gasto": round(transacciones_cliente["monto"].max(), 2),
        "min_gasto": round(transacciones_cliente["monto"].min(), 2),
        "moneda": "MXN",
        "rango": f"{desde.date()} a {hasta.date()}"
    }
    return resumen
