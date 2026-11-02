
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DATOS = (
    Path(__file__).resolve().parent.parent.parent
    / "datos" / "competidores.db"
)


def conectar():
    BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(BASE_DATOS)


def crear_tabla():
    with conectar() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS competidores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT NOT NULL,
                tienda TEXT NOT NULL,
                precio REAL NOT NULL,
                url TEXT,
                fecha TEXT NOT NULL
            )
        """)


def guardar_precio(producto, tienda, precio, url=""):
    crear_tabla()

    with conectar() as conexion:
        conexion.execute("""
            INSERT INTO competidores
            (producto, tienda, precio, url, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (
            producto,
            tienda,
            precio,
            url,
            datetime.now().isoformat(timespec="seconds")
        ))


def consultar_precios():
    crear_tabla()

    with conectar() as conexion:
        cursor = conexion.execute("""
            SELECT producto, tienda, precio, fecha
            FROM competidores
            ORDER BY fecha DESC
        """)

        return cursor.fetchall()

