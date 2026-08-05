import json
from .validacion import validar_ticket
from .normalizacion import buscar_o_crear_comercio, buscar_o_crear_producto, get_embedding
from .extraccion import extraer_ticket_bytes
from .prompt import cargar_valores_permitidos, construir_prompt
from .imagen import preparar_imagen, guardar_imagen_permanente


def guardar_ticket(cur, client, datos, ruta_imagen, tipos_permitidos, categorias_permitidas, perfil_id):
    errores = validar_ticket(datos, tipos_permitidos, categorias_permitidas)
    estado = "validado" if not errores else "pendiente_revision"
    motivo_revision = "; ".join(errores) if errores else None

    cur.execute("SELECT id FROM tipos_ticket WHERE nombre = %s", (datos["tipo_ticket"],))
    tipo_ticket_id = cur.fetchone()[0]

    comercio_id = buscar_o_crear_comercio(cur, datos["comercio"], datos["tipo_ticket"])

    texto_resumen = f"{datos['comercio']['nombre']} - " + ", ".join(p["descripcion"] for p in datos["productos"])
    embedding_ticket = get_embedding(client, texto_resumen)

    atributos = json.dumps({"desglose_iva": datos.get("desglose_iva", [])})

    cur.execute(
        """INSERT INTO tickets (comercio_id, tipo_ticket_id, fecha, total, imagen_path, estado, motivo_revision, atributos, embedding, perfil_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (comercio_id, tipo_ticket_id, datos["fecha"], datos["total"], ruta_imagen, estado, motivo_revision, atributos, embedding_ticket, perfil_id)
    )
    ticket_id = cur.fetchone()[0]

    for p in datos.get("productos", []):
        producto_id = buscar_o_crear_producto(cur, client, p["descripcion"], p["categoria"])
        cur.execute(
            """INSERT INTO lineas_ticket (ticket_id, producto_id, descripcion_original, cantidad, precio_unitario, subtotal)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (ticket_id, producto_id, p["descripcion"], p["cantidad"], p["precio_unitario"], p["subtotal"])
        )

    return ticket_id, estado, motivo_revision


def procesar_ticket(cur, client, fuente_imagen, perfil_id):
    tipos_permitidos, categorias_permitidas = cargar_valores_permitidos(cur)
    prompt = construir_prompt(tipos_permitidos, categorias_permitidas)

    imagen_bytes = preparar_imagen(fuente_imagen)
    ruta_guardada = guardar_imagen_permanente(imagen_bytes)

    try:
        datos = extraer_ticket_bytes(client, imagen_bytes, prompt)
    except Exception as e:
        return {
            "ticket_id": None,
            "estado": "error_extraccion",
            "motivo_revision": str(e),
            "datos_extraidos": None
        }

    ticket_id, estado, motivo_revision = guardar_ticket(
        cur, client, datos, ruta_guardada, tipos_permitidos, categorias_permitidas, perfil_id
    )

    return {
        "ticket_id": ticket_id,
        "estado": estado,
        "motivo_revision": motivo_revision,
        "datos_extraidos": datos
    }