import sqlite3
from typing import List, Dict, Any

DB_NAME = "inventario.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                unidad_medida TEXT NOT NULL DEFAULT 'Pote',
                precio_costo INTEGER NOT NULL DEFAULT 0 CHECK (precio_costo >= 0),
                precio_venta INTEGER NOT NULL DEFAULT 0 CHECK (precio_venta >= 0),
                stock_actual INTEGER NOT NULL CHECK (stock_actual >= 0),
                stock_minimo INTEGER NOT NULL CHECK (stock_minimo >= 0),
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                tipo_movimiento TEXT NOT NULL CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA')),
                cantidad INTEGER NOT NULL CHECK (cantidad > 0),
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

def registrar_producto(sku: str, nombre: str, categoria: str, unidad_medida: str,
                       precio_costo: int, precio_venta: int, stock_actual: int, stock_minimo: int) -> bool:
    """Inserta un nuevo producto con 8 parámetros comerciales."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO productos (sku, nombre, categoria, unidad_medida, precio_costo, precio_venta, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sku.strip().upper(), nombre.strip(), categoria.strip(), unidad_medida.strip(), precio_costo, precio_venta, stock_actual, stock_minimo))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def obtener_todos_productos() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def actualizar_stock_transaccional(producto_id: int, tipo_movimiento: str, cantidad: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (producto_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        stock_actual = row["stock_actual"]
        if tipo_movimiento == "SALIDA":
            if stock_actual < cantidad:
                return False
            nuevo_stock = stock_actual - cantidad
        elif tipo_movimiento == "ENTRADA":
            nuevo_stock = stock_actual + cantidad
        else:
            return False

        cursor.execute("""
            UPDATE productos 
            SET stock_actual = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nuevo_stock, producto_id))
        
        cursor.execute("""
            INSERT INTO movimientos (producto_id, tipo_movimiento, cantidad)
            VALUES (?, ?, ?)
        """, (producto_id, tipo_movimiento, cantidad))
        
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def eliminar_producto(producto_id: int) -> bool:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error:
        return False

def generar_sku_sugerido(categoria: str) -> str:
    prefijo = categoria[:3].upper() if categoria else "PRD"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos WHERE categoria = ?", (categoria,))
        conteo = cursor.fetchone()[0] + 1
        return f"{prefijo}-{conteo:03d}"