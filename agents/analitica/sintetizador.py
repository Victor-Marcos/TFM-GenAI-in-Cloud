import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def nodo_sintetizador(estado):
    """
    Redacta la respuesta final para el usuario, a partir de la respuesta
    ya verificada del especialista. Si se agotaron los reintentos sin
    una respuesta plenamente satisfactoria, lo indica con honestidad.
    """
    intentos = estado.get("intentos", 0)
    hubo_problema = estado.get("motivo_fallo") is None and intentos >= 2

    aviso = ""
    if hubo_problema:
        aviso = (
            "\nNota: no se ha podido verificar completamente esta respuesta tras "
            "varios intentos; indícalo brevemente al usuario con honestidad, sin "
            "sonar alarmante."
        )

    prompt = f"""
Pregunta original del usuario: "{estado['pregunta']}"

Datos obtenidos: "{estado['respuesta_especialista']}"

Redacta una respuesta final clara, breve y en tono cercano, como si fueras
un asistente personal de finanzas. Usa los datos tal cual, sin inventar
nada adicional. No menciones que eres un "especialista" ni el proceso interno.
{aviso}
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[prompt],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low")
        )
    )

    return {**estado, "respuesta_final": response.text}