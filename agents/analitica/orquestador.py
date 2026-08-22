import os
import json
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from agents.extraction.reintentos import llamar_con_reintentos

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

DESCRIPCIONES_ESPECIALISTAS = {
    "financiero": (
        "Cuanto/donde/cuando se ha gastado: totales, gasto por categoria, por comercio, "
        "evolucion en el tiempo, comparativas de meses, informacion sobre el ultimo ticket "
        "o la ultima compra o el ultimo ticket cargado/registrado/subido/procesado. "
        "Tambien preguntas de opinion o valoracion sobre el gasto: '¿gasto demasiado en X?', "
        "'¿en que deberia ahorrar?', '¿es razonable lo que gasto en Y?'"
    ),
    "patrones": (
        "Que productos se compran, con que frecuencia, que productos se compran juntos, "
        "ranking de productos por gasto o por veces comprados. Tambien preguntas sobre "
        "alimentacion, dietas, nutricion o habitos saludables -incluso genericas como "
        "'hazme un plan de comidas' o 'dieta para el gimnasio' o 'como puedo comer mas "
        "sano'- ya que deben responderse combinando conocimiento general de nutricion "
        "con los productos reales que la persona ya compra."
    ),
    "calidad": (
        "Preguntas sobre el propio sistema informatico: cuantos tickets pendientes de "
        "revision manual, porcentaje de auto-validacion, fiabilidad del PROCESO de "
        "extraccion (no de los datos del usuario en si). NO usar para preguntas sobre "
        "cuando se compro o cargo un ticket concreto, eso es 'financiero'."
    ),
    "sql_libre": (
        "Cualquier pregunta sobre LOS DATOS DEL USUARIO (tickets, productos, comercios, "
        "gastos) que no encaje claramente en las anteriores; permite escribir una consulta "
        "SQL a medida. Usar como opcion por defecto ante duda, ANTES que fuera_de_alcance, "
        "si la pregunta menciona compras, gastos, tickets o productos de cualquier forma."
    ),
    "fuera_de_alcance": (
        "USAR SOLO si la pregunta NO tiene absolutamente ninguna relacion con compras, "
        "gastos, tickets, productos, alimentacion o dietas del usuario: charla general, "
        "el tiempo, saludos, preguntas sobre temas completamente ajenos. Si la pregunta "
        "menciona compras, alimentacion, gasto, dietas, productos o tickets de cualquier "
        "forma -incluso pidiendo una opinion o consejo- NUNCA es fuera_de_alcance."
    ),
}


def formatear_historial(historial, max_turnos=4):
    if not historial:
        return ""
    ultimos = historial[-(max_turnos * 2):]
    lineas = [f"{'Usuario' if m['autor'] == 'usuario' else 'Asistente'}: {m['texto']}" for m in ultimos]
    return "\nConversación previa:\n" + "\n".join(lineas) + "\n"


def nodo_orquestador(estado):
    especialista_anterior = estado.get("especialista_elegido")
    motivo_fallo = estado.get("motivo_fallo")

    contexto_reintento = ""
    if especialista_anterior and motivo_fallo:
        contexto_reintento = f"""
IMPORTANTE: ya se intentó responder con el especialista '{especialista_anterior}',
pero no fue suficiente por este motivo: "{motivo_fallo}"
Elige el especialista que mejor resuelva ese motivo concreto, que puede ser
el mismo (si el problema fue de ejecución, no de elección) u otro distinto
(si el motivo indica que la pregunta necesitaba otro tipo de datos).
"""

    lista_especialistas = "\n".join(
        f"- {nombre}: {descripcion}" for nombre, descripcion in DESCRIPCIONES_ESPECIALISTAS.items()
    )

    contexto_historial = formatear_historial(estado.get("historial", []))

    prompt = f"""
Clasifica esta pregunta de un usuario sobre sus gastos personales, eligiendo
EXACTAMENTE uno de estos especialistas:

{lista_especialistas}
{contexto_historial}
Pregunta: "{estado['pregunta']}"
{contexto_reintento}

Responde ÚNICAMENTE con un JSON: {{"especialista": "uno_de_los_anteriores"}}
"""

    response = llamar_con_reintentos(
        client.models.generate_content,
        model="gemini-3.1-flash-lite-preview",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level="minimal")
        )
    )

    resultado = json.loads(response.text)
    especialista = resultado.get("especialista", "sql_libre")

    if especialista not in DESCRIPCIONES_ESPECIALISTAS:
        especialista = "sql_libre"

    return {
        **estado,
        "especialista_elegido": especialista,
        "intentos": estado.get("intentos", 0) + 1,
    }