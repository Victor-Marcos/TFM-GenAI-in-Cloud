import json
from google.genai import types
from .imagen import preparar_imagen


def parsear_json_robusto(texto):
    decoder = json.JSONDecoder()
    texto = texto.strip()

    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
        texto = texto.strip()

    obj, _ = decoder.raw_decode(texto)
    return obj


def extraer_ticket_bytes(client, imagen_bytes, prompt):
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            {"inline_data": {"mime_type": "image/jpeg", "data": imagen_bytes}},
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level="low")
        )
    )
    return parsear_json_robusto(response.text)


def extraer_ticket(client, ruta_imagen, prompt):
    imagen_bytes = preparar_imagen(ruta_imagen)
    return extraer_ticket_bytes(client, imagen_bytes, prompt)