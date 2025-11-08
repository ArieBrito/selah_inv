# -*- coding: utf-8 -*-
"""
Versión Streamlit de la App de Gestión SELAH con catálogo de Pulseras
Autor: Arie Brito + Gemini + GPT-5 (adaptado a Streamlit)
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
        # Nota: `st.secrets` está siendo utilizado para la conexión a la base de datos
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

# La función anterior 'obtener_ids_material' ha sido reemplazada por esta,
# que ahora devuelve la lista de opciones descriptivas para el selectbox
# y un mapa para encontrar el ID_MATERIAL real.
def obtener_material_opciones_display():
    """Devuelve una tupla (lista_de_opciones_display, mapa_display_a_id)."""
    conexion = conectar_db()
    # Estado inicial: solo la opción vacía
    mapa = {" ": " "}
    opciones_display = [" "]

    if conexion is None:
        return opciones_display, mapa

    try:
        cursor = conexion.cursor()
        # Seleccionamos campos clave para la descripción del catálogo
        cursor.execute("SELECT ID_MATERIAL, TIPO, PIEDRA, COLOR, DESCRIPCION FROM MATERIALES ORDER BY ID_MATERIAL")
        result = cursor.fetchall()

        for id_mat, tipo, piedra, color, desc in result:
            # Construir la cadena descriptiva para el usuario
            parts = []
            if tipo and tipo.strip() and tipo.strip() != ' ': parts.append(tipo)
            if piedra and piedra.strip() and piedra.strip() != ' ': parts.append(piedra)
            if color and color.strip() and color.strip() != ' ': parts.append(color)
            if desc and desc.strip() and desc.strip() != ' ': parts.append(f"({desc})")
            
            # Formato de la cadena: ID | TIPO - PIEDRA - COLOR (DESCRIPCION)
            display_string = f"{id_mat} | {' - '.join(parts)}"
            
            # Mapear la cadena descriptiva al ID real
            mapa[display_string] = id_mat
            opciones_display.append(display_string)

        return opciones_display, mapa
        
    except Error as e:
        st.error(f"Error al obtener catálogo de material para display: {e}")
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
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COSTO_CUENTA FROM MATERIALES WHERE ID_MATERIAL=%s", (id_material,))
        res = cursor.fetchone()
        return float(res[0]) if res and res[0] is not None else 0.0
    except Error:
        return 0.0
    finally:
        cursor.close()
        # Verificar la conexión antes de cerrar para evitar errores
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()


def obtener_proveedores():
    conexion = conectar_db()
    if conexion is None:
        return []
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT ID_PROVEEDOR, NOMBRE_PROVEEDOR FROM PROVEEDORES")
        result = cursor.fetchall()
        return result
    except Error as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []
    finally:
        cursor.close()
        if 'conexion' in locals() and conexion.is_connected():
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
        df = pd.read_sql(query, conexion)
        return df
    except Error as e:
        st.error(f"Error al obtener catálogo: {e}")
        return pd.DataFrame()
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()


def obtener_catalogo_pulseras():
    """Devuelve un DataFrame con todas las pulseras registradas."""
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
        df = pd.read_sql(query, conexion)
        return df
    except Error as e:
        st.error(f"Error al obtener catálogo de pulseras: {e}")
        return pd.DataFrame()
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()


# =====================================
# Inicialización de estado para la Calculadora (NUEVO)
# =====================================
def inicializar_calculadora_state():
    """Asegura que todas las claves necesarias para la calculadora existan con valores por defecto."""
    DEFAULT_SELECTBOX_VALUE = " "

    if 'hilo_calc' not in st.session_state:
        st.session_state['hilo_calc'] = DEFAULT_SELECTBOX_VALUE

    for i in range(5):
        id_key = f"id_{i}"
        cant_key = f"cant_{i}"
        
        if id_key not in st.session_state:
            st.session_state[id_key] = DEFAULT_SELECTBOX_VALUE
            
        if cant_key not in st.session_state:
            st.session_state[cant_key] = 0


# =====================================
# Función para limpiar los campos de la calculadora (CORREGIDA)
# =====================================
def limpiar_campos_calculadora():
    # Valor por defecto de las selectboxes, que es la primera opción.
    DEFAULT_SELECTBOX_VALUE = " "

    # 1. Resetear el selectbox de Tipo de Hilo
    if 'hilo_calc' in st.session_state:
        st.session_state['hilo_calc'] = DEFAULT_SELECTBOX_VALUE
        
    # 2. Resetear los 5 pares de inputs de Material y Cantidad
    for i in range(5):
        id_key = f"id_{i}"
        cant_key = f"cant_{i}"
        
        # Resetear el selectbox de material a la opción vacía (" ")
        if id_key in st.session_state:
            st.session_state[id_key] = DEFAULT_SELECTBOX_VALUE

        # Resetear el number_input a 0 
        if cant_key in st.session_state:
            st.session_state[cant_key] = 0

    # 3. Limpiar los resultados de la última calculadora
    for key in ['costo_total', 'precio_real', 'clasificacion', 'precio_clasificado']:
         if key in st.session_state:
            del st.session_state[key]
            
    st.rerun()


# =====================================
# INTERFAZ PRINCIPAL
# =====================================

# Inicialización de estado al comienzo del script
inicializar_calculadora_state()

st.title("Selah: Sistema de Gestión")

tab1, tab2, tab3, tab4 = st.tabs([
    "🧾 Registro de Materiales", 
    "💰 Calculadora de Pulseras", 
    "📚 Catálogo de Materiales", 
    "📿 Catálogo de Pulseras"
])

# =========================
# TAB 1: Registro de Materiales (Sin cambios)
# =========================
with tab1:
    st.subheader("🧾 Registro de Nuevos Materiales")
    with st.form("form_registro"):
        col1, col2 = st.columns(2)
        with col1:
            id_material = st.text_input("ID Producto", key="id_mat")
            tipo = st.selectbox("Tipo", [" "] + ["Corazon","Cristal","Goldstone","Inicial","Perla","Piedra","Separador","Zirconia"], index=0)
            piedra = st.selectbox("Piedra", [" "] + ["Agata","Apatita","Aventurina","Onix","Turquesa","Sodalita","Otro"], index=0)
            forma = st.selectbox("Forma", [" "] + ["Redonda","Gota","Cruz","Corazon","Cilindro","Otro"], index=0)
            color = st.text_input("Color", key="color_mat")
            descripcion = st.text_input("Descripción", key="desc_mat")
        with col2:
            textura = st.selectbox("Textura", [" "] + ["Lisa","Facetada"], index=0)
            largo = st.text_input("Largo", key="largo_mat")
            ancho = st.text_input("Ancho", key="ancho_mat")
            costo_tira = st.text_input("Costo Tira", key="costotira_mat")
            cantidad = st.text_input("Cantidad", key="cantidad_mat")

            proveedores = obtener_proveedores()
            opciones_prov = [" "] + [p[1] for p in proveedores]
            nombre_prov_sel = st.selectbox("Proveedor", opciones_prov, index=0)
            id_proveedor = None
            if nombre_prov_sel != " ":
                dict_proveedores = {p[1]: p[0] for p in proveedores}
                id_proveedor = dict_proveedores.get(nombre_prov_sel)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("Registrar Producto")
        with col_btn2:
            limpiar = st.form_submit_button("🧹 Limpiar Campos")

        if limpiar:
            # Esta limpieza solo afecta a los campos de la pestaña de Registro de Materiales
            for key in list(st.session_state.keys()):
                if key.startswith(("id_mat", "color_mat", "desc_mat", "largo_mat", "ancho_mat", "costotira_mat", "cantidad_mat")):
                    st.session_state[key] = ""
            st.rerun()

        if submitted:
            if not id_material:
                st.error("El ID no puede quedar vacío")
            elif id_proveedor is None:
                st.error("Debes seleccionar un proveedor válido antes de registrar el producto.")
            else:
                conexion = conectar_db()
                if conexion:
                    cursor = conexion.cursor()
                    cursor.execute("SELECT COUNT(*) FROM MATERIALES WHERE ID_MATERIAL=%s", (id_material,))
                    if cursor.fetchone()[0] > 0:
                        st.error("El ID ya existe")
                    else:
                        try:
                            costo_tira_f = float(costo_tira)
                            cantidad_i = int(cantidad)
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
                            st.error("Verifica que los campos numéricos sean correctos")
                        except Error as e:
                            st.error(f"No se pudo registrar el producto: {e}")
                        finally:
                            cursor.close()
                            conexion.close()


# =========================
# TAB 2: Calculadora de Pulseras (MODIFICADA)
# =========================
with tab2:
    st.subheader("💰 Calculadora de Pulseras")
    # AÑADIR CLAVE para control de limpieza
    # Usa la clave y el valor de session_state para mantener el estado
    tipo_hilo = st.selectbox("Tipo de Hilo", [" "] + ["Nylon", "Negro"], index=0, key='hilo_calc')

    # OBTENER LAS OPCIONES DESCRIPTIVAS Y EL MAPA DE ID
    opciones_display, material_mapa = obtener_material_opciones_display()
    
    material_seleccionados = []
    cantidades = []

    st.markdown("### Selección de Materiales (Máx. 5)")
    for i in range(5):
        col1, col2 = st.columns(2)
        with col1:
            # Usar la clave y el valor de session_state para Material (id_i)
            mat_desc = st.selectbox(
                f"Material {i+1} (ID | Tipo - Piedra - Color (Desc))", 
                options=opciones_display, 
                key=f"id_{i}", 
                index=0
            )
            # Obtener el ID_MATERIAL real a partir del mapa
            mat_id = material_mapa.get(mat_desc, " ")
        with col2:
            # Usar la clave y el valor de session_state para Cantidad (cant_i)
            cant = st.number_input(f"Cantidad {i+1}", min_value=0, value=st.session_state[f"cant_{i}"], step=1, key=f"cant_{i}")
        
        # El ID a usar para la lógica de cálculo es mat_id
        material_seleccionados.append(mat_id)
        cantidades.append(cant)

    col_calc, col_clear = st.columns(2)
    with col_calc:
        if st.button("Calcular Precio"):
            costo_total_cuentas = sum([
                cantidades[i] * obtener_costo_cuenta(material_seleccionados[i])
                for i in range(5)
                if material_seleccionados[i] != " "
            ])
            
            # Lógica de costos (sin cambios)
            costo_hilo = 2.4 if tipo_hilo == "Nylon" else 4.0 if tipo_hilo == "Negro" else 0.0
            costo_mano = 40.0
            costo_empaque = 10.0
            costos_fijos = costo_hilo + costo_mano + costo_empaque
            marketing = 0.15 * (costo_total_cuentas + costos_fijos)
            precio_real = costo_total_cuentas + costos_fijos + marketing
            precio_real += 0.30 * precio_real

            # Lógica de clasificación (sin cambios)
            if precio_real <= 160:
                clasificacion = "C"
                precio_clasificado = 160.0
            elif precio_real <= 200:
                clasificacion = "B"
                precio_clasificado = 200.0
            else:
                clasificacion = "A"
                precio_clasificado = 250.0

            st.success(f"**Costo total:** ${costo_total_cuentas + costos_fijos:.2f}")
            st.write(f"**Precio real:** ${precio_real:.2f}")
            st.info(f"**Clasificación:** {clasificacion}, Precio Clasificado: ${precio_clasificado:.2f}")

            # Guardar resultados en session_state (sin cambios)
            st.session_state['costo_total'] = costo_total_cuentas + costos_fijos
            st.session_state['precio_real'] = precio_real
            st.session_state['clasificacion'] = clasificacion
            st.session_state['precio_clasificado'] = precio_clasificado

    with col_clear:
        # El botón de limpiar campos llama a la función corregida
        if st.button("🧹 Limpiar Campos"):
            limpiar_campos_calculadora()

    st.markdown("### Registro de Pulsera Final")
    # Asegurarse de que las keys de session_state para los inputs del registro de pulsera estén definidas para evitar errores al limpiar
    id_producto = st.text_input("ID Producto Pulsera", key='id_producto_pulsera_input')
    descripcion_pulsera = st.text_input("Descripción Pulsera", key='descripcion_pulsera_input')

    col_reg, col_limpiar = st.columns(2)
    with col_reg:
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
                        if 'conexion' in locals() and conexion.is_connected():
                            conexion.close()

    with col_limpiar:
        if st.button("🧹 Limpiar Formulario Pulsera"):
            # Limpiar los campos de registro de pulsera
            if 'id_producto_pulsera_input' in st.session_state:
                 st.session_state['id_producto_pulsera_input'] = ""
            if 'descripcion_pulsera_input' in st.session_state:
                 st.session_state['descripcion_pulsera_input'] = ""
            # No es necesario un st.rerun si solo se cambian los valores de session_state de los inputs
            # pero lo dejo para asegurar el comportamiento esperado.
            st.rerun()


# =========================
# TAB 3: Catálogo de Materiales (Sin cambios)
# =========================
with tab3:
    st.subheader("📚 Catálogo de Materiales")
    if st.button("🔄 Cargar Catálogo"):
        df = obtener_catalogo_materiales()
        if df.empty:
            st.warning("No hay materiales registrados o ocurrió un error.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                label="⬇️ Descargar catálogo en CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name="catalogo_materiales.csv",
                mime="text/csv"
            )


# =========================
# TAB 4: Catálogo de Pulseras (Sin cambios)
# =========================
with tab4:
    st.subheader("📿 Catálogo de Pulseras")
    if st.button("🔄 Cargar Catálogo de Pulseras"):
        df = obtener_catalogo_pulseras()
        if df.empty:
            st.warning("No hay pulseras registradas o ocurrió un error.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                label="⬇️ Descargar catálogo en CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name="catalogo_pulseras.csv",
                mime="text/csv"
            )
