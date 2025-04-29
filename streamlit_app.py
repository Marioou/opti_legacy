# streamlit_app.py

import os
import json
import pandas as pd
import streamlit as st
import tempfile
from fpdf import FPDF

from optimizador.models import PiezaInventario, PiezaModelo, ModeloMueble
from optimizador.logic import optimizar_por_color

from optimizador.logic_opti5 import simulated_annealing_optimize
from optimizador.logic import optimizar_por_color

# ── Paths de datos ───────────────────────────────────────────────────
DATA_DIR = "data"
INV_FILE = os.path.join(DATA_DIR, "inventario.json")
MOD_FILE = os.path.join(DATA_DIR, "modelos.json")

# ── Funciones de persistencia ────────────────────────────────────────
def leer_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── Estado inicial ───────────────────────────────────────────────────
if 'inventario' not in st.session_state:
    st.session_state['inventario'] = leer_json(INV_FILE)
if 'modelos' not in st.session_state:
    st.session_state['modelos'] = leer_json(MOD_FILE)
if 'pieza_buffer' not in st.session_state:
    st.session_state['pieza_buffer'] = []

# ── Configuración de página ──────────────────────────────────────────
st.set_page_config(
    page_title="🛠️ Optimizador de Desperdicios",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("🛠️ Optimizador de Desperdicios")

# ── Menú lateral ─────────────────────────────────────────────────────
módulo = st.sidebar.radio(
    "🔀 Selecciona módulo",
    ("Sobrantes", "Modelos", "Optimización")
)

# ── Módulo “Sobrantes” ────────────────────────────────────────────────
if módulo == "Sobrantes":
    st.header("📥 Agregar Sobrantes")
    with st.form("form_sobrantes", clear_on_submit=True):
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            codigo = st.text_input("Código")
        with c2:
            ancho = st.number_input("Ancho (mm)", min_value=0.0)
        with c3:
            largo = st.number_input("Largo (mm)", min_value=0.0)
        with c4:
            color = st.text_input("Color")
        with c5:
            espesor = st.number_input("Espesor (mm)", min_value=0.0)
        with c6:
            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        guardar = st.form_submit_button("💾 Guardar pieza")
    if guardar:
        nueva = dict(
            codigo=codigo,
            ancho=ancho,
            largo=largo,
            color=color,
            espesor=espesor,
            cantidad=cantidad
        )
        st.session_state['inventario'].append(nueva)
        guardar_json(INV_FILE, st.session_state['inventario'])
        st.success(f"Pieza '{codigo}' agregada.")

    st.markdown("---")
    st.subheader("📤 Subir inventario desde Excel")

    archivo_excel = st.file_uploader("Carga un archivo Excel (.xlsx)", type=["xlsx"])

    if archivo_excel:
        try:
            df_excel = pd.read_excel(archivo_excel)

            # Verificación de columnas mínimas necesarias
            columnas_requeridas = ["codigo", "ancho", "largo", "color", "espesor", "cantidad"]
            
            if not set(columnas_requeridas).issubset(df_excel.columns.str.lower()):
                st.error(f"El archivo debe contener las columnas: {', '.join(columnas_requeridas)}")
            
            else:
            # Normalizar nombres
                df_excel.columns = df_excel.columns.str.lower()

            # Convertir a dicts y añadir
            nuevas_piezas = df_excel[columnas_requeridas].to_dict(orient="records")
            st.session_state['inventario'].extend(nuevas_piezas)
            guardar_json(INV_FILE, st.session_state['inventario'])
            st.success(f"Inventario cargado correctamente: {len(nuevas_piezas)} piezas añadidas.")
        
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
      
    st.markdown("---")
    st.subheader("📦 Inventario de Sobrantes")

    df_inv = pd.DataFrame(st.session_state['inventario'])

    if not df_inv.empty:
        df_inv["Eliminar"] = False  # Nueva columna tipo checkbox

    edited_df = st.data_editor(
        df_inv,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_inventario",
        hide_index=True
    )

    # Detectar qué filas se marcaron para eliminar
    to_delete = edited_df[edited_df["Eliminar"]].index.tolist()

    if to_delete:
        st.warning(f"{len(to_delete)} piezas marcadas para eliminar.")
        if st.button("🗑️ Quitar las piezas seleccionadas"):
            for idx in sorted(to_delete, reverse=True):
                st.session_state['inventario'].pop(idx)
            guardar_json(INV_FILE, st.session_state['inventario'])
            st.success("Piezas eliminadas correctamente.")
            st.experimental_rerun()
    else:
        st.info("No hay piezas en el inventario aún.")



# ── Módulo “Modelos” ─────────────────────────────────────────────────
elif módulo == "Modelos":
    st.header("📋 Definir Modelos de Muebles")
    with st.form("form_pieza_modelo", clear_on_submit=True):
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            codigo_req = st.text_input("Código pieza")
        with c2:
            ancho_req = st.number_input("Ancho (mm)", min_value=0.0)
        with c3:
            largo_req = st.number_input("Largo (mm)", min_value=0.0)
        with c4:
            espesor_req = st.number_input("Espesor (mm)", min_value=0.0)
        with c5:
            cantidad_req = st.number_input("Cantidad", min_value=1, value=1, step=1)
        add_pz = st.form_submit_button("➕ Agregar pieza")
    if add_pz:
        pieza = dict(
            codigo=codigo_req,
            ancho=ancho_req,
            largo=largo_req,
            espesor=espesor_req,
            cantidad=cantidad_req
        )
        st.session_state['pieza_buffer'].append(pieza)

    st.subheader("📦 Piezas en buffer del modelo")
    df_buf = pd.DataFrame(st.session_state['pieza_buffer'])
    if not df_buf.empty:
        df_buf['Eliminar'] = False
        edited_buf = st.data_editor(df_buf, num_rows="dynamic", use_container_width=True)
        to_del_buf = edited_buf.index[edited_buf['Eliminar']].tolist()
        if to_del_buf and st.button("🗑️ Eliminar del buffer"):
            for idx in sorted(to_del_buf, reverse=True):
                st.session_state['pieza_buffer'].pop(idx)
            st.experimental_rerun()
    else:
        st.info("El buffer está vacío. Agrega piezas arriba.")

    st.markdown("---")
    with st.form("form_modelo", clear_on_submit=True):
        id_mod = st.number_input(
            "ID del modelo", min_value=1,
            value=len(st.session_state['modelos']) + 1, step=1
        )
        nombre_mod = st.text_input("Nombre del modelo")
        save_mod = st.form_submit_button("✅ Guardar modelo")
    if save_mod:
        modelo = dict(
            id=id_mod,
            nombre=nombre_mod,
            piezas=st.session_state['pieza_buffer'].copy()
        )
        st.session_state['modelos'].append(modelo)
        st.session_state['pieza_buffer'].clear()
        guardar_json(MOD_FILE, st.session_state['modelos'])
        st.success(f"Modelo '{nombre_mod}' guardado.")

    st.subheader("🗂️ Modelos disponibles")
    df_mods = pd.DataFrame(st.session_state['modelos'])
    if not df_mods.empty:
        df_mods['Eliminar'] = False
        edited_mod = st.data_editor(df_mods, num_rows="dynamic", use_container_width=True)
        to_del_mod = edited_mod.index[edited_mod['Eliminar']].tolist()
        if to_del_mod and st.button("🗑️ Eliminar modelos"):
            for idx in sorted(to_del_mod, reverse=True):
                st.session_state['modelos'].pop(idx)
            guardar_json(MOD_FILE, st.session_state['modelos'])
            st.experimental_rerun()
    else:
        st.info("No hay modelos definidos aún.")

# ── Módulo “Optimización” ─────────────────────────────────────────────
elif módulo == "Optimización":
    st.header("🔎 Ejecutar Optimización")
    inv_objs = [PiezaInventario(**p) for p in st.session_state['inventario']]
    nombres = [m["nombre"] for m in st.session_state['modelos']]

    if not nombres:
        st.warning("Define primero algún modelo.")
        st.stop()

    modelo_sel = st.selectbox("Selecciona modelo", nombres)
    cantidad = st.number_input("Cantidad deseada", min_value=1, value=1, step=1)

    modelo_dict = {m["nombre"]: m for m in st.session_state['modelos']}
    modelo_data = modelo_dict.get(modelo_sel)
    modelo_obj = ModeloMueble(
        id=modelo_data["id"],
        nombre=modelo_data["nombre"],
        piezas=[PiezaModelo(**pz) for pz in modelo_data["piezas"]]
    )

    motor = st.radio("Selecciona motor de optimización", ["Clásico", "Simulated Annealing (Opti 5.0)"])

    if st.button("🛠️ Optimizar"):
        resultados = optimizar_por_color(modelo_obj, inv_objs, cantidad)
        st.session_state["resultados_optimizados"] = resultados

    if "resultados_optimizados" in st.session_state:
        resultados = st.session_state["resultados_optimizados"]

        piezas_lista = []
        for res in resultados:
            for lote in res["piezasUtilizadas"]:
                for pieza in lote:
                        piezas_lista.append({
                            "Código tablero": pieza["codigo"],
                            "Color": pieza["color"],
                            "Ancho (mm)": pieza["ancho"],
                            "Largo (mm)": pieza["largo"],
                            "Espesor (mm)": pieza["espesor"],
                            "Cantidad requerida": pieza["cantidad_req"],
                            "Pieza del modelo": pieza["pieza_modelo_codigo"],
                    })


        if piezas_lista:
            df_export = pd.DataFrame(piezas_lista)

            st.subheader("📋 Resumen de piezas optimizadas")
            st.dataframe(df_export, use_container_width=True)
            
            # PDF Export
        from fpdf import FPDF
        import tempfile
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt="Listado de piezas optimizadas", ln=True, align="C")
        pdf.ln(10)

        for col in df_export.columns:
            pdf.cell(30, 8, col, border=1)
        pdf.ln()
        for _, row in df_export.iterrows():
            for item in row:
                pdf.cell(30, 8, str(item), border=1)
            pdf.ln()

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp_file.name)

        with open(tmp_file.name, "rb") as f:
            st.download_button(
                label="📥 Descargar PDF de piezas optimizadas",
                data=f,
                file_name="optimizado_piezas.pdf",
                mime="application/pdf"
            )
    else:
        st.info("No se encontraron piezas fabricables para exportar.")
