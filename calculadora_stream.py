# -*- coding: utf-8 -*-
"""
Versión Streamlit de la App de Gestión SELAH con catálogo de Pulseras
Autor: Arie Brito + GPT-5 (adaptado y corregido a Streamlit 2025)
"""

import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd

# =====================================
# Conexión a base de datos
# =====================================
def conectar_db():
    try:
        conexion = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets["DB_PORT"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            connect_timeout=10
        )
        if conexion.is_connected():
            st.session_state["db_ok"] = True
            return conexion
        else:
            st.session_state["db_ok"] = False
            st.error("❌ No se pudo establecer conexión con la base de datos.")
            return None
    except Error as e:
        st.session_state["db_ok"] = False
        st.error(f"⚠️ Error de conexión con la base de datos: {e}")
        return None


# =====================================
# Funciones auxiliares
# =====================================
def obtener_material_opciones_display():
    conexion = conectar_db()
    mapa = {" ": " "}
    opciones_display = [" "]

    if conexion is None:
        return opciones_display, mapa

    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT ID_MATERIAL, TIPO, PIEDRA, COLOR, DESCRIPCION FROM MATERIALES ORDER BY ID_MATERIAL")
        result = cursor.fetchall()

        for id_mat, tipo, piedra, color, desc in result:
            parts = []
            if tipo and tipo.strip(): parts.append(tipo)
            if piedra and piedra.strip(): parts.append(piedra)
            if color and color.strip(): parts.append(color)
            if desc and desc.strip(): parts.append(f"({desc})")

            display_string = f"{id_mat} | {' - '.join(parts)}"
            mapa[display_string] = id_mat
            opciones_display.append(display_string)

        return opciones_display, mapa
    except Error as e:
        st.error(f"Error al obtener catálogo de material: {e}")
        return [" "], {" ": " "}
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def obtener_costo_cuenta(id_material):
    if not id_material or id_material == " ":
        return 0.0
    conexion = conectar_db()
    if conexion is None:
        return 0.0
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT COSTO_CUENTA FROM MATERIALES WHERE ID_MATERIAL=%s", (id_material,))
        res = cursor.fetchone()
        return float(res[0]) if res and res[0] is not None else 0.0
    except Error:
        return 0.0
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def obtener_proveedores():
    conexion = conectar_db()
    if conexion is None:
        return []
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT ID_PROVEEDOR, NOMBRE_PROVEEDOR FROM PROVEEDORES")
        return cursor.fetchall()
    except Error as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


def obtener_catalogo_materiales():
    conexion = conectar_db()
    if conexion is None:
        return pd.DataFrame()
    try:
        query = """
        SELECT 
            M.ID_MATERIAL,
            M.TIPO,
            M.PIEDRA,
            M.FORMA,
            M.COLOR,
            M.DESCRIPCION,
            M.TEXTURA,
            M.LARGO,
            M.ANCHO,
            M.COSTO_TIRA,
            M.CANTIDAD,
            M.COSTO_CUENTA,
            P.NOMBRE_PROVEEDOR
        FROM MATERIALES M
        LEFT JOIN PROVEEDORES P ON M.ID_PROVEEDOR = P.ID_PROVEEDOR
        ORDER BY M.ID_MATERIAL
        """
        return pd.read_sql(query, conexion)
    except Error as e:
        st.error(f"Error al obtener catálogo: {e}")
        return pd.DataFrame()
    finally:
        if conexion.is_connected():
            conexion.close()


def obtener_catalogo_pulseras():
    conexion = conectar_db()
    if conexion is None:
        return pd.DataFrame()
    try:
        query = """
        SELECT 
            ID_PRODUCTO,
            DESCRIPCION,
            COSTO,
            PRECIO,
            CLASIFICACION,
            PRECIO_CLASIFICADO
        FROM PULSERAS
        ORDER BY ID_PRODUCTO
        """
        return pd.read_sql(query, conexion)
    except Error as e:
        st.error(f"Error al obtener catálogo de pulseras: {e}")
        return pd.DataFrame()
    finally:
        if conexion.is_connected():
            conexion.close()


# =====================================
# Inicialización de estado
# =====================================
def inicializar_calculadora_state():
    DEFAULT_SELECTBOX_VALUE = " "
    if 'hilo_calc' not in st.session_state:
        st.session_state['hilo_calc'] = DEFAULT_SELECTBOX_VALUE
    for i in range(5):
        st.session_state.setdefault(f"id_{i}", DEFAULT_SELECTBOX_VALUE)
        st.session_state.setdefault(f"cant_{i}", 0)


# =====================================
# Función para limpiar calculadora (Mantenida solo para evitar errores si se llama accidentalmente)
# =====================================
def limpiar_campos_calculadora():
    # Esta función se mantiene pero ya no es llamada por un botón
    DEFAULT_SELECTBOX_VALUE = " "
    st.session_state['hilo_calc'] = DEFAULT_SELECTBOX_VALUE
    for i in range(5):
        st.session_state[f"id_{i}"] = DEFAULT_SELECTBOX_VALUE
        st.session_state[f"cant_{i}"] = 0
    for key in ['costo_total', 'precio_real', 'clasificacion', 'precio_clasificado']:
        st.session_state.pop(key, None)
    st.rerun()  # ✅ reemplazo correcto de experimental_rerun


# =====================================
# INTERFAZ PRINCIPAL
# =====================================
inicializar_calculadora_state()
st.title("Selah: Sistema de Gestión")

tab1, tab2, tab3, tab4 = st.tabs([
    "🧾 Registro de Materiales",
    "💰 Calculadora de Pulseras",
    "📚 Catálogo de Materiales",
    "📿 Catálogo de Pulseras"
])

# =========================
# TAB 1: Registro de Materiales
# =========================
with tab1:
    st.subheader("🧾 Registro de Nuevos Materiales")
    with st.form("form_registro"):
        col1, col2 = st.columns(2)
        with col1:
            id_material = st.text_input("ID Producto", key="id_mat")
            tipo = st.selectbox("Tipo", [" ", "Corazon", "Cristal", "Goldstone", "Inicial", "Perla", "Piedra", "Separador", "Zirconia"])
            piedra = st.selectbox("Piedra", [" ", "Agata", "Apatita", "Aventurina", "Onix", "Turquesa", "Sodalita", "Otro"])
            forma = st.selectbox("Forma", [" ", "Redonda", "Gota", "Cruz", "Corazon", "Cilindro", "Otro"])
            color = st.text_input("Color")
            descripcion = st.text_input("Descripción")
        with col2:
            textura = st.selectbox("Textura", [" ", "Lisa", "Facetada"])
            largo = st.text_input("Largo")
            ancho = st.text_input("Ancho")
            costo_tira = st.text_input("Costo Tira")
            cantidad = st.text_input("Cantidad")
            proveedores = obtener_proveedores()
            opciones_prov = [" "] + [p[1] for p in proveedores]
            nombre_prov_sel = st.selectbox("Proveedor", opciones_prov)
            id_proveedor = None
            if nombre_prov_sel != " ":
                dict_proveedores = {p[1]: p[0] for p in proveedores}
                id_proveedor = dict_proveedores.get(nombre_prov_sel)

        # Se elimina el botón de Limpiar Campos. Solo queda el botón de Registrar.
        submitted = st.form_submit_button("Registrar Producto")

        if submitted:
            if not id_material:
                st.error("El ID no puede quedar vacío")
            elif id_proveedor is None:
                st.error("Debes seleccionar un proveedor válido.")
            else:
                conexion = conectar_db()
                if conexion:
                    cursor = conexion.cursor()
                    cursor.execute("SELECT COUNT(*) FROM MATERIALES WHERE ID_MATERIAL=%s", (id_material,))
                    if cursor.fetchone()[0] > 0:
                        st.error("El ID ya existe")
                    else:
                        try:
                            # Asegurar que los campos numéricos se manejen correctamente
                            costo_tira_f = float(costo_tira) if costo_tira else 0.0
                            cantidad_i = int(cantidad) if cantidad else 0
                            largo_f = float(largo) if largo else None
                            ancho_f = float(ancho) if ancho else None
                            costo_cuenta = costo_tira_f / cantidad_i if cantidad_i != 0 else 0

                            sql = """
                            INSERT INTO MATERIALES
                            (ID_MATERIAL, TIPO, PIEDRA, FORMA, COLOR, DESCRIPCION, TEXTURA, LARGO, ANCHO, COSTO_TIRA, CANTIDAD, COSTO_CUENTA, ID_PROVEEDOR)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            datos = (id_material, tipo, piedra, forma, color, descripcion, textura,
                                     largo_f, ancho_f, costo_tira_f, cantidad_i, costo_cuenta, id_proveedor)
                            cursor.execute(sql, datos)
                            conexion.commit()
                            st.success(f"✅ Producto registrado correctamente: {id_material}")
                        except ValueError:
                            st.error("Verifica que los campos numéricos sean correctos (Costo Tira, Largo, Ancho, Cantidad).")
                        except Error as e:
                            st.error(f"No se pudo registrar el producto: {e}")
                        finally:
                            cursor.close()
                            conexion.close()

# =========================
# TAB 2: Calculadora de Pulseras
# =========================
with tab2:
    st.subheader("💰 Calculadora de Pulseras")

    tipo_hilo = st.selectbox("Tipo de Hilo", [" ", "Nylon", "Negro"], key='hilo_calc')
    opciones_display, material_mapa = obtener_material_opciones_display()

    st.markdown("### Selección de Materiales (Máx. 5)")
    material_seleccionados, cantidades = [], []

    for i in range(5):
        col1, col2 = st.columns(2)
        with col1:
            mat_desc = st.selectbox(
                f"Material {i+1}",
                options=opciones_display,
                key=f"id_{i}"
            )
            mat_id = material_mapa.get(mat_desc, " ")
        with col2:
            cant = st.number_input(f"Cantidad {i+1}", min_value=0, value=st.session_state[f"cant_{i}"], step=1, key=f"cant_{i}")
        material_seleccionados.append(mat_id)
        cantidades.append(cant)

    # Se elimina el layout de columnas y el botón de Limpiar Campos de la calculadora.
    if st.button("Calcular Precio"):
        costo_total_cuentas = sum(
            cantidades[i] * obtener_costo_cuenta(material_seleccionados[i])
            for i in range(5)
            if material_seleccionados[i] != " "
        )
        costo_hilo = 2.4 if tipo_hilo == "Nylon" else 4.0 if tipo_hilo == "Negro" else 0.0
        costo_mano = 40.0
        costo_empaque = 10.0
        costos_fijos = costo_hilo + costo_mano + costo_empaque
        marketing = 0.15 * (costo_total_cuentas + costos_fijos)
        precio_real = (costo_total_cuentas + costos_fijos + marketing) * 1.30

        if precio_real <= 160:
            clasificacion, precio_clasificado = "C", 160.0
        elif precio_real <= 200:
            clasificacion, precio_clasificado = "B", 200.0
        else:
            clasificacion, precio_clasificado = "A", 250.0

        st.success(f"**Costo total:** ${costo_total_cuentas + costos_fijos:.2f}")
        st.write(f"**Precio real:** ${precio_real:.2f}")
        st.info(f"**Clasificación:** {clasificacion}, Precio Clasificado: ${precio_clasificado:.2f}")

        st.session_state.update({
            'costo_total': costo_total_cuentas + costos_fijos,
            'precio_real': precio_real,
            'clasificacion': clasificacion,
            'precio_clasificado': precio_clasificado
        })

    st.markdown("### Registro de Pulsera Final")
    id_producto = st.text_input("ID Producto Pulsera", key='id_producto_pulsera_input')
    descripcion_pulsera = st.text_input("Descripción Pulsera", key='descripcion_pulsera_input')

    # Se elimina el layout de columnas y el botón de Limpiar Formulario Pulsera.
    if st.button("Registrar Pulsera"):
        if not id_producto or not descripcion_pulsera:
            st.error("Debes ingresar ID y descripción del producto")
        elif 'costo_total' not in st.session_state:
            st.error("Primero debes calcular el precio")
        else:
            conexion = conectar_db()
            if conexion:
                cursor = conexion.cursor()
                try:
                    sql = """
                    INSERT INTO PULSERAS (ID_PRODUCTO, DESCRIPCION, COSTO, PRECIO, CLASIFICACION, PRECIO_CLASIFICADO)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    datos = (
                        id_producto,
                        descripcion_pulsera,
                        st.session_state['costo_total'],
                        st.session_state['precio_real'],
                        st.session_state['clasificacion'],
                        st.session_state['precio_clasificado']
                    )
                    cursor.execute(sql, datos)
                    conexion.commit()
                    st.success(f"Pulsera '{descripcion_pulsera}' registrada correctamente")
                except Error as e:
                    st.error(f"No se pudo registrar la pulsera: {e}")
                finally:
                    cursor.close()
                    conexion.close()


# =========================
# TAB 3: Catálogo de Materiales
# =========================
with tab3:
    st.subheader("📚 Catálogo de Materiales")
    if st.button("🔄 Cargar Catálogo"):
        df = obtener_catalogo_materiales()
        if df.empty:
            st.warning("No hay materiales registrados o ocurrió un error.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)


# =========================
# TAB 4: Catálogo de Pulseras
# =========================
with tab4:
    st.subheader("📿 Catálogo de Pulseras")
    if st.button("🔄 Cargar Catálogo de Pulseras"):
        df = obtener_catalogo_pulseras()
        if df.empty:
            st.warning("No hay pulseras registradas o ocurrió un error.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
