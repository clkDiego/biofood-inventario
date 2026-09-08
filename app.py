import os
import sys
import pandas as pd
import streamlit as st
from streamlit.web import cli as stcli

from database import (
    init_db,
    registrar_producto,
    obtener_todos_productos,
    actualizar_stock_transaccional,
    actualizar_stock_minimo,
    actualizar_producto_desde_tabla,
    cambiar_estado_producto,
    generar_sku_sugerido,
    obtener_historial_movimientos
)
from rules_engine import procesar_metricas_globales

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

PRODUCTOS_BIOFOOD = {
    "Polvos": [
        {"nombre": "100% Whey Protein 5 Lbs (2.27 kg)", "unidad": "Pote", "venta": 90000},
        {"nombre": "100% Whey Protein 907g (2.0 Lbs)", "unidad": "Pote", "venta": 42000},
        {"nombre": "IsoWhey Isolate 2.2 Lbs", "unidad": "Pote", "venta": 55000},
        {"nombre": "Massive Pro 5 Lbs", "unidad": "Pote", "venta": 80000},
        {"nombre": "Massive Pro 1.0 Kg (2.2 Lbs)", "unidad": "Pote", "venta": 39000},
        {"nombre": "Big Mass Gainer 5 Kgs (11 Lbs)", "unidad": "Saco/Balde", "venta": 75000},
        {"nombre": "Diet Shake 1.5 Kgs (3.3 Lbs)", "unidad": "Pote", "venta": 45000}
    ],
    "Cápsulas": [
        {"nombre": "ZMA (90 Cápsulas)", "unidad": "Frasco", "venta": 15000},
        {"nombre": "Reductor Plus (60 Cápsulas)", "unidad": "Frasco", "venta": 15000},
        {"nombre": "Reductor Plus (120 Cápsulas)", "unidad": "Frasco", "venta": 27000},
        {"nombre": "Nitro Pump (60 Cápsulas)", "unidad": "Frasco", "venta": 17000},
        {"nombre": "Nitro Pump (120 Cápsulas)", "unidad": "Frasco", "venta": 30000},
        {"nombre": "Thermo Active (60 Cápsulas)", "unidad": "Frasco", "venta": 17000},
        {"nombre": "Thermo Active (120 Cápsulas)", "unidad": "Frasco", "venta": 30000}
    ],
    "Snacks & Barras Proteicas": [
        {"nombre": "Barra PRO2.0 Maní (Display 28 barras)", "unidad": "Display", "venta": 68000},
        {"nombre": "Barra PRO2.0 Almendras (Display 28 barras)", "unidad": "Display", "venta": 68000},
        {"nombre": "Barra PRO2.0 Toffee-Coco (Display 28 barras)", "unidad": "Display", "venta": 68000},
        {"nombre": "Barra Turrón Nougat (Display 28 barras)", "unidad": "Display", "venta": 68000},
        {"nombre": "Whey Cook Harina Proteica 2 Lbs", "unidad": "Bolsa", "venta": 42000}
    ],
    "Pre-Entreno & Rendimiento": [
        {"nombre": "Creatine Max Monohidrato 250g", "unidad": "Pote", "venta": 15000},
        {"nombre": "Full Injection Pre-Workout 1.125 Kg", "unidad": "Pote", "venta": 35000},
        {"nombre": "Extreme Pre Workout Fórmula Avanzada", "unidad": "Pote", "venta": 60000}
    ],
    "Bebidas": [
        {"nombre": "Bad Boss Energy Drink (Pack 24 Uds)", "unidad": "Pack", "venta": 36000},
        {"nombre": "BIO2 Thermogenic Frutos Rojos (Pack 24 uds)", "unidad": "Pack", "venta": 42000},
        {"nombre": "BIO2 Thermogenic Limón (Pack 24 uds)", "unidad": "Pack", "venta": 36000},
        {"nombre": "Colágeno Hidrolizado Collagen+ 300g", "unidad": "Pote", "venta": 28000}
    ]
}

OPCIONES_ENVASE = ["Frasco", "Pote", "Display", "Caja", "Pack", "Saco/Balde", "Bolsa", "Unidad"]

MAPA_MIGRACION_CATEGORIAS = {
    "Proteínas & Gainers": "Polvos",
    "Bebidas Funcionales & Control de Peso": "Bebidas"
}

def inyectar_estilos(alto_contraste=False):
    if alto_contraste:
        bg_app = "#000000"
        bg_card = "#0A0A0A"
        border_card = "2px solid #FFFFFF"
        text_primary = "#FFFFFF"
        text_muted = "#D1D5DB"
        val_money = "#00E5FF"
        val_ok = "#00FF66"
        val_alert = "#FF3333"
        banner_bg = "#1A0000"
        banner_border = "2px solid #FF3B30"
        banner_text = "#FF9999"
    else:
        bg_app = "#0B0F17"
        bg_card = "#141C2E"
        border_card = "1px solid #1E293B"
        text_primary = "#F8FAFC"
        text_muted = "#94A3B8"
        val_money = "#38BDF8"
        val_ok = "#10B981"
        val_alert = "#F97316"
        banner_bg = "linear-gradient(90deg, rgba(239, 68, 68, 0.15) 0%, rgba(15, 23, 42, 0.8) 100%)"
        banner_border = "1px solid rgba(239, 68, 68, 0.25)"
        banner_text = "#FCA5A5"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
            
            html, body, [class*="css"] {{
                font-family: 'Plus Jakarta Sans', sans-serif;
            }}

            .stApp, [data-testid="stAppViewContainer"] {{
                background-color: {bg_app} !important;
            }}

            section[data-testid="stSidebar"] {{
                background-color: {bg_app} !important;
                border-right: 1px solid #1F2937 !important;
            }}

            /* Asegurar que los textos principales sean siempre nítidos y claros */
            h1, h2, h3, h4, [data-testid="stMarkdownContainer"] p {{
                color: {text_primary} !important;
            }}

            /* Banner Alerta */
            .critical-banner {{
                background: {banner_bg} !important;
                border: {banner_border} !important;
                border-left: 5px solid #EF4444 !important;
                color: {banner_text} !important;
                padding: 14px 18px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 0.92rem;
                margin-bottom: 20px;
            }}

            /* Tarjetas de KPIs */
            .kpi-container {{
                background: {bg_card} !important;
                border: {border_card} !important;
                border-radius: 12px;
                padding: 16px 18px;
                box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.35);
            }}
            .kpi-title {{
                color: {text_muted} !important;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.07em;
                text-transform: uppercase;
                margin-bottom: 6px;
            }}
            .kpi-value {{
                font-size: 1.85rem;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 4px;
            }}
            .kpi-subtext {{
                font-size: 0.76rem;
                color: {text_muted} !important;
            }}

            .kpi-val-total {{ color: {text_primary} !important; }}
            .kpi-val-money {{ color: {val_money} !important; }}
            .kpi-val-ok {{ color: {val_ok} !important; }}
            .kpi-val-alert {{ color: {val_alert} !important; }}

            /* Botones de acción */
            div.stButton > button:first-child {{
                background: linear-gradient(135deg, #F97316 0%, #EA580C 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 700 !important;
                padding: 0.55rem 1rem !important;
                box-shadow: 0 2px 8px rgba(249, 115, 22, 0.25) !important;
            }}
            div.stButton > button:first-child:hover {{
                background: linear-gradient(135deg, #FB923C 0%, #F97316 100%) !important;
                color: #FFFFFF !important;
            }}

            div[role="radiogroup"] {{
                gap: 16px;
            }}
        </style>
    """, unsafe_allow_html=True)

def main():
    existe_logo = os.path.exists(LOGO_PATH)
    favicon_path = LOGO_PATH if existe_logo else None

    st.set_page_config(
        page_title="Biofood Nutrition — Control de Stock",
        page_icon=favicon_path,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    if "alto_contraste" not in st.session_state:
        st.session_state["alto_contraste"] = False

    init_db()

    ADMIN_PIN = st.secrets.get("ADMIN_PIN", "2817")
    if "es_admin" not in st.session_state:
        st.session_state["es_admin"] = False

    productos_activos = obtener_todos_productos(solo_activos=True)
    todos_los_productos = obtener_todos_productos(solo_activos=False)
    datos = procesar_metricas_globales(productos_activos)

    # --- BARRA LATERAL ---
    with st.sidebar:
        if existe_logo:
            col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
            with col_l2:
                st.image(LOGO_PATH, width=130)

        st.markdown("<h2 style='text-align: center; margin-top: 5px; margin-bottom: 0px;'>BIOFOOD NUTRITION</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 0.85rem; margin-top: 2px;'>Sistema de Bodega y Distribución</p>", unsafe_allow_html=True)
        st.divider()

        # Selector de Modo de Visualización (Solo las dos opciones que funcionan excelente)
        st.markdown("### Visualización")
        contraste_activo = st.checkbox(
            "Modo Alto Contraste",
            value=st.session_state["alto_contraste"],
            help="Activa bordes reforzados y fondo negro puro para máxima legibilidad en bodega."
        )
        if contraste_activo != st.session_state["alto_contraste"]:
            st.session_state["alto_contraste"] = contraste_activo
            st.rerun()

        st.divider()

        st.markdown("### Acceso Administrador")
        if not st.session_state["es_admin"]:
            pin_input = st.text_input("PIN de seguridad:", type="password", max_chars=10, key="admin_pin_input")
            if st.button("Desbloquear Edición", use_container_width=True):
                if pin_input == ADMIN_PIN:
                    st.session_state["es_admin"] = True
                    st.toast("Modo Administrador activado.")
                    st.rerun()
                else:
                    st.error("PIN incorrecto.")
        else:
            st.success("Modo Administrador Activo")
            if st.button("Bloquear / Cerrar Sesión", use_container_width=True):
                st.session_state["es_admin"] = False
                st.toast("Sesión cerrada.")
                st.rerun()

        st.divider()

        if st.session_state["es_admin"]:
            st.markdown("**REGISTRAR NUEVO SUPLEMENTO**")
            
            categoria_sel = st.selectbox("1. Línea de Producto:", list(PRODUCTOS_BIOFOOD.keys()))
            sugerencias_cat = PRODUCTOS_BIOFOOD[categoria_sel]
            nombres_sugeridos = [item["nombre"] for item in sugerencias_cat] + ["Ingresar otro suplemento manual..."]
            
            sel_nombre = st.selectbox("2. Catálogo Sugerido:", nombres_sugeridos)
            
            if sel_nombre == "Ingresar otro suplemento manual...":
                nombre_final = st.text_input("Nombre comercial:", placeholder="Ej: Creatina Micronizada 300g").strip()
                unidad_default = "Frasco" if categoria_sel == "Cápsulas" else "Pote"
                venta_default = 19990
            else:
                nombre_final = sel_nombre
                match = next((item for item in sugerencias_cat if item["nombre"] == sel_nombre), None)
                unidad_default = match["unidad"] if match else "Pote"
                venta_default = match["venta"] if match else 0

            idx_unidad = OPCIONES_ENVASE.index(unidad_default) if unidad_default in OPCIONES_ENVASE else 0
            unidad_medida = st.selectbox("3. Formato Envase:", OPCIONES_ENVASE, index=idx_unidad)

            auto_sku = st.checkbox("Generar SKU automático", value=True)
            if auto_sku:
                sku_final = generar_sku_sugerido(categoria_sel)
                st.info(f"SKU sugerido: **{sku_final}**")
            else:
                sku_final = st.text_input("Código SKU:", placeholder="Ej: BF-CAPS-001").strip().upper()

            with st.form("form_registro_biofood", clear_on_submit=True):
                precio_venta = st.number_input("Precio Venta Público ($)", min_value=0, step=1000, value=venta_default)
                
                c_stock, c_min = st.columns(2)
                stock_actual = c_stock.number_input("Stock Inicial", min_value=0, step=1, value=12)
                stock_minimo = c_min.number_input("Stock Mínimo", min_value=0, step=1, value=3)

                btn_guardar = st.form_submit_button("Guardar en Inventario", use_container_width=True, type="primary")

                if btn_guardar:
                    if not nombre_final:
                        st.error("El nombre del producto es obligatorio.")
                    elif not sku_final:
                        st.error("El código SKU es obligatorio.")
                    else:
                        exito = registrar_producto(
                            sku_final, nombre_final, categoria_sel, unidad_medida,
                            0, int(precio_venta), int(stock_actual), int(stock_minimo)
                        )
                        if exito:
                            st.toast(f"'{nombre_final}' guardado con éxito.")
                            st.rerun()
                        else:
                            st.error("El código SKU o producto ya existe.")
        else:
            st.info("**Modo Consulta**\n\nCatálogo en modo lectura. Ingresa el PIN arriba para registrar o modificar productos.")

    inyectar_estilos(st.session_state["alto_contraste"])

    # --- CABECERA PRINCIPAL ---
    if existe_logo:
        col_hdr_logo, col_hdr_txt = st.columns([1, 8])
        with col_hdr_logo:
            st.image(LOGO_PATH, width=85)
        with col_hdr_txt:
            st.markdown("<h1 style='margin-bottom: 0px;'>Biofood Nutrition — Centro de Gestión de Stock</h1>", unsafe_allow_html=True)
            st.caption("Monitoreo en Tiempo Real · Almacén Central")
    else:
        st.markdown("# Biofood Nutrition — Centro de Gestión de Stock")
        st.caption("Monitoreo en Tiempo Real · Almacén Central")

    st.write("")

    # 1. Alerta Crítica
    if datos.get("productos_reposicion", 0) > 0:
        st.toast(f"Atención: {datos['productos_reposicion']} producto(s) en nivel crítico.")
        st.markdown(
            f"""
            <div class="critical-banner">
                ALERTA DE REPOSICIÓN: {datos['productos_reposicion']} suplemento(s) se encuentran bajo el stock mínimo de seguridad.
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Tarjetas de KPIs
    valor_total_venta = sum(p.get("stock_actual", 0) * p.get("precio_venta", 0) for p in productos_activos)

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
        st.markdown(
            f"""
            <div class="kpi-container">
                <div class="kpi-title">VALOR INVENTARIO (VENTA)</div>
                <div class="kpi-value kpi-val-money">${valor_total_venta:,}</div>
                <div class="kpi-subtext">valor comercial disponible</div>
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

    # 3. Detalle de Déficit
    if datos.get("productos_reposicion", 0) > 0:
        st.write("")
        with st.expander("Ver detalle de suplementos que requieren reposición", expanded=False):
            items_reposicion = [p for p in datos.get("catalogo", []) if p.get("estado") == "REPOSICIÓN"]
            lista_detalle = []
            for item in items_reposicion:
                st_act = item.get("stock_actual", 0)
                st_min = item.get("stock_minimo", 0)
                deficit = max(0, st_min - st_act)
                cat_limpia = MAPA_MIGRACION_CATEGORIAS.get(item.get("categoria"), item.get("categoria", ""))
                lista_detalle.append({
                    "SKU": item.get("sku", ""),
                    "SUPLEMENTO / PRODUCTO": item.get("nombre", ""),
                    "LÍNEA": cat_limpia,
                    "DISPONIBLE": f"{st_act} {item.get('unidad_medida', 'uds')}",
                    "STOCK MÍNIMO": f"{st_min} {item.get('unidad_medida', 'uds')}",
                    "DÉFICIT (A PEDIR)": f"+{deficit} {item.get('unidad_medida', 'uds')}"
                })
            if lista_detalle:
                st.dataframe(pd.DataFrame(lista_detalle), use_container_width=True, hide_index=True)

    st.write("")
    st.divider()

    # 4. Catálogo de Existencias (Edición en Tabla)
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown("### Catálogo de Suplementos y Existencias")
    with col_t2:
        st.caption(f"**{len(datos.get('catalogo', []))}** suplementos activos")

    if datos.get("catalogo"):
        df = pd.DataFrame(datos["catalogo"])
        df["categoria"] = df["categoria"].replace(MAPA_MIGRACION_CATEGORIAS)

        filtro_col1, filtro_col2 = st.columns([2, 2])
        with filtro_col1:
            busqueda = st.text_input("Buscar por suplemento o SKU:", placeholder="Ej: Whey, Creatina, BF-POLV-001").strip().lower()
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

        columnas_deseadas = ["sku", "nombre", "categoria", "unidad_medida", "precio_venta", "stock_actual", "stock_minimo", "estado"]
        columnas_presentes = [c for c in columnas_deseadas if c in df_filtrado.columns]
        
        df_vista = df_filtrado[columnas_presentes]
        nombres_cabecera = {
            "sku": "SKU", "nombre": "PRODUCTO", "categoria": "LÍNEA", 
            "unidad_medida": "ENVASE", "precio_venta": "VENTA ($)", 
            "stock_actual": "STOCK", "stock_minimo": "MÍNIMO", "estado": "ESTADO"
        }
        df_vista = df_vista.rename(columns=nombres_cabecera)

        if st.session_state["es_admin"]:
            st.caption("Modo Administrador: Puedes modificar Línea, Envase, Venta, Stock y Mínimo directamente en la tabla.")

            column_config = {
                "SKU": st.column_config.TextColumn("SKU", disabled=True),
                "PRODUCTO": st.column_config.TextColumn("PRODUCTO", disabled=True),
                "ESTADO": st.column_config.TextColumn("ESTADO", disabled=True),
                "LÍNEA": st.column_config.SelectboxColumn(
                    "LÍNEA",
                    options=list(PRODUCTOS_BIOFOOD.keys()),
                    required=True
                ),
                "ENVASE": st.column_config.SelectboxColumn(
                    "ENVASE",
                    options=OPCIONES_ENVASE,
                    required=True
                ),
                "VENTA ($)": st.column_config.NumberColumn(
                    "VENTA ($)",
                    min_value=0,
                    step=1000,
                    required=True
                ),
                "STOCK": st.column_config.NumberColumn(
                    "STOCK",
                    min_value=0,
                    step=1,
                    required=True
                ),
                "MÍNIMO": st.column_config.NumberColumn(
                    "MÍNIMO",
                    min_value=0,
                    step=1,
                    required=True
                )
            }

            df_editado = st.data_editor(
                df_vista,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
                disabled=["SKU", "PRODUCTO", "ESTADO"],
                key="editor_catalogo"
            )

            mapa_original = {
                row["SKU"]: (
                    str(row["LÍNEA"]),
                    str(row["ENVASE"]),
                    int(row["VENTA ($)"]),
                    int(row["STOCK"]),
                    int(row["MÍNIMO"])
                )
                for _, row in df_vista.iterrows()
            }

            cambios_detectados = []
            for _, row in df_editado.iterrows():
                sku_actual = row["SKU"]
                orig = mapa_original.get(sku_actual)
                if orig:
                    cat_edit = str(row["LÍNEA"])
                    env_edit = str(row["ENVASE"])
                    pre_edit = int(row["VENTA ($)"])
                    stk_edit = int(row["STOCK"])
                    min_edit = int(row["MÍNIMO"])
                    
                    if (cat_edit, env_edit, pre_edit, stk_edit, min_edit) != orig:
                        cambios_detectados.append({
                            "sku": sku_actual,
                            "categoria": cat_edit,
                            "unidad_medida": env_edit,
                            "precio_venta": pre_edit,
                            "stock_actual": stk_edit,
                            "stock_minimo": min_edit
                        })

            if cambios_detectados:
                if st.button(f"Guardar Cambios de la Tabla ({len(cambios_detectados)} suplementos modificados)", type="primary"):
                    errores = 0
                    for item in cambios_detectados:
                        if not actualizar_producto_desde_tabla(
                            item["sku"],
                            item["categoria"],
                            item["unidad_medida"],
                            item["precio_venta"],
                            item["stock_actual"],
                            item["stock_minimo"]
                        ):
                            errores += 1
                    if errores == 0:
                        st.toast("Cambios guardados correctamente en la base de datos.")
                        st.rerun()
                    else:
                        st.error("Hubo un error al sincronizar algunos cambios en Supabase.")
        else:
            st.dataframe(df_vista, use_container_width=True, hide_index=True)

        csv_data = df_vista.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Exportar Planilla de Inventario (CSV)",
            data=csv_data,
            file_name="inventario_biofood_nutrition.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay existencias registradas. Ingresa los primeros suplementos desde el panel izquierdo.")

    st.write("")

    # 5. Registro Transaccional
    with st.expander("Registrar Movimiento de Bodega (Venta / Recepción)", expanded=False):
        if not st.session_state["es_admin"]:
            st.info("Requiere permisos de administrador. Ingresa el PIN en la barra lateral para registrar movimientos.")
        elif productos_activos:
            opciones = {
                f"{p['sku']} — {p['nombre']} (Stock actual: {p['stock_actual']} {p.get('unidad_medida', '')})": p["id"]
                for p in productos_activos
            }
            
            prod_sel = st.selectbox("1. Seleccionar Suplemento:", list(opciones.keys()))

            c_tipo, c_cant, c_btn = st.columns([3, 2, 2])
            
            with c_tipo:
                tipo_display = st.radio(
                    "2. Operación:",
                    ["Salida (Venta)", "Entrada (Recepción)"],
                    horizontal=True
                )
                tipo = "SALIDA" if "Salida" in tipo_display else "ENTRADA"

            with c_cant:
                cant = st.number_input("3. Cantidad de envases:", min_value=1, step=1, value=1)

            with c_btn:
                st.write("")
                st.write("")
                if st.button("Confirmar Movimiento", use_container_width=True, type="primary"):
                    id_seleccionado = opciones[prod_sel]
                    if actualizar_stock_transaccional(id_seleccionado, tipo, int(cant)):
                        st.toast(f"Operación de {tipo} registrada.")
                        st.success(f"Movimiento de {tipo} registrado correctamente.")
                        st.rerun()
                    else:
                        st.error("Error: Salida rechazada por saldo insuficiente en bodega.")

    # 6. Modificar Stock Mínimo
    if st.session_state["es_admin"] and productos_activos:
        st.write("")
        with st.expander("Modificar Stock Mínimo / Seguridad (Solo Admin)"):
            c_prod_min, c_val_min, c_btn_min = st.columns([4, 2, 2])
            opciones_min = {
                f"{p['sku']} - {p['nombre']} (Mínimo actual: {p['stock_minimo']} {p.get('unidad_medida', '')})": p
                for p in productos_activos
            }
            item_elegido_str = c_prod_min.selectbox("Suplemento a modificar:", list(opciones_min.keys()), key="sb_minimo")
            item_datos = opciones_min[item_elegido_str]
            
            nuevo_valor_min = c_val_min.number_input(
                "Nuevo Mínimo:",
                min_value=0,
                step=1,
                value=int(item_datos["stock_minimo"]),
                key="num_input_min"
            )
            
            c_btn_min.write("")
            c_btn_min.write("")
            if c_btn_min.button("Actualizar Mínimo", use_container_width=True, type="primary"):
                if actualizar_stock_minimo(item_datos["id"], int(nuevo_valor_min)):
                    st.toast(f"Stock mínimo ajustado a {nuevo_valor_min}.")
                    st.rerun()
                else:
                    st.error("Error al actualizar en la base de datos.")

    # 7. Dar de Baja / Reactivar
    if st.session_state["es_admin"] and todos_los_productos:
        st.write("")
        with st.expander("Dar de Baja / Reactivar Suplemento (Solo Admin)"):
            st.caption("Dar de baja oculta el producto del catálogo y de la lista de ventas sin borrar su historial de transacciones.")
            col_sel, col_acc = st.columns([4, 2])
            
            opciones_estado = {
                f"{p['sku']} - {p['nombre']} [{'ACTIVO' if p.get('activo', True) else 'DADO DE BAJA'}]": p
                for p in todos_los_productos
            }
            prod_estado_str = col_sel.selectbox("Seleccionar Suplemento:", list(opciones_estado.keys()), key="sb_baja")
            prod_estado = opciones_estado[prod_estado_str]
            esta_activo = prod_estado.get("activo", True)

            col_acc.write("")
            col_acc.write("")
            if esta_activo:
                if col_acc.button("Dar de Baja", use_container_width=True):
                    if cambiar_estado_producto(prod_estado["id"], False):
                        st.toast(f"'{prod_estado['nombre']}' dado de baja.")
                        st.rerun()
                    else:
                        st.error("Error al cambiar estado.")
            else:
                if col_acc.button("Reactivar Suplemento", use_container_width=True, type="primary"):
                    if cambiar_estado_producto(prod_estado["id"], True):
                        st.toast(f"'{prod_estado['nombre']}' reactivado.")
                        st.rerun()
                    else:
                        st.error("Error al reactivar suplemento.")

    st.write("")

    # 8. Historial de Auditoría
    with st.expander("Historial de Auditoría de Movimientos (Últimas transacciones)"):
        movimientos = obtener_historial_movimientos()
        if movimientos:
            df_mov = pd.DataFrame(movimientos)
            
            fechas = pd.to_datetime(df_mov["fecha"])
            if fechas.dt.tz is None:
                fechas = fechas.dt.tz_localize("UTC")
            df_mov["fecha"] = fechas.dt.tz_convert("America/Santiago").dt.strftime("%d/%m/%Y %H:%M")
            
            df_mov["tipo"] = df_mov["tipo"].apply(
                lambda x: "ENTRADA" if x == "ENTRADA" else "SALIDA"
            )
            
            df_mov["cantidad_fmt"] = df_mov["cantidad"].astype(str) + " " + df_mov["unidad_medida"]
            
            df_mov_vista = df_mov[["fecha", "sku", "nombre", "tipo", "cantidad_fmt"]].rename(columns={
                "fecha": "FECHA / HORA",
                "sku": "SKU",
                "nombre": "PRODUCTO",
                "tipo": "OPERACIÓN",
                "cantidad_fmt": "CANTIDAD"
            })
            
            st.dataframe(df_mov_vista, use_container_width=True, hide_index=True)
            
            csv_mov = df_mov_vista.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar Reporte de Movimientos (CSV)",
                data=csv_mov,
                file_name="historial_movimientos_biofood.csv",
                mime="text/csv"
            )
        else:
            st.info("Aún no hay registros de movimientos en la base de datos.")

if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", "app.py"]
        sys.exit(stcli.main())