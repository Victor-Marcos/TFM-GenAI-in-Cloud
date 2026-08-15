import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.extraction.reintentos import llamar_con_reintentos
from backend.dashboard import productos_completo, productos_comprados_juntos

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


def construir_herramientas(cur, perfil_id):
    return [
        StructuredTool.from_function(
            func=lambda: productos_completo(cur, perfil_id),
            name="productos_mas_comprados",
            description="Ranking de productos por frecuencia de compra y por gasto total. Usar para '¿que compro mas?' o '¿en que producto gasto mas?'",
        ),
        StructuredTool.from_function(
            func=lambda: {"productos_juntos": productos_comprados_juntos(cur, perfil_id)},
            name="productos_comprados_juntos",
            description="Pares de productos que se compran frecuentemente en el mismo ticket. Usar para '¿que suelo comprar junto con X?' o '¿que productos compro a la vez?'",
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

def nodo_patrones(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    contexto = formatear_historial(estado.get("historial", []))

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente especializado en habitos de compra. Usa SIEMPRE "
            "las herramientas disponibles para responder con datos reales; nunca "
            "inventes cifras ni nombres de productos."
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