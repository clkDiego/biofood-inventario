import os
import sqlite3
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL"))
except Exception:
    DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    return sqlite3.connect("inventario.db")

def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            # PostgreSQL (Supabase)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    sku TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    unidad_medida TEXT NOT NULL,
                    precio_costo INTEGER NOT NULL DEFAULT 0,
                    precio_venta INTEGER NOT NULL,
                    stock_actual INTEGER NOT NULL,
                    stock_minimo INTEGER NOT NULL,
                    activo BOOLEAN NOT NULL DEFAULT TRUE
                );
            """)
            # Migración: asegurar que la columna activo exista
            cursor.execute("ALTER TABLE productos ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id SERIAL PRIMARY KEY,
                    producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
                    tipo TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            # SQLite (Local)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    unidad_medida TEXT NOT NULL,
                    precio_costo INTEGER NOT NULL DEFAULT 0,
                    precio_venta INTEGER NOT NULL,
                    stock_actual INTEGER NOT NULL,
                    stock_minimo INTEGER NOT NULL,
                    activo BOOLEAN NOT NULL DEFAULT 1
                );
            """)
            try:
                cursor.execute("ALTER TABLE productos ADD COLUMN activo BOOLEAN DEFAULT 1;")
            except Exception:
                pass

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                );
            """)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error al inicializar base de datos: {e}")
    finally:
        conn.close()

def registrar_producto(sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            query = """
                INSERT INTO productos (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE);
            """
            cursor.execute(query, (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo))
        else:
            query = """
                INSERT INTO productos (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1);
            """
            cursor.execute(query, (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al registrar producto: {e}")
        return False
    finally:
        conn.close()

def obtener_todos_productos(solo_activos=False):
    conn = get_connection()
    try:
        if DATABASE_URL:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            if solo_activos:
                cursor.execute("SELECT * FROM productos WHERE activo IS NOT FALSE ORDER BY id DESC;")
            else:
                cursor.execute("SELECT * FROM productos ORDER BY id DESC;")
            filas = cursor.fetchall()
            cursor.close()
            for f in filas:
                if f.get("activo") is None:
                    f["activo"] = True
            return filas
        else:
            cursor = conn.cursor()
            query = "SELECT id, sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo, activo FROM productos"
            if solo_activos:
                query += " WHERE activo = 1"
            query += " ORDER BY id DESC;"
            cursor.execute(query)
            filas = cursor.fetchall()
            cursor.close()
            columnas = ["id", "sku", "nombre", "categoria", "unidad_medida", "precio_costo", "precio_venta", "stock_actual", "stock_minimo", "activo"]
            resultado = []
            for fila in filas:
                item = dict(zip(columnas, fila))
                item["activo"] = bool(item.get("activo", True))
                resultado.append(item)
            return resultado
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []
    finally:
        conn.close()

def cambiar_estado_producto(producto_id, nuevo_estado):
    """Activa o da de baja un suplemento sin borrar su historial."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("UPDATE productos SET activo = %s WHERE id = %s;", (nuevo_estado, producto_id))
        else:
            cursor.execute("UPDATE productos SET activo = ? WHERE id = ?;", (1 if nuevo_estado else 0, producto_id))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al cambiar estado de producto: {e}")
        return False
    finally:
        conn.close()

def actualizar_stock_transaccional(producto_id, tipo, cantidad):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("SELECT stock_actual FROM productos WHERE id = %s;", (producto_id,))
        else:
            cursor.execute("SELECT stock_actual FROM productos WHERE id = ?;", (producto_id,))
        
        resultado = cursor.fetchone()
        if not resultado:
            return False
            
        stock_actual = resultado[0] if isinstance(resultado, tuple) else resultado["stock_actual"]

        if tipo == "SALIDA":
            if stock_actual < cantidad:
                return False
            nuevo_stock = stock_actual - cantidad
        else:
            nuevo_stock = stock_actual + cantidad

        if DATABASE_URL:
            cursor.execute("UPDATE productos SET stock_actual = %s WHERE id = %s;", (nuevo_stock, producto_id))
            cursor.execute("INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES (%s, %s, %s);", (producto_id, tipo, cantidad))
        else:
            cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?;", (nuevo_stock, producto_id))
            cursor.execute("INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES (?, ?, ?);", (producto_id, tipo, cantidad))

        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error en movimiento transaccional: {e}")
        return False
    finally:
        conn.close()

def actualizar_stock_minimo(producto_id, nuevo_minimo):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if DATABASE_URL:
            cursor.execute("UPDATE productos SET stock_minimo = %s WHERE id = %s;", (nuevo_minimo, producto_id))
        else:
            cursor.execute("UPDATE productos SET stock_minimo = ? WHERE id = ?;", (nuevo_minimo, producto_id))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al actualizar stock mínimo: {e}")
        return False
    finally:
        conn.close()

def generar_sku_sugerido(categoria):
    prefijos = {
        "Proteínas & Gainers": "BF-PROT",
        "Snacks & Barras Proteicas": "BF-BAR",
        "Pre-Entreno & Rendimiento": "BF-PRE",
        "Bebidas Funcionales & Control de Peso": "BF-FUNC"
    }
    pref = prefijos.get(categoria, "BF-ITEM")
    productos = obtener_todos_productos()
    conteo = sum(1 for p in productos if p.get("categoria") == categoria) + 1
    return f"{pref}-{conteo:03d}"

def obtener_historial_movimientos(limite=100):
    conn = get_connection()
    try:
        if DATABASE_URL:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            query = """
                SELECT m.fecha, p.sku, p.nombre, m.tipo, m.cantidad, p.unidad_medida
                FROM movimientos m
                JOIN productos p ON m.producto_id = p.id
                ORDER BY m.fecha DESC
                LIMIT %s;
            """
            cursor.execute(query, (limite,))
            filas = cursor.fetchall()
            cursor.close()
            return filas
        else:
            cursor = conn.cursor()
            query = """
                SELECT m.fecha, p.sku, p.nombre, m.tipo, m.cantidad, p.unidad_medida
                FROM movimientos m
                JOIN productos p ON m.producto_id = p.id
                ORDER BY m.fecha DESC
                LIMIT ?;
            """
            cursor.execute(query, (limite,))
            filas = cursor.fetchall()
            cursor.close()
            columnas = ["fecha", "sku", "nombre", "tipo", "cantidad", "unidad_medida"]
            return [dict(zip(columnas, fila)) for fila in filas]
    except Exception as e:
        print(f"Error al consultar historial: {e}")
        return []
    finally:
        conn.close()