import os
import json
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

DESCRIPCIONES_ESPECIALISTAS = {
    "financiero": "Cuanto/donde/cuando se ha gastado: totales, gasto por categoria, por comercio, evolucion en el tiempo, comparativas de meses.",
    "patrones": "Que productos se compran, con que frecuencia, que productos se compran juntos, ranking de productos por gasto o por veces comprados.",
    "calidad": "Preguntas sobre el propio sistema: cuantos tickets pendientes de revision manual, porcentaje de auto-validacion, fiabilidad del pipeline de extraccion.",
    "sql_libre": "Cualquier pregunta sobre los datos que no encaje claramente en las anteriores; permite escribir una consulta SQL a medida.",
}


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

    prompt = f"""
Clasifica esta pregunta de un usuario sobre sus gastos personales, eligiendo
EXACTAMENTE uno de estos especialistas:

{lista_especialistas}

Pregunta: "{estado['pregunta']}"
{contexto_reintento}

Responde ÚNICAMENTE con un JSON: {{"especialista": "uno_de_los_anteriores"}}
"""

    response = client.models.generate_content(
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