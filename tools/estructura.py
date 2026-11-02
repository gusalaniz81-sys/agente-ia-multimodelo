
import ast
from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent

def analizar_estructura(nombre):
    ruta = (PROYECTO / nombre).resolve()

    if not ruta.is_relative_to(PROYECTO):
        return {"error": "Acceso fuera del proyecto."}

    if any(parte in {".venv", ".git", "__pycache__"} for parte in ruta.relative_to(PROYECTO).parts):
        return {"error": "Carpeta protegida."}

    if ruta.suffix != ".py" or not ruta.is_file():
        return {"error": "Se necesita un archivo Python existente."}

    try:
        if ruta.stat().st_size > 20_000:
            return {"error": "Archivo demasiado grande."}

        codigo = ruta.read_text(encoding="utf-8")
        arbol = ast.parse(codigo, filename=nombre)

        estructura = {
            "archivo": nombre,
            "funciones": [],
            "clases": []
        }

        for nodo in arbol.body:
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                estructura["funciones"].append({
                    "nombre": nodo.name,
                    "linea": nodo.lineno
                })

            elif isinstance(nodo, ast.ClassDef):
                metodos = []

                for elemento in nodo.body:
                    if isinstance(elemento, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        metodos.append({
                            "nombre": elemento.name,
                            "linea": elemento.lineno
                        })

                estructura["clases"].append({
                    "nombre": nodo.name,
                    "linea": nodo.lineno,
                    "metodos": metodos
                })

        return estructura

    except SyntaxError as error:
        return {"error": f"Error de sintaxis en línea {error.lineno}: {error.msg}"}

    except (OSError, UnicodeError) as error:
        return {"error": f"No se pudo leer el archivo: {type(error).__name__}"}
