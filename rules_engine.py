from typing import List, Dict, Any

def evaluar_estado_producto(stock_actual: int, stock_minimo: int) -> Dict[str, Any]:
    """Evalúa si un SKU quiebra el stock de seguridad (PC3)."""
    if stock_actual <= stock_minimo:
        return {"estado": "REPOSICIÓN", "es_critico": True}
    return {"estado": "OK", "es_critico": False}

def procesar_metricas_globales(productos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula existencias, capital inmovilizado y márgenes comerciales."""
    total_existencias = sum(p.get("stock_actual", 0) for p in productos)
    valor_inventario_costo = sum(p.get("stock_actual", 0) * p.get("precio_costo", 0) for p in productos)
    valor_inventario_venta = sum(p.get("stock_actual", 0) * p.get("precio_venta", 0) for p in productos)
    criticos = 0
    seguros = 0

    for p in productos:
        evaluacion = evaluar_estado_producto(p.get("stock_actual", 0), p.get("stock_minimo", 0))
        p["estado"] = evaluacion["estado"]
        
        p_costo = p.get("precio_costo", 0)
        p_venta = p.get("precio_venta", 0)
        p["margen_pct"] = round(((p_venta - p_costo) / p_venta * 100), 1) if p_venta > 0 else 0
        
        if evaluacion["es_critico"]:
            criticos += 1
        else:
            seguros += 1

    return {
        "total_existencias": total_existencias,
        "valor_inventario_costo": valor_inventario_costo,
        "valor_inventario_venta": valor_inventario_venta,
        "productos_ok": seguros,
        "productos_reposicion": criticos,
        "catalogo": productos
    }