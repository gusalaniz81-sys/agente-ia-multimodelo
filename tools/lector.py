from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent

EXTENSIONES = {".py", ".txt", ".md", ".json"}
CARPETAS_EXCLUIDAS = {".venv", ".git", "__pycache__"}

def leer_archivo(nombre):
    ruta = (PROYECTO / nombre).resolve()

    if not ruta.is_relative_to(PROYECTO):
        return "Error: no se permite acceder fuera del proyecto."

    relativa = ruta.relative_to(PROYECTO)

    if any(parte in CARPETAS_EXCLUIDAS for parte in relativa.parts):
        return "Error: no se permite acceder a carpetas internas."

    if ruta.name == ".env" or ruta.name.startswith(".env."):
        return "Error: archivo protegido."

    if ruta.suffix.lower() not in EXTENSIONES:
        return "Error: extensión de archivo no permitida."

    if not ruta.is_file():
        return "Error: el archivo no existe."

    try:
        if ruta.stat().st_size > 20_000:
            return "Error: el archivo supera el tamaño permitido."

        return ruta.read_text(encoding="utf-8")

    except (OSError, UnicodeError) as error:
        return f"Error al leer el archivo: {type(error).__name__}"

