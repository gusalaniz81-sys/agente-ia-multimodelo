from pathlib import Path

PROYECTO = Path(__file__).resolve().parent.parent

def listar_archivos():
     archivos = []
     
     for ruta in PROYECTO.rglob("*"):
         if any(parte in {".venv", ".git", "__pycache__"} for parte in ruta.relative_to(PROYECTO).parts):
             continue
 
         if ruta.is_file() and ruta.name != ".env":
             archivos.append(str(ruta.relative_to(PROYECTO)))

     return archivos
