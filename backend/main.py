import sys
import os
from io import BytesIO
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.consultas import (
    listar_tickets,
    obtener_ticket,
    listar_perfiles,
    listar_pendientes,
    marcar_como_validado,
    crear_perfil,
    ejecutar_sql_seguro,
    eliminar_perfil,
    obtener_esquema_bbdd,
    actualizar_ticket_completo,
    eliminar_ticket,
)
from backend.dashboard import (
    resumen_general,
    evolucion_completa,
    categorias_completo,
    comercios_completo,
    productos_completo,
    productos_comprados_juntos,
    gasto_por_tipo_ticket,
    calidad_sistema,
)

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



class CorreccionTicket(BaseModel):
    total_corregido: float | None = None

class NuevoPerfil(BaseModel):
    nombre: str
    descripcion: str | None = None

class ConsultaSQL(BaseModel):
    sql: str

class LineaEditada(BaseModel):
    id: int
    descripcion_original: str
    cantidad: float
    precio_unitario: float
    subtotal: float


class TicketCompleto(BaseModel):
    fecha: str
    total: float
    comercio_nombre: str | None = None
    lineas: list[LineaEditada]


@app.patch("/tickets/{ticket_id}/completo")
def actualizar_ticket_endpoint(ticket_id: int, perfil_id: int, datos: TicketCompleto):
    ok = actualizar_ticket_completo(
        cur, ticket_id, perfil_id,
        datos.fecha, datos.total, datos.comercio_nombre,
        [linea.dict() for linea in datos.lineas]
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return {"mensaje": "Ticket actualizado y validado"}


@app.get("/")
def raiz():
    return {"mensaje": "API de tickets funcionando"}


@app.get("/perfiles")
def get_perfiles():
    return listar_perfiles(cur)

@app.post("/perfiles")
def crear_perfil_endpoint(perfil: NuevoPerfil):
    return crear_perfil(cur, perfil.nombre, perfil.descripcion)

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


@app.get("/tickets/pendientes")
def get_pendientes(perfil_id: int):
    return listar_pendientes(cur, perfil_id)


@app.get("/tickets")
def get_tickets(perfil_id: int, limite: int = 50):
    return listar_tickets(cur, perfil_id, limite)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, perfil_id: int):
    ticket = obtener_ticket(cur, ticket_id, perfil_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket

@app.get("/esquema")
def get_esquema():
    return obtener_esquema_bbdd(cur)

@app.patch("/tickets/{ticket_id}/validar")
def validar_manualmente(ticket_id: int, perfil_id: int, correccion: CorreccionTicket):
    ok = marcar_como_validado(cur, ticket_id, perfil_id, correccion.total_corregido)
    if not ok:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return {"mensaje": "Ticket validado"}


@app.post("/consulta-sql")
def consulta_sql_endpoint(consulta: ConsultaSQL):
    try:
        return ejecutar_sql_seguro(cur, consulta.sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/perfiles/{perfil_id}")
def eliminar_perfil_endpoint(perfil_id: int):
    ok = eliminar_perfil(cur, perfil_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return {"mensaje": "Perfil eliminado"}


@app.get("/tickets/{ticket_id}/imagen")
def get_imagen_ticket(ticket_id: int, perfil_id: int):
    ticket = obtener_ticket(cur, ticket_id, perfil_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    ruta_imagen = ticket.get("imagen_path")
    if not ruta_imagen or not os.path.exists(ruta_imagen):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return FileResponse(ruta_imagen)

@app.get("/tickets/{ticket_id}/imagen")
def get_imagen_ticket(ticket_id: int, perfil_id: int):
    ticket = obtener_ticket(cur, ticket_id, perfil_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    ruta_imagen = ticket.get("imagen_path")
    if not ruta_imagen or not os.path.exists(ruta_imagen):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return FileResponse(ruta_imagen)


@app.delete("/tickets/{ticket_id}")
def eliminar_ticket_endpoint(ticket_id: int, perfil_id: int):
    ok = eliminar_ticket(cur, ticket_id, perfil_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return {"mensaje": "Ticket eliminado"}

@app.get("/dashboard/resumen")
def get_dashboard_resumen(perfil_id: int):
    return resumen_general(cur, perfil_id)

@app.get("/dashboard/evolucion")
def get_dashboard_evolucion(perfil_id: int):
    return evolucion_completa(cur, perfil_id)

@app.get("/dashboard/categorias")
def get_dashboard_categorias(perfil_id: int):
    return categorias_completo(cur, perfil_id)


@app.get("/dashboard/comercios")
def get_dashboard_comercios(perfil_id: int):
    return comercios_completo(cur, perfil_id)


@app.get("/dashboard/productos")
def get_dashboard_productos(perfil_id: int):
    return productos_completo(cur, perfil_id)


@app.get("/dashboard/patrones")
def get_dashboard_patrones(perfil_id: int):
    return {"productos_juntos": productos_comprados_juntos(cur, perfil_id)}


@app.get("/dashboard/tipos")
def get_dashboard_tipos(perfil_id: int):
    return {"por_tipo": gasto_por_tipo_ticket(cur, perfil_id)}


@app.get("/dashboard/calidad")
def get_dashboard_calidad(perfil_id: int):
    return calidad_sistema(cur, perfil_id)