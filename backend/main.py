import sys
import os
from io import BytesIO

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.consultas import listar_tickets, obtener_ticket, listar_perfiles
from agents.extraction.pipeline import procesar_ticket
from agents.extraction.config import get_gemini_client, get_db_connection

app = FastAPI(title="TFM GenAI in Cloud - API de tickets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = get_gemini_client()
conn = get_db_connection()
cur = conn.cursor()


@app.get("/")
def raiz():
    return {"mensaje": "API de tickets funcionando"}


@app.get("/perfiles")
def get_perfiles():
    return listar_perfiles(cur)


@app.post("/tickets")
def subir_ticket(archivo: UploadFile, perfil_id: int):
    """
    Recibe una imagen de ticket, la procesa completamente
    (extracción, validación, normalización, guardado) y
    devuelve el resultado.
    """
    contenido = archivo.file.read()
    resultado = procesar_ticket(cur, client, BytesIO(contenido), perfil_id)
    return resultado


@app.get("/tickets")
def get_tickets(perfil_id: int, limite: int = 50):
    return listar_tickets(cur, perfil_id, limite)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, perfil_id: int):
    ticket = obtener_ticket(cur, ticket_id, perfil_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket