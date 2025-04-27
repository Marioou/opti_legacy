#Streamlit app for the waste optimizer

import os
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from optimizador.models import PiezaInventario, PiezaModelo, ModeloMueble
from optimizador.logic import optimizar_por_color

# ── Paths de datos ───────────────────────────────────────────────────
DATA_DIR = "data"
INV_FILE  = os.path.join(DATA_DIR, "inventario.json")
MOD_FILE  = os.path.join(DATA_DIR, "modelos.json")

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
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1:
            codigo = st.text_input("Código")
        with c2:
            ancho  = st.number_input("Ancho (mm)", min_value=0.0)
        with c3:
            largo  = st.number_input("Largo (mm)", min_value=0.0)
        with c4:
            color  = st.text_input("Color")
        with c5:
            espesor= st.number_input("Espesor (mm)", min_value=0.0)
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
    st.subheader("📦 Inventario de Sobrantes")
    df_inv = pd.DataFrame(st.session_state['inventario'])
    if not df_inv.empty:
        df_inv['Eliminar'] = False
        edited = st.data_editor(
            df_inv,
            num_rows="dynamic",
            use_container_width=True
        )
        to_delete = edited.index[edited['Eliminar']].tolist()
        if to_delete and st.button("🗑️ Eliminar seleccionadas"):
            for idx in sorted(to_delete, reverse=True):
                st.session_state['inventario'].pop(idx)
            guardar_json(INV_FILE, st.session_state['inventario'])
            st.success("Piezas eliminadas correctamente.")
    else:
        st.info("No hay piezas en el inventario aún.")

# ── Módulo “Modelos” ─────────────────────────────────────────────────
elif módulo == "Modelos":
    st.header("📋 Definir Modelos de Muebles")
    # Formulario de piezas del modelo (sin Color)
    with st.form("form_pieza_modelo", clear_on_submit=True):
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1:
            codigo_req = st.text_input("Código pieza")
        with c2:
            ancho_req  = st.number_input("Ancho (mm)", min_value=0.0)
        with c3:
            largo_req  = st.number_input("Largo (mm)", min_value=0.0)
        with c4:
            espesor_req= st.number_input("Espesor (mm)", min_value=0.0)
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
        edited_buf = st.data_editor(
            df_buf,
            num_rows="dynamic",
            use_container_width=True
        )
        to_del_buf = edited_buf.index[edited_buf['Eliminar']].tolist()
        if to_del_buf and st.button("🗑️ Eliminar del buffer"):
            for idx in sorted(to_del_buf, reverse=True):
                st.session_state['pieza_buffer'].pop(idx)
            st.success("Piezas eliminadas del buffer.")
    else:
        st.info("El buffer está vacío. Agrega piezas arriba.")

    st.markdown("---")
    # Guardar modelo completo
    with st.form("form_modelo", clear_on_submit=True):
        id_mod = st.number_input(
            "ID del modelo",
            min_value=1,
            value=len(st.session_state['modelos'])+1,
            step=1
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

    st.markdown("---")
    st.subheader("🗂️ Modelos disponibles")
    df_mods = pd.DataFrame(st.session_state['modelos'])
    if not df_mods.empty:
        df_mods['Eliminar'] = False
        edited_mod = st.data_editor(
            df_mods,
            num_rows="dynamic",
            use_container_width=True
        )
        to_del_mod = edited_mod.index[edited_mod['Eliminar']].tolist()
        if to_del_mod and st.button("🗑️ Eliminar modelos"):
            for idx in sorted(to_del_mod, reverse=True):
                st.session_state['modelos'].pop(idx)
            guardar_json(MOD_FILE, st.session_state['modelos'])
            st.success("Modelos eliminados correctamente.")
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

    if st.button("🛠️ Optimizar"):
        resultados = optimizar_por_color(modelo_obj, inv_objs, cantidad)
        for res in resultados:
            st.subheader(f"🎨 Color: {res['color']}")
            st.write(f"Fabricables: {res['cantidadFabricable']} / {res['cantidadSolicitada']}")
            flat = [item for lote in res["piezasUtilizadas"] for item in lote]
            if flat:
                st.dataframe(pd.DataFrame(flat), use_container_width=True)
            else:
                st.write("No hay piezas válidas para este color.")        

# Guardar datos de eficiencia
efficiency_data = []

for res in resultados:
    area_piezas = 0
    area_tableros = 0

    for lote in res["piezasUtilizadas"]:
        for pieza in lote:
            area_piezas += pieza["cantidad_req"] * pieza["largo"] * pieza["ancho"]
            area_tableros += pieza["tableros_usados"] * pieza["largo"] * pieza["ancho"]

    eficiencia = (area_piezas / area_tableros) * 100 if area_tableros else 0
    efficiency_data.append({
        "color": res["color"],
        "eficiencia": eficiencia
    })

# Plot gráfico de eficiencia
if efficiency_data:
    df_eff = pd.DataFrame(efficiency_data)
    fig, ax = plt.subplots()
    ax.bar(df_eff["color"], df_eff["eficiencia"])
    ax.set_ylabel("Aprovechamiento (%)")
    ax.set_xlabel("Color")
    ax.set_title("Eficiencia de Aprovechamiento por Color")
    ax.set_ylim(0, 100)
    st.pyplot(fig)

