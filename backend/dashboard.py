def resumen_general(cur, perfil_id):
    cur.execute("SELECT COALESCE(SUM(total), 0) FROM tickets WHERE perfil_id = %s", (perfil_id,))
    gasto_total = cur.fetchone()[0]

    cur.execute(
        "SELECT estado, COUNT(*) FROM tickets WHERE perfil_id = %s GROUP BY estado",
        (perfil_id,)
    )
    tickets_por_estado = {estado: cantidad for estado, cantidad in cur.fetchall()}
    total_tickets = sum(tickets_por_estado.values())

    cur.execute(
        "SELECT COUNT(DISTINCT comercio_id) FROM tickets WHERE perfil_id = %s",
        (perfil_id,)
    )
    comercios_distintos = cur.fetchone()[0]

    cur.execute(
        """SELECT COUNT(DISTINCT p.id)
           FROM productos p
           JOIN lineas_ticket lt ON lt.producto_id = p.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s""",
        (perfil_id,)
    )
    productos_distintos = cur.fetchone()[0]

    ticket_medio = float(gasto_total) / total_tickets if total_tickets > 0 else 0

    return {
        "gasto_total": float(gasto_total),
        "total_tickets": total_tickets,
        "tickets_por_estado": tickets_por_estado,
        "ticket_medio": round(ticket_medio, 2),
        "comercios_distintos": comercios_distintos,
        "productos_distintos": productos_distintos,
    }

def gasto_por_mes(cur, perfil_id):
    cur.execute(
        """SELECT to_char(fecha, 'YYYY-MM') AS mes, SUM(total) AS total, COUNT(*) AS num_tickets
           FROM tickets
           WHERE perfil_id = %s
           GROUP BY mes
           ORDER BY mes""",
        (perfil_id,)
    )
    return [{"mes": m, "total": float(t), "num_tickets": n} for m, t, n in cur.fetchall()]


def gasto_por_dia_semana(cur, perfil_id):
    cur.execute(
        """SELECT
               CASE EXTRACT(DOW FROM fecha)
                   WHEN 0 THEN 'Domingo' WHEN 1 THEN 'Lunes' WHEN 2 THEN 'Martes'
                   WHEN 3 THEN 'Miércoles' WHEN 4 THEN 'Jueves' WHEN 5 THEN 'Viernes'
                   WHEN 6 THEN 'Sábado'
               END AS dia,
               EXTRACT(DOW FROM fecha) AS orden,
               SUM(total) AS total
           FROM tickets
           WHERE perfil_id = %s
           GROUP BY dia, orden
           ORDER BY orden""",
        (perfil_id,)
    )
    return [{"dia": d, "total": float(t)} for d, _, t in cur.fetchall()]


def comparativa_mes_actual_vs_anterior(cur, perfil_id):
    cur.execute(
        """SELECT
               to_char(fecha, 'YYYY-MM') AS mes,
               SUM(total) AS total
           FROM tickets
           WHERE perfil_id = %s
             AND fecha >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
           GROUP BY mes
           ORDER BY mes""",
        (perfil_id,)
    )
    filas = cur.fetchall()
    resultado = {"mes_anterior": 0, "mes_actual": 0}
    if len(filas) >= 1:
        resultado["mes_anterior"] = float(filas[0][1])
    if len(filas) >= 2:
        resultado["mes_actual"] = float(filas[1][1])

    if resultado["mes_anterior"] > 0:
        variacion = ((resultado["mes_actual"] - resultado["mes_anterior"]) / resultado["mes_anterior"]) * 100
    else:
        variacion = 0

    resultado["variacion_pct"] = round(variacion, 1)
    return resultado


def evolucion_completa(cur, perfil_id):
    return {
        "por_mes": gasto_por_mes(cur, perfil_id),
        "por_dia_semana": gasto_por_dia_semana(cur, perfil_id),
        "comparativa": comparativa_mes_actual_vs_anterior(cur, perfil_id),
    }

# ---- Nivel 3: Categorías ----

def gasto_por_categoria(cur, perfil_id):
    cur.execute(
        """SELECT cp.nombre, SUM(lt.subtotal) AS total
           FROM lineas_ticket lt
           JOIN productos p ON lt.producto_id = p.id
           JOIN categorias_producto cp ON p.categoria_id = cp.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s
           GROUP BY cp.nombre
           ORDER BY total DESC""",
        (perfil_id,)
    )
    return [{"categoria": c, "total": float(t)} for c, t in cur.fetchall()]


def evolucion_categoria(cur, perfil_id, categoria_nombre):
    cur.execute(
        """SELECT to_char(t.fecha, 'YYYY-MM') AS mes, SUM(lt.subtotal) AS total
           FROM lineas_ticket lt
           JOIN productos p ON lt.producto_id = p.id
           JOIN categorias_producto cp ON p.categoria_id = cp.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s AND cp.nombre = %s
           GROUP BY mes
           ORDER BY mes""",
        (perfil_id, categoria_nombre)
    )
    return [{"mes": m, "total": float(t)} for m, t in cur.fetchall()]


def ticket_medio_por_categoria(cur, perfil_id):
    cur.execute(
        """SELECT cp.nombre, AVG(lt.subtotal) AS media
           FROM lineas_ticket lt
           JOIN productos p ON lt.producto_id = p.id
           JOIN categorias_producto cp ON p.categoria_id = cp.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s
           GROUP BY cp.nombre
           ORDER BY media DESC""",
        (perfil_id,)
    )
    return [{"categoria": c, "media": round(float(m), 2)} for c, m in cur.fetchall()]


def categorias_completo(cur, perfil_id):
    return {
        "gasto_por_categoria": gasto_por_categoria(cur, perfil_id),
        "ticket_medio_por_categoria": ticket_medio_por_categoria(cur, perfil_id),
    }


# ---- Nivel 4: Comercios ----

def comercios_completo(cur, perfil_id):
    cur.execute(
        """SELECT c.nombre, SUM(t.total) AS gasto, COUNT(*) AS visitas, AVG(t.total) AS ticket_medio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.perfil_id = %s
           GROUP BY c.nombre
           ORDER BY gasto DESC""",
        (perfil_id,)
    )
    return [
        {"comercio": n, "gasto": float(g), "visitas": v, "ticket_medio": round(float(tm), 2)}
        for n, g, v, tm in cur.fetchall()
    ]


# ---- Nivel 5: Productos ----

def productos_completo(cur, perfil_id, limite=15):
    cur.execute(
        """SELECT p.nombre_normalizado, COUNT(*) AS veces, SUM(lt.subtotal) AS gasto_total
           FROM lineas_ticket lt
           JOIN productos p ON lt.producto_id = p.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s
           GROUP BY p.nombre_normalizado
           ORDER BY veces DESC
           LIMIT %s""",
        (perfil_id, limite)
    )
    top_frecuencia = [{"producto": n, "veces": v, "gasto_total": float(g)} for n, v, g in cur.fetchall()]

    cur.execute(
        """SELECT p.nombre_normalizado, SUM(lt.subtotal) AS gasto_total
           FROM lineas_ticket lt
           JOIN productos p ON lt.producto_id = p.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s
           GROUP BY p.nombre_normalizado
           ORDER BY gasto_total DESC
           LIMIT %s""",
        (perfil_id, limite)
    )
    top_gasto = [{"producto": n, "gasto_total": float(g)} for n, g in cur.fetchall()]

    return {"top_frecuencia": top_frecuencia, "top_gasto": top_gasto}


def evolucion_precio_producto(cur, perfil_id, producto_nombre):
    cur.execute(
        """SELECT t.fecha, lt.precio_unitario
           FROM lineas_ticket lt
           JOIN productos p ON lt.producto_id = p.id
           JOIN tickets t ON lt.ticket_id = t.id
           WHERE t.perfil_id = %s AND p.nombre_normalizado = %s
           ORDER BY t.fecha""",
        (perfil_id, producto_nombre)
    )
    return [{"fecha": f.isoformat(), "precio": float(p)} for f, p in cur.fetchall()]


# ---- Nivel 8: Patrones (co-ocurrencia) ----

def productos_comprados_juntos(cur, perfil_id, limite=15):
    cur.execute(
        """SELECT p1.nombre_normalizado AS producto_a, p2.nombre_normalizado AS producto_b, COUNT(*) AS veces_juntos
           FROM lineas_ticket lt1
           JOIN lineas_ticket lt2 ON lt1.ticket_id = lt2.ticket_id AND lt1.producto_id < lt2.producto_id
           JOIN productos p1 ON lt1.producto_id = p1.id
           JOIN productos p2 ON lt2.producto_id = p2.id
           JOIN tickets t ON lt1.ticket_id = t.id
           WHERE t.perfil_id = %s
           GROUP BY producto_a, producto_b
           HAVING COUNT(*) > 1
           ORDER BY veces_juntos DESC
           LIMIT %s""",
        (perfil_id, limite)
    )
    return [{"producto_a": a, "producto_b": b, "veces_juntos": v} for a, b, v in cur.fetchall()]


# ---- Nivel 9: Tipos de ticket ----

def gasto_por_tipo_ticket(cur, perfil_id):
    cur.execute(
        """SELECT tt.nombre, SUM(t.total) AS total, COUNT(*) AS num_tickets
           FROM tickets t
           JOIN tipos_ticket tt ON t.tipo_ticket_id = tt.id
           WHERE t.perfil_id = %s
           GROUP BY tt.nombre
           ORDER BY total DESC""",
        (perfil_id,)
    )
    return [{"tipo": n, "total": float(t), "num_tickets": c} for n, t, c in cur.fetchall()]


# ---- Nivel 7: Calidad del sistema ----

def calidad_sistema(cur, perfil_id):
    cur.execute("SELECT COUNT(*) FROM tickets WHERE perfil_id = %s", (perfil_id,))
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM tickets WHERE perfil_id = %s AND estado = 'validado'",
        (perfil_id,)
    )
    auto_validados = cur.fetchone()[0]

    porcentaje_auto = round((auto_validados / total) * 100, 1) if total > 0 else 0

    cur.execute(
        """SELECT motivo_revision FROM tickets
           WHERE perfil_id = %s AND motivo_revision IS NOT NULL""",
        (perfil_id,)
    )
    motivos = [fila[0] for fila in cur.fetchall()]

    from collections import Counter
    palabras_clave = Counter()
    for motivo in motivos:
        for fragmento in motivo.split(";"):
            fragmento = fragmento.strip()
            if ":" in fragmento:
                tipo_error = fragmento.split(":")[0].strip()
                palabras_clave[tipo_error] += 1

    motivos_frecuentes = [{"motivo": m, "veces": v} for m, v in palabras_clave.most_common(10)]

    return {
        "total_tickets": total,
        "auto_validados": auto_validados,
        "porcentaje_auto_validado": porcentaje_auto,
        "motivos_frecuentes": motivos_frecuentes,
    }


def ultimo_ticket(cur, perfil_id):
    cur.execute(
        """SELECT t.fecha, t.total, c.nombre AS comercio
           FROM tickets t
           JOIN comercios c ON t.comercio_id = c.id
           WHERE t.perfil_id = %s
           ORDER BY t.fecha DESC, t.id DESC
           LIMIT 1""",
        (perfil_id,)
    )
    fila = cur.fetchone()
    if not fila:
        return {"mensaje": "No hay tickets registrados"}
    fecha, total, comercio = fila
    return {"fecha": fecha.isoformat(), "total": float(total), "comercio": comercio}