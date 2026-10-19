from openai import OpenAI
from dotenv import load_dotenv
from tools.archivos import listar_archivos
from tools.lector import leer_archivo
import json

load_dotenv()

def main():
     print("Iniciando agente de IA multimodelo...")
     
     cliente = OpenAI()
     herramientas = [
    {
        "type": "function",
        "name": "listar_archivos",
        "description": "Lista los archivos del proyecto Python",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "leer_archivo",
        "description": "Lee el contenido de un archivo Python del proyecto",
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Ruta del archivo, por ejemplo core/agent.py"
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
         instructions="Sos un asistente de IA. Responde en español de forma clara y útil",
         input=instruccion,
         tools=herramientas,
         max_output_tokens=300
     )
     resultados =[]

     for elemento in respuesta.output:
         if elemento.type == "function_call":
             
             if elemento.name == "listar_archivos":
                 archivos = listar_archivos()
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

     if respuesta.output and any(
         elemento.type == "function_call" for elemento in respuesta.output
     ):
         respuesta = cliente.responses.create(
             model="gpt-4.1-mini",
             previous_response_id=respuesta.id,
             input=[resultado_herramienta],
             max_output_tokens=300
         )

     print("\nRespuesta del agente")
     print(respuesta.output_text)


if __name__ == "__main__":
    main()
