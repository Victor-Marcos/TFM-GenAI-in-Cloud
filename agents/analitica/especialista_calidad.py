import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.dashboard import calidad_sistema
from backend.consultas import listar_pendientes
from agents.extraction.reintentos import llamar_con_reintentos

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


def construir_herramientas(cur, perfil_id):
    return [
        StructuredTool.from_function(
            func=lambda: calidad_sistema(cur, perfil_id),
            name="calidad_sistema",
            description="Porcentaje de tickets auto-validados sin intervencion manual, y los motivos de revision mas frecuentes. Usar para '¿que tan fiable es el sistema?' o '¿cuantos tickets se han validado solos?'",
        ),
        StructuredTool.from_function(
            func=lambda: listar_pendientes(cur, perfil_id),
            name="tickets_pendientes",
            description="Lista de tickets que todavia estan pendientes de revision manual, con su motivo. Usar para '¿cuantos tickets tengo pendientes de revisar?' o '¿que tickets fallaron?'",
        ),
    ]


def formatear_historial(historial, max_turnos=4):
    if not historial:
        return ""
    ultimos = historial[-(max_turnos * 2):]
    lineas = [f"{'Usuario' if m['autor'] == 'usuario' else 'Asistente'}: {m['texto']}" for m in ultimos]
    return "\n\nConversación previa (para entender referencias como 'y el mes pasado'):\n" + "\n".join(lineas)


def extraer_texto(respuesta):
    if isinstance(respuesta.content, str):
        return respuesta.content
    if isinstance(respuesta.content, list):
        return "".join(
            bloque.get("text", "") for bloque in respuesta.content if isinstance(bloque, dict)
        )
    return str(respuesta.content)


def nodo_calidad(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    contexto = formatear_historial(estado.get("historial", []))

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente que informa sobre la fiabilidad del propio sistema "
            "de gestion de tickets del usuario. Usa SIEMPRE las herramientas "
            "disponibles para responder con datos reales; nunca inventes cifras. "
            "Si la pregunta pide una opinión o valoración sobre la fiabilidad, "
            "ofrécela basándote en los datos reales, dejando claro que es tu "
            "interpretación, no un hecho objetivo."
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