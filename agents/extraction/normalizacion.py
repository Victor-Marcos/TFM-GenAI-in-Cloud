from .reintentos import llamar_con_reintentos

def get_embedding(client, texto, task_type="CLUSTERING"):
    from google.genai import types
    result = llamar_con_reintentos(
        client.models.embed_content,
        model="gemini-embedding-001",
        contents=texto,
        config=types.EmbedContentConfig(
            output_dimensionality=1536,
            task_type=task_type
        )
    )
    return result.embeddings[0].values


def buscar_o_crear_comercio(cur, comercio_datos, tipo_ticket_nombre):
    cur.execute("SELECT id FROM tipos_ticket WHERE nombre = %s", (tipo_ticket_nombre,))
    tipo_ticket_id = cur.fetchone()[0]

    nif = comercio_datos.get("nif")
    if nif:
        cur.execute("SELECT id FROM comercios WHERE nif = %s", (nif,))
        row = cur.fetchone()
        if row:
            return row[0]

    cur.execute(
        "SELECT id FROM comercios WHERE nombre = %s AND direccion = %s",
        (comercio_datos["nombre"], comercio_datos.get("direccion"))
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """INSERT INTO comercios (nombre, direccion, nif, tipo_ticket_id)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (comercio_datos["nombre"], comercio_datos.get("direccion"), nif, tipo_ticket_id)
    )
    return cur.fetchone()[0]


def crear_producto_nuevo(cur, client, descripcion, categoria_id, embedding):
    try:
        cur.execute(
            """INSERT INTO productos (nombre_normalizado, categoria_id, embedding)
               VALUES (%s, %s, %s) RETURNING id""",
            (descripcion, categoria_id, embedding)
        )
        return cur.fetchone()[0]
    except Exception as e:
        if "productos_nombre_normalizado_key" in str(e):
            cur.execute("SELECT id FROM productos WHERE nombre_normalizado = %s", (descripcion,))
            fila = cur.fetchone()
            if fila:
                return fila[0]
        raise


def buscar_o_crear_producto(cur, client, descripcion, categoria_nombre, top_k=5):
    cur.execute("SELECT id FROM categorias_producto WHERE nombre = %s", (categoria_nombre,))
    categoria_id = cur.fetchone()[0]

    embedding = get_embedding(client, descripcion)

    cur.execute(
        """SELECT id, nombre_normalizado
           FROM productos
           WHERE categoria_id = %s
           ORDER BY embedding <=> %s::vector ASC
           LIMIT %s""",
        (categoria_id, embedding, top_k)
    )
    candidatos = cur.fetchall()

    if not candidatos:
        return crear_producto_nuevo(cur, client, descripcion, categoria_id, embedding)

    from google.genai import types
    lista_candidatos = "\n".join([f"{c[0]}: {c[1]}" for c in candidatos])
    prompt_verificacion = f"""
Un ticket menciona el producto: "{descripcion}"

Estos son productos ya existentes en el catálogo, de la misma categoría:
{lista_candidatos}

¿Alguno de ellos es EXACTAMENTE el mismo producto (aunque esté escrito de forma distinta)?
Responde ÚNICAMENTE con el id numérico si hay coincidencia, o con "NINGUNO" si son productos distintos.
"""
    response = llamar_con_reintentos(
            client.models.generate_content,
            model="gemini-3.1-flash-lite-preview",
            contents=[prompt_verificacion],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="minimal")
            )
    )
    resultado = response.text.strip()

    if resultado.isdigit():
        return int(resultado)

    return crear_producto_nuevo(cur, client, descripcion, categoria_id, embedding)