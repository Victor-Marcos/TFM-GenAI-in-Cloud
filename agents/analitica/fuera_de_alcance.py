def nodo_fuera_de_alcance(estado):
    """
    Responde directamente cuando la pregunta no tiene relacion con los
    datos del usuario. No pasa por el Verificador ni el Sintetizador:
    no hay nada que verificar ni datos que sintetizar.
    """
    return {
        **estado,
        "respuesta_final": (
            "Soy un asistente centrado en tus tickets y gastos personales, "
            "así que no puedo ayudarte con eso. Pero sí puedo contarte en qué "
            "gastas más, qué compras con frecuencia, o cómo va la fiabilidad "
            "del sistema, entre otras cosas."
        ),
    }