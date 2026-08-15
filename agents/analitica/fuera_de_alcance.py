def nodo_fuera_de_alcance(estado):
    return {
        **estado,
        "respuesta_final": (
            "Puedo ayudarte a entender tus tickets y gastos: cuánto y en qué gastas, "
            "qué productos compras con más frecuencia, en qué comercios sueles comprar, "
            "o qué tan fiable está siendo el sistema de extracción de tickets. "
            "¿Sobre qué te gustaría preguntar?"
        ),
    }