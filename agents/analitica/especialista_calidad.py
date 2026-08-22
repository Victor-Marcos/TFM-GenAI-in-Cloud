import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.dashboard import calidad_sistema
from backend.consultas import listar_pendientes, ejecutar_sql_seguro
from agents.extraction.reintentos import llamar_con_reintentos

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


def construir_herramientas(cur, perfil_id):
    def consulta_respaldo(sql: str):
        if "tickets" in sql.lower() and f"perfil_id = {perfil_id}" not in sql:
            return "Error: falta el filtro WHERE perfil_id = " + str(perfil_id)
        return ejecutar_sql_seguro(cur, sql)

    return [
        StructuredTool.from_function(
            func=lambda: calidad_sistema(cur, perfil_id),
            name="calidad_sistema",
            description="Porcentaje de tickets auto-validados sin intervencion manual, y los motivos de revision mas frecuentes.",
        ),
        StructuredTool.from_function(
            func=lambda: listar_pendientes(cur, perfil_id),
            name="tickets_pendientes",
            description="Lista de tickets todavia pendientes de revision manual, con su motivo.",
        ),
        StructuredTool.from_function(
            func=consulta_respaldo,
            name="consulta_sql_respaldo",
            description=(
                "USAR SOLO si ninguna otra herramienta responde exactamente lo que se "
                "pregunta. Ejecuta un SELECT a medida sobre tickets, lineas_ticket, "
                "productos, comercios, categorias_producto, tipos_ticket. "
                f"DEBE incluir WHERE ... perfil_id = {perfil_id} si toca la tabla tickets."
            ),
        ),
    ]


def formatear_historial(historial, max_turnos=4):
    if not historial:
        return ""
    ultimos = historial[-(max_turnos * 2):]
    lineas = [f"{'Usuario' if m['autor'] == 'usuario' else 'Asistente'}: {m['texto']}" for m in ultimos]
    return "\n\nConversación previa:\n" + "\n".join(lineas)


def extraer_texto(respuesta):
    if isinstance(respuesta.content, str):
        return respuesta.content
    if isinstance(respuesta.content, list):
        return "".join(b.get("text", "") for b in respuesta.content if isinstance(b, dict))
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
            "Si ninguna herramienta especifica encaja, usa consulta_sql_respaldo "
            "antes de responder sin datos. "
            "Si la pregunta pide una opinión o valoración, ofrécela basándote en "
            "los datos reales, dejando claro que es tu interpretación. "
            "No uses formato Markdown (nada de **negrita**, guiones de lista ni numeración); "
            "escribe en texto plano, con saltos de línea simples si necesitas separar ideas."
            f"{contexto}"
        )),
        HumanMessage(content=estado["pregunta"]),
    ]

    respuesta = llamar_con_reintentos(llm_con_tools.invoke, mensajes)

    if not respuesta.tool_calls:
        return {**estado, "respuesta_especialista": extraer_texto(respuesta), "datos_obtenidos": None}

    mensajes.append(respuesta)
    mapa_herramientas = {h.name: h for h in herramientas}

    for llamada in respuesta.tool_calls:
        try:
            herramienta = mapa_herramientas[llamada["name"]]
            resultado = herramienta.invoke(llamada["args"])
        except KeyError:
            resultado = f"Error: herramienta '{llamada['name']}' no existe. Disponibles: {list(mapa_herramientas.keys())}"
        except Exception as e:
            resultado = f"Error al ejecutar la herramienta: {e}"
        mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))

    respuesta_final = llamar_con_reintentos(llm_con_tools.invoke, mensajes)

    datos_obtenidos = "\n".join(m.content for m in mensajes if isinstance(m, ToolMessage))

    return {
        **estado,
        "respuesta_especialista": extraer_texto(respuesta_final),
        "datos_obtenidos": datos_obtenidos,
    }