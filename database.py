import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# 1. Detectar si hay base de datos remota (Secrets de Streamlit o variable de entorno)
DATABASE_URL = os.getenv("DATABASE_URL")
try:
    import streamlit as st
    if not DATABASE_URL and "DATABASE_URL" in st.secrets:
        DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    pass

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    return sqlite3.connect("inventario.db")

def init_db():
    if not DATABASE_URL:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                unidad_medida TEXT NOT NULL,
                precio_costo INTEGER NOT NULL,
                precio_venta INTEGER NOT NULL,
                stock_actual INTEGER NOT NULL,
                stock_minimo INTEGER NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            );
        """)
        conn.commit()
        conn.close()

def registrar_producto(sku, nombre, categoria, unidad, costo, venta, stock, stock_min):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO productos (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """ if DATABASE_URL else """
            INSERT INTO productos (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(query, (sku, nombre, categoria, unidad, costo, venta, stock, stock_min))
        conn.commit()
        return True
    except Exception as e:
        if DATABASE_URL:
            conn.rollback()
        print(f"Error al registrar producto: {e}")
        return False
    finally:
        conn.close()

def obtener_todos_productos():
    conn = get_connection()
    try:
        if DATABASE_URL:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM productos ORDER BY nombre ASC;")
            rows = [dict(r) for r in cursor.fetchall()]
        else:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos ORDER BY nombre ASC;")
            rows = [dict(r) for r in cursor.fetchall()]
        return rows
    finally:
        conn.close()

def actualizar_stock_transaccional(producto_id, tipo, cantidad):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        param = "%s" if DATABASE_URL else "?"
        cursor.execute(f"SELECT stock_actual FROM productos WHERE id = {param};", (producto_id,))
        res = cursor.fetchone()
        if not res:
            return False

        stock_actual = res["stock_actual"] if isinstance(res, dict) else res[0]
        nuevo_stock = stock_actual + cantidad if tipo == "ENTRADA" else stock_actual - cantidad

        if nuevo_stock < 0:
            return False

        cursor.execute(f"UPDATE productos SET stock_actual = {param} WHERE id = {param};", (nuevo_stock, producto_id))
        cursor.execute(f"INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES ({param}, {param}, {param});", (producto_id, tipo, cantidad))
        conn.commit()
        return True
    except Exception as e:
        if DATABASE_URL:
            conn.rollback()
        print(f"Error en stock: {e}")
        return False
    finally:
        conn.close()

def generar_sku_sugerido(categoria):
    prefijos = {
        "Proteínas & Gainers": "PRO",
        "Snacks & Barras Proteicas": "SNK",
        "Pre-Entreno & Rendimiento": "PWR",
        "Bebidas Funcionales & Control de Peso": "DRK"
    }
    pref = prefijos.get(categoria, "GEN")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        param = "%s" if DATABASE_URL else "?"
        cursor.execute(f"SELECT COUNT(*) FROM productos WHERE sku LIKE {param};", (f"{pref}-%",))
        res = cursor.fetchone()
        count = res[0] if not isinstance(res, dict) else list(res.values())[0]
        return f"{pref}-{str(count + 1).zfill(3)}"
    finally:
        conn.close()