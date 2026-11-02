
from decimal import Decimal


def comparar_precios(mi_precio, competidores):
    mi_precio = Decimal(str(mi_precio))
    resultados = []

    for producto in competidores:
        precio = Decimal(str(producto["precio"]))
        diferencia = mi_precio - precio

        resultados.append({
            "nombre": producto["nombre"],
            "precio": float(precio),
            "diferencia": float(diferencia),
            "mas_barato_que_yo": precio < mi_precio
        })

    resultados.sort(key=lambda producto: producto["precio"])

    return {
        "mi_precio": float(mi_precio),
        "competidores": resultados
    }
