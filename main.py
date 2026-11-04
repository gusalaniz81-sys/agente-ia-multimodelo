from openai import OpenAI
from dotenv import load_dotenv
from tools.archivos import listar_archivos
from tools.lector import leer_archivo
import json
from tools.buscador import buscar_texto
from tools.diagnostico import verificar_sintaxis
from tools.estructura import analizar_estructura
from modulos.mercado_libre.consultar_publicacion import consultar_publicacion
from modulos.mercado_libre.listar_publicaciones import listar_publicaciones

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
},
    {
    "type": "function",
    "name": "consultar_publicacion",
    "description": "Consulta en Mercado Libre el título, precio, moneda, enlace y envío gratis de una publicación a partir de su ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "item_id": {
                "type": "string",
                "description": "ID de la publicación sin guiones, por ejemplo MLA1910816755"
            }
        },
        "required": ["item_id"],
        "additionalProperties": False
    },
    "strict": True
},
    {
    "type": "function",
    "name": "listar_publicaciones",
    "description": "Lista las publicaciones de la cuenta conectada de Mercado Libre, con ID, título, precio, moneda y estado. Devuelve también el total de publicaciones. Para ver las siguientes, volver a llamarla con desde igual a la cantidad total ya mostrada.",
    "parameters": {
        "type": "object",
        "properties": {
            "estado": {
                "type": ["string", "null"],
                "enum": ["active", "paused", "closed", None],
                "description": "Filtra por estado: active, paused o closed. Usar null para no filtrar."
            },
            "limite": {
                "type": ["integer", "null"],
                "description": "Cantidad de publicaciones, de 1 a 20. Usar null para el valor por defecto, 10."
            },
            "desde": {
                "type": ["integer", "null"],
                "description": "Cantidad de publicaciones a saltear. Usar null para empezar desde la primera."
            }
        },
        "required": ["estado", "limite", "desde"],
        "additionalProperties": False
    },
    "strict": True
}
]


     ultima_respuesta_id = None

     while True:
         try:
             instruccion = input("\n¿Qué tarea querés realizar? (escribí salir para terminar) ").strip()
         except (EOFError, KeyboardInterrupt):
             print()
             break

         if not instruccion:
             continue

         if instruccion.lower() == "salir":
             break


         respuesta = cliente.responses.create(
             model="gpt-4.1-mini",
             instructions="Sos un asistente de IA. Responde en español. Si una tarea requiere consultar archivos, utilizá las " \
             "herramientas disponibles. No digas que vas a leer un archivo: ejecutá la herramientas leer_archivo. Cuando tengas " \
             "la información, respondé al usuario.",
             previous_response_id=ultima_respuesta_id,
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

                     elif elemento.name == "consultar_publicacion":
                        argumentos = json.loads(elemento.arguments)
                        item_id = argumentos["item_id"]

                        print("Herramienta utilizada: consultar_publicacion")
                        print("Publicación consultada:", item_id)

                        publicacion = consultar_publicacion(item_id)

                        resultado_herramienta = {
                            "type": "function_call_output",
                            "call_id": elemento.call_id,
                            "output": json.dumps(publicacion, ensure_ascii=False)
                        }
                        resultados.append(resultado_herramienta)

                     elif elemento.name == "listar_publicaciones":
                        argumentos = json.loads(elemento.arguments)

                        print("Herramienta utilizada: listar_publicaciones")

                        publicaciones = listar_publicaciones(
                            argumentos["estado"],
                            argumentos["limite"],
                            argumentos["desde"]
                        )

                        resultado_herramienta = {
                            "type": "function_call_output",
                            "call_id": elemento.call_id,
                            "output": json.dumps(publicaciones, ensure_ascii=False)
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
            ultima_respuesta_id = None
            continue

         if respuesta.status == "incomplete":
             print("Aviso: el modelo no pudo completar su respuesta.")
             print(f"Motivo: {respuesta.incomplete_details}")
             ultima_respuesta_id = respuesta.id
             continue

         print("\nRespuesta del agente")
         print(respuesta.output_text)
         ultima_respuesta_id = respuesta.id


if __name__ == "__main__":
    main()
