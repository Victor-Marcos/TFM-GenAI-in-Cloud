import sys
import os
from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException
from backend.consultas import listar_tickets, obtener_ticket

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, UploadFile
from agents.extraction.pipeline import procesar_ticket
from agents.extraction.config import get_gemini_client, get_db_connection

app = FastAPI(title="TFM GenAI in Cloud - API de tickets")

client = get_gemini_client()
conn = get_db_connection()
cur = conn.cursor()


@app.post("/tickets")
def subir_ticket(archivo: UploadFile):
    """
    Recibe una imagen de ticket, la procesa completamente
    (extracción, validación, normalización, guardado) y
    devuelve el resultado.
    """
    contenido = archivo.file.read()
    resultado = procesar_ticket(cur, client, BytesIO(contenido))
    return resultado


@app.get("/")
def raiz():
    return {"mensaje": "API de tickets funcionando"}


@app.get("/tickets")
def get_tickets(limite: int = 50):
    return listar_tickets(cur, limite)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    ticket = obtener_ticket(cur, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket