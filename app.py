import sys
import pandas as pd
import streamlit as st
from streamlit.web import cli as stcli

from database import (
    init_db,
    registrar_producto,
    obtener_todos_productos,
    actualizar_stock_transaccional,
    generar_sku_sugerido
)
from rules_engine import procesar_metricas_globales

# Catálogo oficial Biofood Nutrition
PRODUCTOS_BIOFOOD = {
    "Proteínas & Gainers": [
        {"nombre": "100% Whey Protein 5 Lbs (2.27 kg)", "unidad": "Pote", "costo": 58000, "venta": 90000},
        {"nombre": "100% Whey Protein 907g (2.0 Lbs)", "unidad": "Pote", "costo": 27000, "venta": 42000},
        {"nombre": "IsoWhey Isolate 2.2 Lbs", "unidad": "Pote", "costo": 36000, "venta": 55000},
        {"nombre": "Massive Pro 5 Lbs", "unidad": "Pote", "costo": 52000, "venta": 80000},
        {"nombre": "Massive Pro 1.0 Kg (2.2 Lbs)", "unidad": "Pote", "costo": 25000, "venta": 39000},
        {"nombre": "Big Mass Gainer 5 Kgs (11 Lbs)", "unidad": "Saco/Balde", "costo": 48000, "venta": 75000},
        {"nombre": "Diet Shake 1.5 Kgs (3.3 Lbs)", "unidad": "Pote", "costo": 29000, "venta": 45000}
    ],
    "Snacks & Barras Proteicas": [
        {"nombre": "Barra PRO2.0 Maní (Display 28 barras)", "unidad": "Display", "costo": 44000, "venta": 68000},
        {"nombre": "Barra PRO2.0 Almendras (Display 28 barras)", "unidad": "Display", "costo": 44000, "venta": 68000},
        {"nombre": "Barra PRO2.0 Toffee-Coco (Display 28 barras)", "unidad": "Display", "costo": 44000, "venta": 68000},
        {"nombre": "Barra Turrón Nougat (Display 28 barras)", "unidad": "Display", "costo": 44000, "venta": 68000},
        {"nombre": "Whey Cook Harina Proteica 2 Lbs", "unidad": "Bolsa", "costo": 27000, "venta": 42000}
    ],
    "Pre-Entreno & Rendimiento": [
        {"nombre": "Creatine Max Monohidrato 250g", "unidad": "Pote", "costo": 9500, "venta": 15000},
        {"nombre": "Full Injection Pre-Workout 1.125 Kg", "unidad": "Pote", "costo": 22000, "venta": 35000},
        {"nombre": "Nitropump Óxido Nítrico (60 cápsulas)", "unidad": "Frasco", "costo": 11000, "venta": 17000},
        {"nombre": "Extreme Pre Workout Fórmula Avanzada", "unidad": "Pote", "costo": 38000, "venta": 60000}
    ],
    "Bebidas Funcionales & Control de Peso": [
        {"nombre": "Bad Boss Energy Drink (Pack 24 latas)", "unidad": "Pack", "costo": 23000, "venta": 36000},
        {"nombre": "BIO2 Thermogenic Frutos Rojos (Pack 24 uds)", "unidad": "Pack", "costo": 27000, "venta": 42000},
        {"nombre": "BIO2 Thermogenic Limón (Pack 24 uds)", "unidad": "Pack", "costo": 23000, "venta": 36000},
        {"nombre": "Thermoactive Quemador (60 cápsulas)", "unidad": "Frasco", "costo": 10500, "venta": 17000},
        {"nombre": "Colágeno Hidrolizado Collagen+ 300g", "unidad": "Pote", "costo": 18000, "venta": 28000}
    ]
}

def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

            /* Banner Alerta Crítica Biofood */
            .critical-banner {
                background: linear-gradient(90deg, rgba(234, 88, 12, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
                border-left: 5px solid #FF5722;
                color: #FF8A65;
                padding: 14px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 0.95rem;
                margin-bottom: 20px;
                border: 1px solid rgba(255, 87, 34, 0.3);
            }

            /* Tarjetas KPIs Deportivas */
            .kpi-container {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 18px 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            }
            .kpi-title {
                color: #94A3B8;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 4px;
            }
            .kpi-value {
                font-size: 1.85rem;
                font-weight: 800;
                margin-bottom: 2px;
            }
            .kpi-subtext {
                font-size: 0.78rem;
                color: #64748B;
            }

            .kpi-val-total { color: #F8FAFC; }
            .kpi-val-money { color: #38BDF8; }
            .kpi-val-ok { color: #10B981; }
            .kpi-val-alert { color: #FF5722; }

            /* Botones estilo Biofood */
            div.stButton > button:first-child {
                background-color: #EA580C;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                transition: all 0.2s ease;
            }
            div.stButton > button:first-child:hover {
                background-color: #C2410C;
                border: none;
                color: #FFFFFF;
            }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Biofood Nutrition — Control de Stock",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_db()
    inyectar_estilos()

    raw_productos = obtener_todos_productos()
    datos = procesar_metricas_globales(raw_productos)

    # --- BARRA LATERAL (PC1: Alta Asistida) ---
    with st.sidebar:
        st.markdown("## ⚡ BIOFOOD NUTRITION")
        st.caption("Sistema de Bodega & Centro de Distribución")
        st.divider()

        st.markdown("**REGISTRAR SUPLEMENTO**")
        
        categoria_sel = st.selectbox("1. Línea de Producto:", list(PRODUCTOS_BIOFOOD.keys()))
        sugerencias_cat = PRODUCTOS_BIOFOOD[categoria_sel]
        nombres_sugeridos = [item["nombre"] for item in sugerencias_cat] + ["+ Ingresar otro producto manual..."]
        
        sel_nombre = st.selectbox("2. Catálogo Oficial Biofood:", nombres_sugeridos)
        
        if sel_nombre == "+ Ingresar otro producto manual...":
            nombre_final = st.text_input("Nombre comercial del producto:", placeholder="Ej: Glutamina Pure 300g").strip()
            unidad_default = "Pote"
            costo_default = 12000
            venta_default = 19990
        else:
            nombre_final = sel_nombre
            match = next((item for item in sugerencias_cat if item["nombre"] == sel_nombre), None)
            unidad_default = match["unidad"] if match else "Pote"
            costo_default = match["costo"] if match else 0
            venta_default = match["venta"] if match else 0

        opciones_unidad = ["Pote", "Display", "Pack", "Frasco", "Saco/Balde", "Bolsa", "Unidad"]
        idx_unidad = opciones_unidad.index(unidad_default) if unidad_default in opciones_unidad else 0
        unidad_medida = st.selectbox("3. Formato de Envase:", opciones_unidad, index=idx_unidad)

        auto_sku = st.checkbox("Generar SKU automático", value=True)
        if auto_sku:
            sku_final = generar_sku_sugerido(categoria_sel)
            st.info(f"SKU sugerido: **{sku_final}**")
        else:
            sku_final = st.text_input("Código SKU / Barras:", placeholder="Ej: BF-WHEY-5LB").strip().upper()

        with st.form("form_registro_biofood", clear_on_submit=True):
            c_costo, c_venta = st.columns(2)
            precio_costo = c_costo.number_input("Costo Laboratorio ($)", min_value=0, step=1000, value=costo_default)
            precio_venta = c_venta.number_input("Precio Venta Público ($)", min_value=0, step=1000, value=venta_default)
            
            c_stock, c_min = st.columns(2)
            stock_actual = c_stock.number_input("Stock Inicial", min_value=0, step=1, value=12)
            stock_minimo = c_min.number_input("Stock de Seguridad", min_value=0, step=1, value=5)

            btn_guardar = st.form_submit_button("Guardar en Inventario", use_container_width=True, type="primary")

            if btn_guardar:
                if not nombre_final:
                    st.error("⚠️ El nombre del producto es obligatorio.")
                elif not sku_final:
                    st.error("⚠️ El código SKU es obligatorio.")
                else:
                    exito = registrar_producto(
                        sku_final, nombre_final, categoria_sel, unidad_medida,
                        int(precio_costo), int(precio_venta), int(stock_actual), int(stock_minimo)
                    )
                    if exito:
                        st.toast(f"✅ '{nombre_final}' guardado con éxito.", icon="⚡")
                        st.rerun()
                    else:
                        st.error("❌ El código SKU o suplemento ya existe.")

    # --- PANEL PRINCIPAL ---
    st.markdown("# Biofood Nutrition — Centro de Gestión de Stock")
    st.caption("Monitoreo en Tiempo Real · Almacén Central")
    st.write("")

    # 1. Alerta Crítica Proactiva (PC3)
    if datos.get("productos_reposicion", 0) > 0:
        st.toast(f"¡Atención! {datos['productos_reposicion']} producto(s) en quiebre o nivel crítico.", icon="⚠️")
        st.markdown(
            f"""
            <div class="critical-banner">
                🚨 <strong>ALERTA DE REPOSICIÓN:</strong> {datos['productos_reposicion']} suplemento(s) se encuentran bajo el stock de seguridad — Se requiere generar orden de compra a laboratorio.
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Tarjetas de KPIs Comerciales
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="kpi-container">
                <div class="kpi-title">TOTAL UNIDADES</div>
                <div class="kpi-value kpi-val-total">{datos.get('total_existencias', 0)}</div>
                <div class="kpi-subtext">físicas en bodega</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with k2:
        val_costo = datos.get('valor_inventario_costo', 0)
        st.markdown(
            f"""
            <div class="kpi-container">
                <div class="kpi-title">CAPITAL INMOVILIZADO</div>
                <div class="kpi-value kpi-val-money">${val_costo:,}</div>
                <div class="kpi-subtext">costo de existencias</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with k3:
        st.markdown(
            f"""
            <div class="kpi-container">
                <div class="kpi-title">STOCK EN REGLA</div>
                <div class="kpi-value kpi-val-ok">{datos.get('productos_ok', 0)}</div>
                <div class="kpi-subtext">niveles óptimos</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with k4:
        st.markdown(
            f"""
            <div class="kpi-container">
                <div class="kpi-title">EN REPOSICIÓN</div>
                <div class="kpi-value kpi-val-alert">{datos.get('productos_reposicion', 0)}</div>
                <div class="kpi-subtext">bajo nivel mínimo</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Detalle Interactivo de Déficit
    if datos.get("productos_reposicion", 0) > 0:
        st.write("")
        with st.expander("🚨 **Ver detalle de suplementos que requieren reposición a laboratorio**", expanded=False):
            items_reposicion = [p for p in datos.get("catalogo", []) if p.get("estado") == "REPOSICIÓN"]
            lista_detalle = []
            for item in items_reposicion:
                st_act = item.get("stock_actual", 0)
                st_min = item.get("stock_minimo", 0)
                p_costo = item.get("precio_costo", 0)
                deficit = max(0, st_min - st_act)
                costo_reposicion = deficit * p_costo
                lista_detalle.append({
                    "SKU": item.get("sku", ""),
                    "SUPLEMENTO / PRODUCTO": item.get("nombre", ""),
                    "LÍNEA": item.get("categoria", ""),
                    "DISPONIBLE": f"{st_act} {item.get('unidad_medida', 'uds')}",
                    "STOCK MÍNIMO": f"{st_min} {item.get('unidad_medida', 'uds')}",
                    "DÉFICIT": f"+{deficit} {item.get('unidad_medida', 'uds')}",
                    "INVERSIÓN REPOSICIÓN ($)": f"${costo_reposicion:,}"
                })
            if lista_detalle:
                st.dataframe(pd.DataFrame(lista_detalle), use_container_width=True, hide_index=True)

    st.write("")
    st.divider()

    # 4. Catálogo y Trazabilidad
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown("### Catálogo de Existencias y Precios")
    with col_t2:
        st.caption(f"**{len(datos.get('catalogo', []))}** productos registrados")

    if datos.get("catalogo"):
        df = pd.DataFrame(datos["catalogo"])

        filtro_col1, filtro_col2 = st.columns([2, 2])
        with filtro_col1:
            busqueda = st.text_input("🔍 Buscar por suplemento o SKU:", placeholder="Ej: Whey, Creatina, PRO-001").strip().lower()
        with filtro_col2:
            filtro_estado = st.selectbox("Filtrar por Condición:", ["Todos", "OK", "REPOSICIÓN"])

        df_filtrado = df.copy()
        if busqueda:
            df_filtrado = df_filtrado[
                df_filtrado["nombre"].str.lower().str.contains(busqueda) |
                df_filtrado["sku"].str.lower().str.contains(busqueda)
            ]
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["estado"] == filtro_estado]

        columnas_deseadas = ["sku", "nombre", "categoria", "unidad_medida", "precio_costo", "precio_venta", "stock_actual", "stock_minimo", "margen_pct", "estado"]
        columnas_presentes = [c for c in columnas_deseadas if c in df_filtrado.columns]
        
        df_vista = df_filtrado[columnas_presentes]
        nombres_cabecera = {
            "sku": "SKU", "nombre": "PRODUCTO", "categoria": "LÍNEA", 
            "unidad_medida": "ENVASE", "precio_costo": "COSTO ($)", 
            "precio_venta": "VENTA ($)", "stock_actual": "STOCK", 
            "stock_minimo": "MÍNIMO", "margen_pct": "MARGEN %", "estado": "ESTADO"
        }
        df_vista = df_vista.rename(columns=nombres_cabecera)

        st.dataframe(df_vista, use_container_width=True, hide_index=True)

        csv_data = df_vista.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Planilla de Inventario (CSV)",
            data=csv_data,
            file_name="inventario_biofood_nutrition.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay existencias registradas. Ingresa los primeros suplementos desde el panel izquierdo.")

    st.write("")

    # 5. Registro Transaccional (PC2)
    with st.expander("⚡ Registrar Movimiento de Bodega (Venta / Recepción de Laboratorio)"):
        if datos.get("catalogo"):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            opciones = {
                f"{p['sku']} - {p['nombre']} (Stock actual: {p['stock_actual']} {p.get('unidad_medida', '')})": p["id"]
                for p in datos["catalogo"]
            }
            prod_sel = c1.selectbox("Seleccionar Suplemento:", list(opciones.keys()))
            tipo = c2.selectbox(
                "Tipo de Movimiento:",
                ["SALIDA", "ENTRADA"],
                format_func=lambda x: "Venta / Despacho (Salida)" if x == "SALIDA" else "Recepción Laboratorio (Entrada)"
            )
            cant = c3.number_input("Cantidad de Envases:", min_value=1, step=1, value=1)

            if c4.button("Confirmar Movimiento", use_container_width=True, type="primary"):
                id_seleccionado = opciones[prod_sel]
                if actualizar_stock_transaccional(id_seleccionado, tipo, int(cant)):
                    st.toast(f"Operación de {tipo} registrada correctamente.", icon="⚡")
                    st.success("Movimiento registrado en base de datos.")
                    st.rerun()
                else:
                    st.error("Error: Salida rechazada por saldo insuficiente en bodega.")

if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", "app.py"]
        sys.exit(stcli.main())