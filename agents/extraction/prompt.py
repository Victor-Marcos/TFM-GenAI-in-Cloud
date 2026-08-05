def cargar_valores_permitidos(cur):
    cur.execute("SELECT nombre FROM tipos_ticket ORDER BY nombre")
    tipos_permitidos = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT nombre FROM categorias_producto ORDER BY nombre")
    categorias_permitidas = [r[0] for r in cur.fetchall()]

    return tipos_permitidos, categorias_permitidas


def construir_prompt(tipos_permitidos, categorias_permitidas):
    return f"""
Analiza esta imagen de un ticket/factura y extrae la información en formato JSON con esta estructura exacta:

{{
  "tipo_ticket": "uno de estos valores: {tipos_permitidos}",
  "comercio": {{
    "nombre": "nombre del establecimiento",
    "direccion": "dirección si aparece, o null",
    "nif": "NIF/CIF si aparece, o null"
  }},
  "fecha": "YYYY-MM-DD",
  "total": 0.00,
  "desglose_iva": [
    {{
      "porcentaje": 0.0,
      "base_imponible": 0.00,
      "cuota": 0.00
    }}
  ],
  "productos": [
    {{
      "descripcion": "texto tal cual aparece en el ticket",
      "categoria": "una de estas: {categorias_permitidas}",
      "cantidad": 0,
      "precio_unitario": 0.00,
      "subtotal": 0.00
    }}
  ]
}}

Reglas:
- "tipo_ticket" y "categoria" deben ser EXACTAMENTE uno de los valores permitidos indicados arriba, sin inventar otros.
- "desglose_iva" debe reflejar la tabla de IVA que aparece en el ticket (normalmente al pie, con columnas de base imponible, porcentaje y cuota). Si el ticket no trae esta tabla, devuelve una lista vacía [].
- Si un producto no encaja claramente en ninguna categoría, usa "alimentacion_general" (para comida) u "otros" (para el resto).
- Si no puedes leer un dato con certeza, pon null en ese campo, no inventes valores.
- Devuelve ÚNICAMENTE el JSON, sin texto adicional ni backticks.
"""