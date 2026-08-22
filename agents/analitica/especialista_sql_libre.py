import os
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.consultas import ejecutar_sql_seguro
from agents.extraction.reintentos import llamar_con_reintentos

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

ESQUEMA_BBDD = """
Tablas disponibles (todas filtradas ya por el perfil correcto, no incluyas
condiciones de perfil_id en tu SQL, se añaden automaticamente):

- tickets(id, comercio_id, tipo_ticket_id, fecha, total, estado, atributos, perfil_id)
- lineas_ticket(id, ticket_id, producto_id, descripcion_original, cantidad, precio_unitario, subtotal)
- productos(id, nombre_normalizado, categoria_id)
- categorias_producto(id, nombre)
- comercios(id, nombre, cadena, direccion, nif)
- tipos_ticket(id, nombre)
"""


def construir_herramientas(cur, perfil_id):
    def ejecutar_consulta(sql: str):
        sql_con_filtro = sql
        if "tickets" in sql.lower() and f"perfil_id = {perfil_id}" not in sql:
            raise ValueError("La consulta debe filtrar explicitamente por perfil_id, usando el valor proporcionado")
        return ejecutar_sql_seguro(cur, sql_con_filtro)

    return [
        StructuredTool.from_function(
            func=ejecutar_consulta,
            name="ejecutar_sql",
            description=f"Ejecuta una consulta SELECT sobre la base de datos para responder preguntas que no cubren otras herramientas. {ESQUEMA_BBDD} IMPORTANTE: cualquier consulta que toque la tabla tickets debe incluir 'WHERE ... perfil_id = {perfil_id}' explicitamente.",
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


def nodo_sql_libre(estado, cur):
    herramientas = construir_herramientas(cur, estado["perfil_id"])
    llm_con_tools = llm.bind_tools(herramientas)

    contexto = formatear_historial(estado.get("historial", []))

    mensajes = [
        SystemMessage(content=(
            "Eres un asistente que responde preguntas sobre los datos del usuario "
            "escribiendo consultas SQL de solo lectura (SELECT). Usa SIEMPRE la "
            "herramienta ejecutar_sql; nunca inventes datos. Si tu primera consulta "
            "falla, intenta corregirla basandote en el mensaje de error. "
            "Si la pregunta pide una opinión o recomendación, ofrécela basándote en "
            "los datos reales que obtengas, dejando claro que es tu interpretación, "
            "no un hecho objetivo. "
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
            resultado = f"Error: la herramienta '{llamada['name']}' no existe. Las herramientas disponibles son: {list(mapa_herramientas.keys())}"
        except Exception as e:
            resultado = f"Error al ejecutar la consulta: {e}"
        mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))

    respuesta_final = llamar_con_reintentos(llm_con_tools.invoke, mensajes)

    datos_obtenidos = "\n".join(m.content for m in mensajes if isinstance(m, ToolMessage))

    return {
        **estado,
        "respuesta_especialista": extraer_texto(respuesta_final),
        "datos_obtenidos": datos_obtenidos,
    }