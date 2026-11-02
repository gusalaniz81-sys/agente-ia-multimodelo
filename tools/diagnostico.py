import ast
from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent

def verificar_sintaxis(nombre):
    ruta = (PROYECTO / nombre).resolve()

    if not ruta.is_relative_to(PROYECTO):
        return "Error: acceso fuera del proyecto."

    if any(parte in {".venv", ".git", "__pycache__"} for parte in ruta.relative_to(PROYECTO).parts):
        return "Error: carpeta protegida."

    if ruta.suffix != ".py":
        return "Error: solo se permiten archivos Python."

    if not ruta.is_file():
        return "Error: el archivo no existe."

    try:
        if ruta.stat().st_size > 20_000:
            return "Error: archivo demasiado grande."

        codigo = ruta.read_text(encoding="utf-8")
        ast.parse(codigo, filename=nombre)

        return f"El archivo {nombre} no presenta errores de sintaxis."

    except SyntaxError as error:
        return (
            f"Error de sintaxis en {nombre}, "
            f"línea {error.lineno}: {error.msg}"
        )

    except (OSError, UnicodeError) as error:
        return f"Error al leer el archivo: {type(error).__name__}"
