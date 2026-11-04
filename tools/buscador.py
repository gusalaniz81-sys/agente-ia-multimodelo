from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent
EXTENSIONES = {".py", ".txt", ".md", ".json"}
CARPETAS_EXCLUIDAS = {".venv", ".git", "__pycache__", "datos"}

def buscar_texto(texto):
    if not isinstance(texto, str) or not texto.strip():
        return "Error: ingresá un texto para buscar."

    resultados = []

    for ruta in PROYECTO.rglob("*"):
        relativa = ruta.relative_to(PROYECTO)

        if any(parte in CARPETAS_EXCLUIDAS for parte in relativa.parts):
            continue

        if ruta.is_symlink() or not ruta.is_file():
            continue

        if ruta.name == ".env" or ruta.name.startswith(".env."):
            continue

        if ruta.suffix.lower() not in EXTENSIONES:
            continue

        if ruta.stat().st_size > 20_000:
            continue

        try:
            with ruta.open(encoding="utf-8") as archivo:
                for numero, linea in enumerate(archivo, start=1):
                    if texto.lower() in linea.lower():
                        resultados.append({
                            "archivo": str(relativa),
                            "linea": numero,
                            "contenido": linea.strip()[:200]
                        })

                        if len(resultados) >= 30:
                            return resultados

        except (OSError, UnicodeError):
            continue

    return resultados
