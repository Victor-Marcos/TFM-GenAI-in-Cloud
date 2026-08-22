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
Tablas disponibles:
- tickets(id, comercio_id, tipo_ticket_id, fecha, total, estado, atributos, perfil_id)
- lineas_ticket(id, ticket_id, producto_id, descripcion_original, cantidad, precio_unitario, subtotal)
- productos(id, nombre_normalizado, categoria_id)
- categorias_producto(id, nombre)
- comercios(id, nombre, cadena, direccion, nif)
- tipos_ticket(id, nombre)

IMPORTANTE: cualquier consulta que toque la tabla 'tickets' DEBE incluir
explicitamente 'WHERE ... perfil_id = {perfil_id}' (sustituyendo {perfil_id}
por el valor real indicado abajo). Esto NO se añade automaticamente, tienes
que escribirlo tu mismo en cada consulta.

IMPORTANTE sobre fechas: la columna 'fecha' es de tipo DATE, no texto.
Para filtrar por mes usa EXTRACT(MONTH FROM fecha) = N, nunca LIKE.
Si el usuario no especifica un año concreto, NO asumas un año: incluye
TODOS los años disponibles para ese mes, usando solo EXTRACT(MONTH FROM
fecha) = N sin restringir el año.
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
    mapa_herramientas = {h.name: h for h in herramientas}

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
            "Si tu consulta solo obtiene un identificador o nombre de categoria/producto "
            "(por ejemplo, el id de una categoria), eso NO es la respuesta final: debes "
            "ejecutar OTRA consulta (con JOIN a lineas_ticket y tickets) que calcule "
            "el dato numerico real que se pregunta, ANTES de dar tu respuesta final. "
            "Nunca respondas con una cifra que no provenga literalmente del resultado "
            "de una consulta SQL ya ejecutada. "
            "IMPORTANTE: la base de datos es PostgreSQL, no SQLite ni MySQL. Usa "
            "EXTRACT(MONTH FROM fecha) o EXTRACT(YEAR FROM fecha) para fechas, NUNCA "
            "funciones como STRFTIME() o DATE_FORMAT() que no existen en PostgreSQL. "
            "Prefiere SIEMPRE una única consulta que responda directamente a la "
            "pregunta, en vez de varias consultas exploratorias. Por ejemplo, para "
            "preguntas sobre en qué categoría recortar gasto, una única consulta que "
            "agrupe el gasto por categoria y lo ordene de mayor a menor ya es "
            "suficiente para responder. "
            "No uses formato Markdown (nada de **negrita**, guiones de lista ni numeración); "
            "escribe en texto plano, con saltos de línea simples si necesitas separar ideas."
            f"{contexto}"
        )),
        HumanMessage(content=estado["pregunta"]),
    ]

    max_rondas = 6
    for ronda in range(max_rondas):
        respuesta = llamar_con_reintentos(llm_con_tools.invoke, mensajes)

        if not respuesta.tool_calls:
            datos_obtenidos = "\n".join(m.content for m in mensajes if isinstance(m, ToolMessage))
            print(f"[SQL_LIBRE] pregunta: {estado['pregunta']}")
            print(f"[SQL_LIBRE] rondas usadas: {ronda + 1}")
            print(f"[SQL_LIBRE] datos_obtenidos: {datos_obtenidos[:800]}")
            return {
                **estado,
                "respuesta_especialista": extraer_texto(respuesta),
                "datos_obtenidos": datos_obtenidos if datos_obtenidos else None,
            }

        mensajes.append(respuesta)

        for llamada in respuesta.tool_calls:
            try:
                herramienta = mapa_herramientas[llamada["name"]]
                resultado = herramienta.invoke(llamada["args"])
            except KeyError:
                resultado = f"Error: la herramienta '{llamada['name']}' no existe. Disponibles: {list(mapa_herramientas.keys())}"
            except Exception as e:
                resultado = f"Error al ejecutar la consulta: {e}"
            mensajes.append(ToolMessage(content=str(resultado), tool_call_id=llamada["id"]))

    respuesta_final = llamar_con_reintentos(llm_con_tools.invoke, mensajes)
    datos_obtenidos = "\n".join(m.content for m in mensajes if isinstance(m, ToolMessage))

    print(f"[SQL_LIBRE] pregunta: {estado['pregunta']}")
    print(f"[SQL_LIBRE] limite de rondas alcanzado")
    print(f"[SQL_LIBRE] datos_obtenidos: {datos_obtenidos[:800]}")

    return {
        **estado,
        "respuesta_especialista": extraer_texto(respuesta_final),
        "datos_obtenidos": datos_obtenidos,
    }