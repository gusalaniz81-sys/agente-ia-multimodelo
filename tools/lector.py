from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent

def leer_archivo(nombre):
    ruta = (PROYECTO / nombre).resolve()

    if not ruta.is_relative_to(PROYECTO):
        return "Error: no se permite acceder fuera del proyecto."

    if any(parte in {".venv", ".git", "__pycache__"} for parte in ruta.relative_to(PROYECTO).parts):
        return "Error: no se permite acceder a carpetas internas."
    
    if ruta.suffix != ".py":
        return "Error: solo se pueden leer archivos Python"

    if not ruta.is_file():
        return "Error: el archivo no existe."

    return ruta.read_text(encoding="utf-8")
