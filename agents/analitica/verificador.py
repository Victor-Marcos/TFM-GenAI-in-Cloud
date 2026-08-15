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
    prompt = f"""
Pregunta original del usuario: "{estado['pregunta']}"

Respuesta que ha dado el especialista "{estado['especialista_elegido']}":
"{estado['respuesta_especialista']}"

¿Esta respuesta responde de verdad la pregunta, con datos concretos (no
vagos ni genéricos)? Considera que falla si: falta un dato pedido
explícitamente, la respuesta dice que no tiene información pudiendo
tenerla, o el especialista no era el adecuado para esta pregunta.

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