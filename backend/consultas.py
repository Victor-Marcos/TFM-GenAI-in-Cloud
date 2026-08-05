def listar_tickets(cur, limite=50):
    """Devuelve los tickets más recientes, con datos del comercio."""
    cur.execute(
        """SELECT t.id, t.fecha, t.total, t.estado, c.nombre AS comercio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           ORDER BY t.id DESC
           LIMIT %s""",
        (limite,)
    )
    columnas = ["id", "fecha", "total", "estado", "comercio"]
    return [dict(zip(columnas, fila)) for fila in cur.fetchall()]


def obtener_ticket(cur, ticket_id):
    """Devuelve el detalle completo de un ticket, con sus líneas de producto."""
    cur.execute(
        """SELECT t.id, t.fecha, t.total, t.estado, t.motivo_revision, t.atributos, c.nombre AS comercio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.id = %s""",
        (ticket_id,)
    )
    fila = cur.fetchone()
    if not fila:
        return None

    ticket = dict(zip(["id", "fecha", "total", "estado", "motivo_revision", "atributos", "comercio"], fila))

    cur.execute(
        """SELECT lt.descripcion_original, lt.cantidad, lt.precio_unitario, lt.subtotal, p.nombre_normalizado
           FROM lineas_ticket lt
           LEFT JOIN productos p ON lt.producto_id = p.id
           WHERE lt.ticket_id = %s""",
        (ticket_id,)
    )
    columnas_lineas = ["descripcion_original", "cantidad", "precio_unitario", "subtotal", "producto_normalizado"]
    ticket["productos"] = [dict(zip(columnas_lineas, fila)) for fila in cur.fetchall()]

    return ticket