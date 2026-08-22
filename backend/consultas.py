from pgvector import Vector
import os

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
        """SELECT t.id, t.fecha, t.total, t.estado, t.motivo_revision, t.atributos, c.nombre AS comercio, t.imagen_path
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.id = %s AND t.perfil_id = %s""",
        (ticket_id, perfil_id)
    )
    fila = cur.fetchone()
    if not fila:
        return None

    ticket = dict(zip(["id", "fecha", "total", "estado", "motivo_revision", "atributos", "comercio", "imagen_path"], fila))

    cur.execute(
        """SELECT lt.id, lt.descripcion_original, lt.cantidad, lt.precio_unitario, lt.subtotal, p.nombre_normalizado
           FROM lineas_ticket lt
           LEFT JOIN productos p ON lt.producto_id = p.id
           WHERE lt.ticket_id = %s
           ORDER BY lt.id""",
        (ticket_id,)
    )
    columnas_lineas = ["id", "descripcion_original", "cantidad", "precio_unitario", "subtotal", "producto_normalizado"]
    ticket["productos"] = [dict(zip(columnas_lineas, fila)) for fila in cur.fetchall()]

    return ticket


def listar_pendientes(cur, perfil_id):
    cur.execute(
        """SELECT t.id, t.fecha, t.total, t.motivo_revision, c.nombre AS comercio, t.imagen_path
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.perfil_id = %s AND t.estado = 'pendiente_revision'
           ORDER BY t.id DESC""",
        (perfil_id,)
    )
    columnas = ["id", "fecha", "total", "motivo_revision", "comercio", "imagen_path"]
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

    print(f"[SQL EJECUTADO] {consulta_sql}")

    cur.execute(consulta_sql)
    columnas = [desc[0] for desc in cur.description]

    filas = []
    for fila in cur.fetchall():
        fila_procesada = []
        for valor in fila:
            if isinstance(valor, Vector):
                fila_procesada.append(f"[vector de {valor.dimensions} dimensiones]")
            else:
                fila_procesada.append(valor)
        filas.append(fila_procesada)

    return {"columnas": columnas, "filas": filas}

def eliminar_perfil(cur, perfil_id):
    cur.execute("SELECT imagen_path FROM tickets WHERE perfil_id = %s", (perfil_id,))
    rutas_imagenes = [fila[0] for fila in cur.fetchall() if fila[0]]

    cur.execute("DELETE FROM tickets WHERE perfil_id = %s", (perfil_id,))
    cur.execute("DELETE FROM perfiles WHERE id = %s", (perfil_id,))

    for ruta in rutas_imagenes:
        if os.path.exists(ruta):
            os.remove(ruta)

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


def actualizar_ticket_completo(cur, ticket_id, perfil_id, fecha, total, comercio_nombre, lineas):
    """
    Actualiza un ticket completo (cabecera + líneas) tras revisión manual,
    y lo marca como validado. Verifica que el ticket pertenece al perfil
    antes de tocar nada.
    """
    cur.execute("SELECT comercio_id FROM tickets WHERE id = %s AND perfil_id = %s", (ticket_id, perfil_id))
    fila = cur.fetchone()
    if not fila:
        return False
    comercio_id = fila[0]

    if comercio_nombre:
        cur.execute("UPDATE comercios SET nombre = %s WHERE id = %s", (comercio_nombre, comercio_id))

    cur.execute(
        """UPDATE tickets SET fecha = %s, total = %s, estado = 'validado', motivo_revision = NULL
           WHERE id = %s AND perfil_id = %s""",
        (fecha, total, ticket_id, perfil_id)
    )

    for linea in lineas:
        cur.execute(
            """UPDATE lineas_ticket
               SET descripcion_original = %s, cantidad = %s, precio_unitario = %s, subtotal = %s
               WHERE id = %s AND ticket_id = %s""",
            (linea["descripcion_original"], linea["cantidad"], linea["precio_unitario"], linea["subtotal"], linea["id"], ticket_id)
        )

    return True

def eliminar_ticket(cur, ticket_id, perfil_id):
    cur.execute("SELECT imagen_path FROM tickets WHERE id = %s AND perfil_id = %s", (ticket_id, perfil_id))
    fila = cur.fetchone()
    if not fila:
        return False

    ruta_imagen = fila[0]
    cur.execute("DELETE FROM tickets WHERE id = %s AND perfil_id = %s", (ticket_id, perfil_id))

    if ruta_imagen and os.path.exists(ruta_imagen):
        os.remove(ruta_imagen)

    return cur.rowcount > 0