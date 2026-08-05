from datetime import date


def validar_ticket(datos, tipos_permitidos, categorias_permitidas):
    errores = []

    if datos.get("tipo_ticket") not in tipos_permitidos:
        errores.append(f"tipo_ticket inválido: {datos.get('tipo_ticket')}")

    try:
        fecha = date.fromisoformat(datos["fecha"])
        if fecha > date.today():
            errores.append("La fecha está en el futuro")
    except (ValueError, TypeError, KeyError):
        errores.append("Fecha inválida o ausente")

    productos = datos.get("productos", [])
    if not productos:
        errores.append("El ticket no tiene ningún producto")

    suma_lineas = 0
    for p in productos:
        if p.get("categoria") not in categorias_permitidas:
            errores.append(f"Categoría inválida: {p.get('categoria')}")
        if not p.get("precio_unitario") or p["precio_unitario"] <= 0:
            errores.append(f"Precio no válido en: {p.get('descripcion')}")
        if not p.get("cantidad") or p["cantidad"] <= 0:
            errores.append(f"Cantidad no válida en: {p.get('descripcion')}")
        suma_lineas += (p.get("subtotal") or 0)

    total = datos.get("total") or 0
    if abs(suma_lineas - total) > 0.05:
        errores.append(f"Suma de líneas ({suma_lineas:.2f}) no coincide con total ({total:.2f})")

    desglose = datos.get("desglose_iva", [])
    if desglose:
        suma_desglose = sum(d["base_imponible"] + d["cuota"] for d in desglose)
        if abs(suma_desglose - total) > 0.05:
            errores.append(f"Desglose de IVA ({suma_desglose:.2f}) no coincide con total ({total:.2f})")

    return errores