import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.extraction.reintentos import llamar_con_reintentos
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


def extraer_texto(respuesta):
    """
    El contenido de la respuesta puede venir como string simple o como
    lista de bloques con metadatos. Esta funcion normaliza ambos casos
    a un string limpio.
    """
    if isinstance(respuesta.content, str):
        return respuesta.content
    if isinstance(respuesta.content, list):
        return "".join(
            bloque.get("text", "") for bloque in respuesta.content if isinstance(bloque, dict)
        )
    return str(respuesta.content)


def formatear_historial(historial, max_turnos=4):
    if not historial:
        return ""
    ultimos = historial[-(max_turnos * 2):]
    lineas = [f"{'Usuario' if m['autor'] == 'usuario' else 'Asistente'}: {m['texto']}" for m in ultimos]
    return "\n\nConversación previa (para entender referencias como 'y el mes pasado'):\n" + "\n".join(lineas)

def nodo_financiero(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    contexto = formatear_historial(estado.get("historial", []))

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente financiero personal. Usa SIEMPRE las herramientas "
            "disponibles para responder con datos reales; nunca inventes cifras. "
            "Si una pregunta necesita varias herramientas, llama a todas las que hagan falta."
            f"{contexto}"
        )),
        HumanMessage(content=estado["pregunta"]),
    ]

    respuesta = llamar_con_reintentos(llm_con_tools.invoke, mensajes)

    if not respuesta.tool_calls:
        return {**estado, "respuesta_especialista": extraer_texto(respuesta)}

    mensajes.append(respuesta)
    mapa_herramientas = {h.name: h for h in herramientas}

    for llamada in respuesta.tool_calls:
        try:
            herramienta = mapa_herramientas[llamada["name"]]
            resultado = herramienta.invoke(llamada["args"])
        except KeyError:
            resultado = f"Error: la herramienta '{llamada['name']}' no existe. Las herramientas disponibles son: {list(mapa_herramientas.keys())}"
        except Exception as e:
            resultado = f"Error al ejecutar la herramienta: {e}"
        mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))

    respuesta_final = llamar_con_reintentos(llm_con_tools.invoke, mensajes)
    return {**estado, "respuesta_especialista": extraer_texto(respuesta_final)}