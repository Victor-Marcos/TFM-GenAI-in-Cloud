from langgraph.graph import StateGraph, END
from agents.analitica.estado import EstadoAgente
from agents.analitica.orquestador import nodo_orquestador
from agents.analitica.verificador import nodo_verificador
from agents.analitica.sintetizador import nodo_sintetizador
from agents.analitica.especialista_financiero import nodo_financiero


def construir_grafo(cur):
    """
    Construye el grafo del sistema de agentes. cur se cierra sobre el
    nodo financiero (y, mas adelante, sobre los demas especialistas)
    para que tengan acceso a la base de datos.
    """
    grafo = StateGraph(EstadoAgente)

    grafo.add_node("orquestador", nodo_orquestador)
    grafo.add_node("financiero", lambda estado: nodo_financiero(estado, cur))
    grafo.add_node("verificador", nodo_verificador)
    grafo.add_node("sintetizador", nodo_sintetizador)

    grafo.set_entry_point("orquestador")

    def elegir_especialista(estado):
        especialista = estado["especialista_elegido"]
        if especialista == "financiero":
            return "financiero"
        return "financiero"  # de momento, todos van al financiero hasta tener el resto

    grafo.add_conditional_edges("orquestador", elegir_especialista, {
        "financiero": "financiero",
    })

    grafo.add_edge("financiero", "verificador")

    def decidir_siguiente(estado):
        if estado.get("motivo_fallo") is None:
            return "sintetizador"
        return "orquestador"

    grafo.add_conditional_edges("verificador", decidir_siguiente, {
        "sintetizador": "sintetizador",
        "orquestador": "orquestador",
    })

    grafo.add_edge("sintetizador", END)

    return grafo.compile()