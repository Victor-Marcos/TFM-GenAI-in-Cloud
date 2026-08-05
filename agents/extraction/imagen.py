import uuid
from pathlib import Path
from PIL import Image
from io import BytesIO
import pillow_heif
pillow_heif.register_heif_opener()

DIRECTORIO_ALMACENAMIENTO = Path(__file__).parent.parent.parent / "data" / "tickets_guardados"


def preparar_imagen(fuente, max_ancho=1600):
    with Image.open(fuente) as img:
        img = img.convert("RGB")
        if img.width > max_ancho:
            ratio = max_ancho / img.width
            nuevo_alto = int(img.height * ratio)
            img = img.resize((max_ancho, nuevo_alto))

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()


def guardar_imagen_permanente(imagen_bytes):
    DIRECTORIO_ALMACENAMIENTO.mkdir(parents=True, exist_ok=True)
    nombre_fichero = f"{uuid.uuid4()}.jpg"
    ruta_destino = DIRECTORIO_ALMACENAMIENTO / nombre_fichero

    with open(ruta_destino, "wb") as f:
        f.write(imagen_bytes)

    return str(ruta_destino)