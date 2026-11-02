from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent

CARPETAS_EXCLUIDAS = {".venv", ".git", "__pycache__"}
ARCHIVOS_EXCLUIDOS = {".env", ".env.local"}

def listar_archivos(nombre=""):
    archivos = []

    for ruta in PROYECTO.rglob("*"):
        relativa = ruta.relative_to(PROYECTO)

        if any(parte in CARPETAS_EXCLUIDAS for parte in relativa.parts):
            continue

        if not ruta.is_file() or ruta.is_symlink():
            continue

        if ruta.name in ARCHIVOS_EXCLUIDOS or ruta.name.startswith(".env."):
            continue

        if nombre.lower() in ruta.name.lower():
            archivos.append(str(relativa))

    return sorted(archivos)
