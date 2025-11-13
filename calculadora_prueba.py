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
        query = "SELECT ID_MATERIAL, TIPO, PIEDRA, FORMA, TEXTURA, LARGO, ANCHO, COLOR, DESCRIPCION FROM MATERIALES ORDER BY ID_MATERIAL"
        cursor.execute(query)
        result = cursor.fetchall()

        # Desempaquetando 9 valores
        for id_mat, tipo, piedra, forma, textura, largo, ancho, color, desc in result:
            parts = []
            if tipo and str(tipo).strip(): parts.append(tipo)
            if piedra and str(piedra).strip(): parts.append(piedra)
            if forma and str(forma).strip(): parts.append(forma)
            if textura and str(textura).strip(): parts.append(textura)
            if largo is not None and str(largo).strip(): parts.append(f"L:{largo}")
            if ancho is not None and str(ancho).strip(): parts.append(f"A:{ancho}")
            if desc and str(desc).strip(): parts.append(f"({desc})")

            display_string = f"{id_mat} | {' - '.join(parts)}"
            mapa[display_string] = id_mat
            opciones_display.append(display_string)

        return opciones_display, mapa
    except Error as e:
        st.error(f"Error al obtener catálogo de material: {e}")
        return [" "], {" ": " "}
    finally:
        try:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
        except Exception:
            pass


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
        try:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
        except Exception:
            pass


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
        try:
            if conexion.is_connected():
                cursor.close()
                conexion.close()
        except Exception:
            pass


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
        try:
            if conexion.is_connected():
                conexion.close()
        except Exception:
            pass


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
        try:
            if conexion.is_connected():
                conexion.close()
        except Exception:
            pass


# =====================================
# Inicialización de estado (IMPORTANTE)
# =====================================
def init_session_state():
    keys_defaults = {
        # TAB1 formulario
        "id_mat": "",
        "tipo_select": " ",
        "tipo_input": "",
        "piedra_select": " ",
        "piedra_input": "",
        "forma_select": " ",
        "forma_input": "",
        "color": "",
        "descripcion": "",
        "textura_sel": " ",
        "textura_input": "",
        "largo": "",
        "ancho": "",
        "costo_tira": "",
        "cantidad": "",
        # proveedor select uses key "Proveedor"
        "Proveedor": " ",
        # TAB2 calculadora
        "hilo_calc": " ",
        "id_0": " ",
        "id_1": " ",
        "id_2": " ",
        "id_3": " ",
        "id_4": " ",
        "cant_0": 0,
        "cant_1": 0,
        "cant_2": 0,
        "cant_3": 0,
        "cant_4": 0,
        # registro pulsera
        "id_producto_pulsera_input": "",
        "descripcion_pulsera_input": "",
        # resultados cálculo (pueden no existir hasta calcular)
        "costo_total": None,
        "precio_real": None,
        "clasificacion": None,
        "precio_clasificado": None,
        # DB status
        "db_ok": False
    }
    for k, v in keys_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session_state()


# =====================================
# Helper: limpiar funciones
# =====================================
def limpiar_form_registro():
    # reasignar valores para los keys del formulario
    st.session_state["id_mat"] = ""
    st.session_state["tipo_select"] = " "
    st.session_state["tipo_input"] = ""
    st.session_state["piedra_select"] = " "
    st.session_state["piedra_input"] = ""
    st.session_state["forma_select"] = " "
    st.session_state["forma_input"] = ""
    st.session_state["color"] = ""
    st.session_state["descripcion"] = ""
    st.session_state["textura_sel"] = " "
    st.session_state["textura_input"] = ""
    st.session_state["largo"] = ""
    st.session_state["ancho"] = ""
    st.session_state["costo_tira"] = ""
    st.session_state["cantidad"] = ""
    st.session_state["Proveedor"] = " "
    # no se eliminan claves, solo reseteamos valores existentes
    # limpiar también posibles mensajes de cálculo
    st.session_state.pop('costo_total', None)
    st.session_state.pop('precio_real', None)
    st.session_state.pop('clasificacion', None)
    st.session_state.pop('precio_clasificado', None)


def limpiar_calculadora_materiales():
    st.session_state['hilo_calc'] = " "
    for i in range(5):
        st.session_state[f"id_{i}"] = " "
        st.session_state[f"cant_{i}"] = 0


def limpiar_registro_pulsera():
    st.session_state['id_producto_pulsera_input'] = ""
    st.session_state['descripcion_pulsera_input'] = ""
    st.session_state.pop('costo_total', None)
    st.session_state.pop('precio_real', None)
    st.session_state.pop('clasificacion', None)
    st.session_state.pop('precio_clasificado', None)


# =====================================
# INTERFAZ PRINCIPAL
# =====================================
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

        # --------- COLUMNA 1 ---------
        with col1:
            id_material = st.text_input("ID Producto", key="id_mat")

            # --- TIPO ---
            tipo_opciones = [" ", "Natural", "Sintético", "Plástico", "Metal"]
            tipo_seleccion = st.selectbox("Tipo", tipo_opciones, key="tipo_select")
            tipo_input = st.text_input("Escribir Tipo (opcional)", key="tipo_input")
            tipo_final = tipo_input.strip() if tipo_input.strip() else tipo_seleccion

            # --- PIEDRA ---
            piedra_opciones = [" ", "Cuarzo", "Turquesa", "Obsidiana"]
            piedra_seleccion = st.selectbox("Piedra", piedra_opciones, key="piedra_select")
            piedra_input = st.text_input("Escribir Piedra (opcional)", key="piedra_input")
            piedra_final = piedra_input.strip() if piedra_input.strip() else piedra_seleccion

            # --- FORMA ---
            forma_opciones = [" ", "Redonda", "Cuadrada", "Facetada"]
            forma_seleccion = st.selectbox("Forma", forma_opciones, key="forma_select")
            forma_input = st.text_input("Escribir Forma (opcional)", key="forma_input")
            forma_final = forma_input.strip() if forma_input.strip() else forma_seleccion

            color = st.text_input("Color", key="color")
            descripcion = st.text_input("Descripción", key="descripcion")


        # --------- COLUMNA 2 ---------
        with col2:
            # --- TEXTURA ---
            textura_options = [" ", "Lisa", "Facetada", "Otro"]
            textura_sel = st.selectbox("Textura", textura_options, key="textura_sel")
            textura = st.text_input("Escribir Textura (opcional)", key="textura_input") if textura_sel == "Otro" else textura_sel

            largo = st.text_input("Largo", key="largo")
            ancho = st.text_input("Ancho", key="ancho")
            costo_tira = st.text_input("Costo Tira", key="costo_tira")
            cantidad = st.text_input("Cantidad", key="cantidad")

            proveedores = obtener_proveedores()
            opciones_prov = [" "] + [p[1] for p in proveedores]
            nombre_prov_sel = st.selectbox("Proveedor", opciones_prov, key="Proveedor")
            id_proveedor = {p[1]: p[0] for p in proveedores}.get(nombre_prov_sel) if nombre_prov_sel != " " else None

        # botones (Registrar y Borrar)
        submitted = st.form_submit_button("Registrar Producto")
        borrar = st.form_submit_button("🧹 Borrar Todo")

        if borrar:
            limpiar_form_registro()
            st.experimental_rerun()

        # --------- VALIDACIONES ---------
        if submitted:
            if not id_material or not str(id_material).strip():
                st.error("El ID no puede quedar vacío.")
            elif not tipo_final or not str(tipo_final).strip():
                st.error("El campo Tipo no puede quedar vacío.")
            elif not piedra_final or not str(piedra_final).strip():
                st.error("El campo Piedra no puede quedar vacío.")
            elif not forma_final or not str(forma_final).strip():
                st.error("El campo Forma no puede quedar vacío.")
            elif id_proveedor is None:
                st.error("Debes seleccionar un proveedor válido.")
            else:
                conexion = conectar_db()
                if conexion:
                    cursor = conexion.cursor()
                    cursor.execute("SELECT COUNT(*) FROM MATERIALES WHERE ID_MATERIAL=%s", (id_material,))
                    if cursor.fetchone()[0] > 0:
                        st.error("El ID ya existe.")
                    else:
                        try:
                            costo_tira_f = float(costo_tira) if str(costo_tira).strip() else 0.0
                            cantidad_i = int(cantidad) if str(cantidad).strip() else 0
                            largo_f = float(largo) if str(largo).strip() else None
                            ancho_f = float(ancho) if str(ancho).strip() else None
                            costo_cuenta = costo_tira_f / cantidad_i if cantidad_i else 0

                            sql = """
                            INSERT INTO MATERIALES
                            (ID_MATERIAL, TIPO, PIEDRA, FORMA, COLOR, DESCRIPCION,
                             TEXTURA, LARGO, ANCHO, COSTO_TIRA, CANTIDAD,
                             COSTO_CUENTA, ID_PROVEEDOR)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                            datos = (
                                id_material, tipo_final, piedra_final, forma_final, color,
                                descripcion, textura, largo_f, ancho_f,
                                costo_tira_f, cantidad_i, costo_cuenta, id_proveedor
                            )

                            cursor.execute(sql, datos)
                            conexion.commit()
                            st.success(f"Producto registrado correctamente: {id_material}")
                            # opcional: limpiar_form_registro() al registrar
                        except ValueError:
                            st.error("Verifica los campos numéricos (Costo Tira, Cantidad, Largo, Ancho).")
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
            cant = st.number_input(f"Cantidad {i+1}", min_value=0, value=st.session_state.get(f"cant_{i}", 0), step=1, key=f"cant_{i}")
        material_seleccionados.append(mat_id)
        cantidades.append(cant)

    # botón para limpiar selección de materiales
    col_clear1, col_clear2 = st.columns([1, 3])
    with col_clear1:
        if st.button("🧹 Limpiar Selección de Materiales"):
            limpiar_calculadora_materiales()
            st.experimental_rerun()

    # calcular precio
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

    # botón para limpiar formulario de pulsera
    colp1, colp2 = st.columns([1, 3])
    with colp1:
        if st.button("🧹 Borrar Formulario de Pulsera"):
            limpiar_registro_pulsera()
            st.experimental_rerun()

    if st.button("Registrar Pulsera"):
        if not id_producto or not descripcion_pulsera:
            st.error("Debes ingresar ID y descripción del producto")
        elif 'costo_total' not in st.session_state or st.session_state.get('costo_total') is None:
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
                    # opcional: limpiar_registro_pulsera()
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
