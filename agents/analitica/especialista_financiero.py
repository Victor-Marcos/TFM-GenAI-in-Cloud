import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.dashboard import (
    resumen_general,
    gasto_por_categoria,
    comercios_completo,
    evolucion_completa,
    gasto_por_tipo_ticket,
    ticket_medio_por_categoria,
)

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


def construir_herramientas(cur, perfil_id):
    return [
        StructuredTool.from_function(
            func=lambda: resumen_general(cur, perfil_id),
            name="resumen_general",
            description="Gasto total, numero de tickets, ticket medio, comercios y productos distintos. Usar para preguntas generales tipo '¿cuanto he gastado en total?'",
        ),
        StructuredTool.from_function(
            func=lambda: gasto_por_categoria(cur, perfil_id),
            name="gasto_por_categoria",
            description="Gasto agrupado por categoria de producto (lacteos, carne, combustible...). Usar para '¿en que gasto mas?'",
        ),
        StructuredTool.from_function(
            func=lambda: comercios_completo(cur, perfil_id),
            name="gasto_por_comercio",
            description="Gasto, visitas y ticket medio por cada comercio. Usar para '¿donde compro mas?' o '¿cual es mi comercio favorito?'",
        ),
        StructuredTool.from_function(
            func=lambda: evolucion_completa(cur, perfil_id),
            name="evolucion_temporal",
            description="Evolucion del gasto mes a mes, por dia de la semana, y comparativa mes actual vs anterior.",
        ),
        StructuredTool.from_function(
            func=lambda: {"por_tipo": gasto_por_tipo_ticket(cur, perfil_id)},
            name="gasto_por_tipo_ticket",
            description="Gasto agrupado por tipo de ticket (supermercado, gasolinera, restaurante...). Usar para '¿cuánto gasto en gasolina?' o similar.",
        ),
        StructuredTool.from_function(
            func=lambda: ticket_medio_por_categoria(cur, perfil_id),
            name="ticket_medio_por_categoria",
            description="El importe medio que sueles gastar por compra en cada categoria. Usar para '¿cuanto suelo gastar cada vez que compro carne?'",
        ),
    ]


def nodo_financiero(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente financiero personal. Usa SIEMPRE las herramientas "
            "disponibles para responder con datos reales; nunca inventes cifras. "
            "Si una pregunta necesita varias herramientas, llama a todas las que hagan falta."
        )),
        HumanMessage(content=estado["pregunta"]),
    ]

    respuesta = llm_con_tools.invoke(mensajes)

    if not respuesta.tool_calls:
        return {**estado, "respuesta_especialista": respuesta.content}

    mensajes.append(respuesta)
    mapa_herramientas = {h.name: h for h in herramientas}

    for llamada in respuesta.tool_calls:
        herramienta = mapa_herramientas[llamada["name"]]
        resultado = herramienta.invoke(llamada["args"])
        mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))

    respuesta_final = llm_con_tools.invoke(mensajes)
    return {**estado, "respuesta_especialista": respuesta_final.content}