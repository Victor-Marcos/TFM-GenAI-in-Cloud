import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.dashboard import (
    resumen_general, gasto_por_categoria, comercios_completo,
    evolucion_completa, gasto_por_tipo_ticket, ticket_medio_por_categoria,
    ultimo_ticket,
)
from backend.consultas import ejecutar_sql_seguro
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
            func=lambda: resumen_general(cur, perfil_id),
            name="resumen_general",
            description="Gasto total, numero de tickets, ticket medio, comercios y productos distintos.",
        ),
        StructuredTool.from_function(
            func=lambda: gasto_por_categoria(cur, perfil_id),
            name="gasto_por_categoria",
            description="Gasto agrupado por categoria de producto.",
        ),
        StructuredTool.from_function(
            func=lambda: comercios_completo(cur, perfil_id),
            name="gasto_por_comercio",
            description="Gasto, visitas y ticket medio por cada comercio.",
        ),
        StructuredTool.from_function(
            func=lambda: evolucion_completa(cur, perfil_id),
            name="evolucion_temporal",
            description="Evolucion del gasto mes a mes, por dia de la semana, y comparativa.",
        ),
        StructuredTool.from_function(
            func=lambda: {"por_tipo": gasto_por_tipo_ticket(cur, perfil_id)},
            name="gasto_por_tipo_ticket",
            description="Gasto agrupado por tipo de ticket.",
        ),
        StructuredTool.from_function(
            func=lambda: ticket_medio_por_categoria(cur, perfil_id),
            name="ticket_medio_por_categoria",
            description="Importe medio gastado por compra en cada categoria.",
        ),
        StructuredTool.from_function(
            func=lambda: ultimo_ticket(cur, perfil_id),
            name="ultimo_ticket",
            description="El ticket mas reciente: fecha, comercio y total.",
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


def nodo_financiero(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    contexto = formatear_historial(estado.get("historial", []))

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente financiero personal. Usa SIEMPRE las herramientas "
            "disponibles para responder con datos reales; nunca inventes cifras. "
            "IMPORTANTE: tus herramientas fijas dan totales generales, pero NO permiten "
            "combinar dos filtros a la vez (por ejemplo, una categoria en un mes concreto, "
            "o un comercio en un periodo concreto). Si la pregunta pide un filtro combinado "
            "o algo muy especifico que ninguna herramienta cubre exactamente, usa SIEMPRE "
            "consulta_sql_respaldo en vez de responder que no tienes datos. "
            "Si una pregunta necesita varias herramientas, llama a todas las que hagan falta. "
            "Si la pregunta pide una opinión, valoración o recomendación, ofrécela "
            "basándote en los datos reales obtenidos, con un tono cercano y natural (está "
            "bien decir 'normalmente' o 'podrías considerar' si te apoyas en datos reales); "
            "deja claro que es una interpretación, no un hecho. "
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