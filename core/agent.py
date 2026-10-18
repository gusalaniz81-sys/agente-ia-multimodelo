class Agent:
    def __init__(self):
         self.nombre = "Agente IA Multimodelo"
    
    def recibir_instruccion(self, instruccion):
        print(f"instruccion recibida: {instruccion}")
    def identificar_tarea(self, instruccion):
        if "buscar" in instruccion.lower():
            return "busqueda"
        elif "calcular" in instruccion.lower():
            return "calculo"
        else:
            return "desconocida"
    def ejecutar_tarea(self, tipo_tarea):
        if tipo_tarea == "busqueda":
            print("Se debe utilizar una herramienta de busqueda")
        elif tipo_tarea == "Calculo":
            print("Se debe utilizar una herramienta de calculo")
        else:
            print("Todavía no se puede realizar la tarea")
