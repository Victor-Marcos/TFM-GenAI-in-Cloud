def listar_tickets(cur, perfil_id, limite=50):
    cur.execute(
        """SELECT t.id, t.fecha, t.total, t.estado, c.nombre AS comercio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.perfil_id = %s
           ORDER BY t.id DESC
           LIMIT %s""",
        (perfil_id, limite)
    )
    columnas = ["id", "fecha", "total", "estado", "comercio"]
    return [dict(zip(columnas, fila)) for fila in cur.fetchall()]


def obtener_ticket(cur, ticket_id, perfil_id):
    cur.execute(
        """SELECT t.id, t.fecha, t.total, t.estado, t.motivo_revision, t.atributos, c.nombre AS comercio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.id = %s AND t.perfil_id = %s""",
        (ticket_id, perfil_id)
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


def listar_pendientes(cur, perfil_id):
    cur.execute(
        """SELECT t.id, t.fecha, t.total, t.motivo_revision, c.nombre AS comercio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.perfil_id = %s AND t.estado = 'pendiente_revision'
           ORDER BY t.id DESC""",
        (perfil_id,)
    )
    columnas = ["id", "fecha", "total", "motivo_revision", "comercio"]
    return [dict(zip(columnas, fila)) for fila in cur.fetchall()]


def marcar_como_validado(cur, ticket_id, perfil_id, total_corregido=None):
    if total_corregido is not None:
        cur.execute(
            "UPDATE tickets SET estado = 'validado', motivo_revision = NULL, total = %s WHERE id = %s AND perfil_id = %s",
            (total_corregido, ticket_id, perfil_id)
        )
    else:
        cur.execute(
            "UPDATE tickets SET estado = 'validado', motivo_revision = NULL WHERE id = %s AND perfil_id = %s",
            (ticket_id, perfil_id)
        )
    return cur.rowcount > 0


def listar_perfiles(cur):
    cur.execute("SELECT id, nombre, descripcion, avatar_color FROM perfiles ORDER BY id")
    columnas = ["id", "nombre", "descripcion", "avatar_color"]
    return [dict(zip(columnas, fila)) for fila in cur.fetchall()]


def crear_perfil(cur, nombre, descripcion=None, avatar_color="#4A90D9"):
    cur.execute(
        """INSERT INTO perfiles (nombre, descripcion, avatar_color)
           VALUES (%s, %s, %s) RETURNING id, nombre, descripcion, avatar_color""",
        (nombre, descripcion, avatar_color)
    )
    fila = cur.fetchone()
    return dict(zip(["id", "nombre", "descripcion", "avatar_color"], fila))



PALABRAS_PROHIBIDAS = ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "create"]

def ejecutar_sql_seguro(cur, consulta_sql, limite_filas=500):
    consulta_limpia = consulta_sql.strip().lower()

    if not consulta_limpia.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT")

    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in consulta_limpia:
            raise ValueError(f"Consulta no permitida: contiene '{palabra}'")

    if "limit" not in consulta_limpia:
        consulta_sql = f"{consulta_sql.rstrip(';')} LIMIT {limite_filas}"

    cur.execute(consulta_sql)
    columnas = [desc[0] for desc in cur.description]
    filas = cur.fetchall()
    return {
        "columnas": columnas,
        "filas": [list(fila) for fila in filas]
    }

def eliminar_perfil(cur, perfil_id):
    cur.execute("DELETE FROM tickets WHERE perfil_id = %s", (perfil_id,))
    cur.execute("DELETE FROM perfiles WHERE id = %s", (perfil_id,))
    return cur.rowcount > 0


def obtener_esquema_bbdd(cur):
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    tablas = {}
    for tabla, columna, tipo in cur.fetchall():
        tablas.setdefault(tabla, []).append({"columna": columna, "tipo": tipo})

    cur.execute("""
        SELECT
            tc.table_name AS tabla_origen,
            kcu.column_name AS columna_origen,
            ccu.table_name AS tabla_destino,
            ccu.column_name AS columna_destino
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
    """)
    relaciones = [
        {"tabla_origen": fila[0], "columna_origen": fila[1], "tabla_destino": fila[2], "columna_destino": fila[3]}
        for fila in cur.fetchall()
    ]

    return {"tablas": tablas, "relaciones": relaciones}