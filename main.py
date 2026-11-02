from openai import OpenAI
from dotenv import load_dotenv
from tools.archivos import listar_archivos
from tools.lector import leer_archivo
import json
from tools.buscador import buscar_texto
from tools.diagnostico import verificar_sintaxis
from tools.estructura import analizar_estructura

load_dotenv()

def main():
     print("Iniciando agente de IA multimodelo...")
     
     cliente = OpenAI()
     herramientas = [
    {
        "type": "function",
        "name": "listar_archivos",
        "description": "Busca archivos del proyecto por nombre o lista todos los archivos.",
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": ["string", "null"],
                    "description": "Nombre a buscar. Usar null para listar todos."
                }
            },
            "required": ["nombre"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "leer_archivo",
        "description": "Lee el contenido de archivos .py, .txt, .md y .json del proyecto.",
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Ruta relativa del archivo, por ejemplo prueba.md"
                }
            },
            "required": ["nombre"],
            "additionalProperties": False
        },
        "strict": True
    },

    {
    "type": "function",
    "name": "buscar_texto",
    "description": "Busca palabras, funciones, clases o fragmentos de código dentro de los archivos del proyecto y devuelve las coincidencias con sus números de línea.",
    "parameters": {
        "type": "object",
        "properties": {
            "texto": {
                "type": "string",
                "description": "Texto exacto o fragmento que se desea buscar, por ejemplo def main o class Agent"
            }
        },
        "required": ["texto"],
        "additionalProperties": False
    },
    "strict": True
},

    {
    "type": "function",
    "name": "verificar_sintaxis",
    "description": "Verifica errores de sintaxis en un archivo Python sin ejecutarlo. Devuelve la línea y descripción del error, si existe.",
    "parameters": {
        "type": "object",
        "properties": {
            "nombre": {
                "type": "string",
                "description": "Ruta relativa del archivo Python, por ejemplo core/agent.py"
            }
        },
        "required": ["nombre"],
        "additionalProperties": False
    },
    "strict": True
},
    {
    "type": "function",
    "name": "analizar_estructura",
    "description": "Identifica clases, funciones y métodos definidos en un archivo Python, indicando sus números de línea, sin ejecutar el código.",
    "parameters": {
        "type": "object",
        "properties": {
            "nombre": {
                "type": "string",
                "description": "Ruta relativa del archivo Python que se desea analizar."
            }
        },
        "required": ["nombre"],
        "additionalProperties": False
    },
    "strict": True
}
]


     instruccion = input("¿Que tarea querés realizar?")

     respuesta = cliente.responses.create(
         model="gpt-4.1-mini",
         instructions="Sos un asistente de IA. Responde en español. Si una tarea requiere consultar archivos, utilizá las " \
         "herramientas disponibles. No digas que vas a leer un archivo: ejecutá la herramientas leer_archivo. Cuando tengas " \
         "la información, respondé al usuario.",
         input=instruccion,
         tools=herramientas,
         max_output_tokens=1000
     )
     rondas = 0
     max_rondas = 5

     while rondas < max_rondas:
         rondas += 1
         resultados =[]
         print(f'Ronda actual: {rondas}')
         print(f'Estado de respuesta: {respuesta.status}')
         print(f'Motivo de interrupción: {respuesta.incomplete_details}')

         if not any(elemento.type == "function_call" for elemento in respuesta.output):
             break

         for elemento in respuesta.output:
             if elemento.type == "function_call":
                
                 if elemento.name == "listar_archivos":
                    argumentos = json.loads(elemento.arguments)
                    nombre = argumentos.get("nombre") or ""
                    archivos = listar_archivos(nombre)
                    print("Archivos encontrados:", archivos)

                    resultado_herramienta = {
                         "type": "function_call_output",
                         "call_id": elemento.call_id,
                         "output": json.dumps(archivos)
                     }
                    resultados.append(resultado_herramienta)
                
                 elif elemento.name == "leer_archivo":
                     argumentos = json.loads(elemento.arguments)
                     print("Herramienta utilizada: leer_archivo")
                     print("Archivo solicitado:", argumentos["nombre"])
                     contenido = leer_archivo(argumentos["nombre"])

                     resultado_herramienta = {
                         "type": "function_call_output",
                         "call_id": elemento.call_id,
                         "output": contenido
                     }
                     resultados.append(resultado_herramienta)

                 elif elemento.name == "buscar_texto":
                    argumentos = json.loads(elemento.arguments)
                    texto = argumentos["texto"]

                    print("Herramienta utilizada: buscar_texto")
                    print("Texto buscado:", texto)

                    coincidencias = buscar_texto(texto)

                    resultado_herramienta = {
                        "type": "function_call_output",
                        "call_id": elemento.call_id,
                        "output": json.dumps(coincidencias, ensure_ascii=False)
                    }
                    resultados.append(resultado_herramienta)

                 elif elemento.name == "verificar_sintaxis":
                      argumentos = json.loads(elemento.arguments)
                      nombre = argumentos["nombre"]

                      print("Herramienta utilizada: verificar_sintaxis")
                      print("Archivo analizado:", nombre)

                      diagnostico = verificar_sintaxis(nombre)

                      resultado_herramienta = {
                            "type": "function_call_output",
                            "call_id": elemento.call_id,
                            "output": diagnostico
                        }
                      resultados.append(resultado_herramienta)

                 elif elemento.name == "analizar_estructura":
                    argumentos = json.loads(elemento.arguments)
                    nombre = argumentos["nombre"]

                    print("Herramienta utilizada: analizar_estructura")
                    print("Archivo analizado:", nombre)

                    estructura = analizar_estructura(nombre)

                    resultado_herramienta = {
                        "type": "function_call_output",
                        "call_id": elemento.call_id,
                        "output": json.dumps(estructura, ensure_ascii=False)
                    }
                    resultados.append(resultado_herramienta)

         if respuesta.output and any(
             elemento.type == "function_call" for elemento in respuesta.output
         ):
             respuesta = cliente.responses.create(
                 model="gpt-4.1-mini",
                 previous_response_id=respuesta.id,
                 input=resultados,
                 tools=herramientas,
                 max_output_tokens=1000
             )
     if any(elemento.type == "function_call" for elemento in respuesta.output):
        print("Aviso: se alcanzó el límite de rondas y la tarea quedó incompleta.")
        return

     if respuesta.status == "incomplete":
         print("Aviso: el modelo no pudo completar su respuesta.")
         print(f"Motivo: {respuesta.incomplete_details}")
         return

     print("\nRespuesta del agente")
     print(respuesta.output_text)


if __name__ == "__main__":
    main()
