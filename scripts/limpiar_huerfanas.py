import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from agents.extraction.config import get_db_connection
from pathlib import Path

conn = get_db_connection()
cur = conn.cursor()

cur.execute("SELECT imagen_path FROM tickets WHERE imagen_path IS NOT NULL")
rutas_en_uso = {fila[0] for fila in cur.fetchall()}

directorio = Path(__file__).parent.parent / "data" / "tickets_guardados"
borradas = 0
for fichero in directorio.glob("*.jpg"):
    if str(fichero) not in rutas_en_uso:
        fichero.unlink()
        borradas += 1

print(f"Borradas {borradas} imágenes huérfanas")