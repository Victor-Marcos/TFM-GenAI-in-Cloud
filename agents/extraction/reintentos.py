import time
import random


def llamar_con_reintentos(funcion, *args, max_intentos=6, espera_maxima=60, **kwargs):
    """
    Ejecuta una función que llama a la API de Gemini, reintentando con
    backoff exponencial truncado y jitter si se recibe un error 429
    (límite de peticiones excedido), tal como recomienda la
    documentación oficial de Google.
    """
    for intento in range(max_intentos):
        try:
            return funcion(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) and intento < max_intentos - 1:
                espera_base = min(2 ** intento, espera_maxima)
                espera = espera_base + random.uniform(0, 1)
                print(f"  -> 429 (cuota excedida), reintento {intento + 1}/{max_intentos} en {espera:.1f}s...")
                time.sleep(espera)
            else:
                raise