import os
import json
from dotenv import load_dotenv
load_dotenv()

from agents.extraction.reintentos import llamar_con_reintentos
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MAX_INTENTOS = 2


def nodo_verificador(estado):
    """
    Comprueba si la respuesta del especialista responde de verdad la
    pregunta original. Si no, escribe motivo_fallo para que el
    Orquestador pueda reintentar con mejor informacion.
    """
    datos = estado.get("datos_obtenidos")
    resumen_datos = datos if datos else "NINGUNO — no se llamó a ninguna herramienta"

    prompt = f"""
Pregunta original del usuario: "{estado['pregunta']}"

Datos reales obtenidos de la base de datos por el especialista:
{resumen_datos}

Respuesta que ha dado el especialista "{estado['especialista_elegido']}":
"{estado['respuesta_especialista']}"

¿Esta respuesta responde de verdad la pregunta? Ten en cuenta:
- Si "Datos reales obtenidos" es NINGUNO, la respuesta casi seguro es
  insuficiente: significa que no se consultó ninguna fuente de datos real,
  sea cual sea el tono de la respuesta.
- Si la pregunta pide una opinión o recomendación, un tono cercano o
  frases como "normalmente" o "podrías considerar" son perfectamente
  válidas, SIEMPRE que la respuesta se apoye en los datos reales
  mostrados arriba, no en conocimiento general sin ninguna cifra del
  usuario detrás.
- Para preguntas de opinión, dieta o recomendación, es SUFICIENTE si la
  respuesta menciona productos o categorías reales obtenidos de las
  herramientas (visibles en "Datos reales obtenidos"), aunque no incluya
  cifras numéricas — no exijas números para este tipo de preguntas.
- Falla también si falta un dato pedido explícitamente, o si el
  especialista elegido no era el adecuado para esta pregunta.
- IMPORTANTE: si la respuesta menciona una cifra numérica concreta (un
  importe en euros, un conteo), verifica que ese número, o los números de
  los que se deriva (por ejemplo, un porcentaje calculado a partir de dos
  cifras presentes en los datos), aparezcan de forma reconocible en "Datos
  reales obtenidos". Cálculos simples derivados de esos datos (porcentajes,
  posiciones en un ranking, comparaciones) SON válidos y no cuentan como
  cifra inventada. Solo marca como INSUFICIENTE si el número no tiene
  ninguna relación calculable con los datos mostrados.

Responde ÚNICAMENTE con un JSON:
{{"suficiente": true/false, "motivo": "explicacion breve solo si suficiente es false, si no cadena vacia"}}
"""

    response = llamar_con_reintentos(
        client.models.generate_content,
        model="gemini-3.1-flash-lite-preview",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level="low")
        )
    )

    resultado = json.loads(response.text)
    suficiente = resultado.get("suficiente", True)
    motivo = resultado.get("motivo", "")

    intentos_agotados = estado.get("intentos", 0) >= MAX_INTENTOS

    if suficiente or intentos_agotados:
        return {**estado, "motivo_fallo": None}

    return {**estado, "motivo_fallo": motivo}