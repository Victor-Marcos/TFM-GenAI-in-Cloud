import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.dashboard import productos_completo, productos_comprados_juntos
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
            func=lambda: productos_completo(cur, perfil_id),
            name="productos_mas_comprados",
            description="Ranking de productos por frecuencia de compra y por gasto total. Usar para '¿que compro mas?' o '¿en que producto gasto mas?'",
        ),
        StructuredTool.from_function(
            func=lambda: {"productos_juntos": productos_comprados_juntos(cur, perfil_id)},
            name="productos_comprados_juntos",
            description="Pares de productos que se compran frecuentemente en el mismo ticket. Usar para '¿que suelo comprar junto con X?' o '¿que productos compro a la vez?'",
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


def nodo_patrones(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    contexto = formatear_historial(estado.get("historial", []))

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente especializado en habitos de compra. Usa SIEMPRE "
            "las herramientas disponibles para responder con datos reales; nunca "
            "inventes cifras ni nombres de productos. Si ninguna herramienta "
            "especifica encaja, usa consulta_sql_respaldo antes de responder sin "
            "datos. "
            "Si la pregunta pide una opinión, valoración o recomendación, ofrécela "
            "basándote en los datos reales obtenidos, con un tono cercano y natural. "
            "Para preguntas sobre dietas o alimentación saludable, combina tu conocimiento "
            "general de nutrición con los productos reales que la persona compra (obtenidos "
            "mediante tus herramientas), sugiriendo comidas o cambios que aprovechen lo que "
            "ya tiene en su cesta habitual. "
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

    print(f"[PATRONES] pregunta: {estado['pregunta']}")
    print(f"[PATRONES] datos_obtenidos: {datos_obtenidos[:800]}")

    return {
        **estado,
        "respuesta_especialista": extraer_texto(respuesta_final),
        "datos_obtenidos": datos_obtenidos,
    }