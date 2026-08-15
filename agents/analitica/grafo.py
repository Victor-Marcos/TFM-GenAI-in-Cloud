from langgraph.graph import StateGraph, END
from agents.analitica.estado import EstadoAgente
from agents.analitica.orquestador import nodo_orquestador
from agents.analitica.verificador import nodo_verificador
from agents.analitica.sintetizador import nodo_sintetizador
from agents.analitica.especialista_financiero import nodo_financiero
from agents.analitica.especialista_patrones import nodo_patrones
from agents.analitica.especialista_calidad import nodo_calidad
from agents.analitica.especialista_sql_libre import nodo_sql_libre
from agents.analitica.fuera_de_alcance import nodo_fuera_de_alcance


def construir_grafo(cur):
    grafo = StateGraph(EstadoAgente)

    grafo.add_node("orquestador", nodo_orquestador)
    grafo.add_node("financiero", lambda estado: nodo_financiero(estado, cur))
    grafo.add_node("patrones", lambda estado: nodo_patrones(estado, cur))
    grafo.add_node("calidad", lambda estado: nodo_calidad(estado, cur))
    grafo.add_node("sql_libre", lambda estado: nodo_sql_libre(estado, cur))
    grafo.add_node("fuera_de_alcance", nodo_fuera_de_alcance)
    grafo.add_node("verificador", nodo_verificador)
    grafo.add_node("sintetizador", nodo_sintetizador)

    grafo.set_entry_point("orquestador")

    def elegir_especialista(estado):
        return estado["especialista_elegido"]

    grafo.add_conditional_edges("orquestador", elegir_especialista, {
        "financiero": "financiero",
        "patrones": "patrones",
        "calidad": "calidad",
        "sql_libre": "sql_libre",
        "fuera_de_alcance": "fuera_de_alcance",
    })

    grafo.add_edge("financiero", "verificador")
    grafo.add_edge("patrones", "verificador")
    grafo.add_edge("calidad", "verificador")
    grafo.add_edge("sql_libre", "verificador")

    def decidir_siguiente(estado):
        if estado.get("motivo_fallo") is None:
            return "sintetizador"
        return "orquestador"

    grafo.add_conditional_edges("verificador", decidir_siguiente, {
        "sintetizador": "sintetizador",
        "orquestador": "orquestador",
    })

    grafo.add_edge("sintetizador", END)
    grafo.add_edge("fuera_de_alcance", END)

    return grafo.compile()