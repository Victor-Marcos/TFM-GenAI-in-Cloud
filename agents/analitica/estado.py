from typing import TypedDict, Optional

class EstadoAgente(TypedDict):
    pregunta: str
    perfil_id: int
    especialista_elegido: Optional[str]
    respuesta_especialista: Optional[str]
    motivo_fallo: Optional[str]
    intentos: int
    respuesta_final: Optional[str]