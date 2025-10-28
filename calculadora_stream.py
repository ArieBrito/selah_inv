"""
Versión Streamlit de la App de Gestión SELAH
Autor: Arie Brito + Gemini (adaptado a Streamlit)
"""

import streamlit as st
import mysql.connector
from mysql.connector import Error

@st.cache_resource
def conectar_db():
    try:
        conexion = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets["DB_PORT"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            connect_timeout=10  # evita cuelgues
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


def obtener_ids_material():
    conexion = conectar_db()
    if conexion is None:
        return []
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT ID_MATERIAL FROM MATERIAL")
        result = cursor.fetchall()
        return [r[0] for r in result]
    except Error:
        return []
    finally:
        cursor.close()
        conexion.close()

def obtener_costo_cuenta(id_material):
    if not id_material:
        return 0.0
    conexion = conectar_db()
    if conexion is None:
        return 0.0
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COSTO_CUENTA FROM MATERIAL WHERE ID_MATERIAL=%s", (id_material,))
        res = cursor.fetchone()
        return float(res[0]) if res and res[0] is not None else 0.0
    except Error:
        return 0.0
    finally:
        cursor.close()
        conexion.close()

# =========================
# Registro de Materiales
# =========================
st.title("📦 Registro de Materiales")

with st.form("form_registro"):
    col1, col2 = st.columns(2)

    with col1:
        id_material = st.text_input("ID Producto")
        tipo = st.selectbox("Tipo", ["Corazon","Cristal","Goldstone","Inicial","Perla","Piedra","Separador","Zirconia"])
        piedra = st.selectbox("Piedra", ["Agata","Aguamarina","Amazonita","Angelita","Apatita","Aventurina","Calcita","Coral","cristal","croazón nácar","goldfilled","granate","hematita","jade","jade teñido","lepidolita","madera","madre perla","mezzaluna","minerales","morganita","nacar","obsidiana","ojo de tigre","onix","opalo","ovalo dorado","perla","perla de rio","perla mallorca","piedras duras","piedras preciosas","selenita","sodalita","turmalina","turquesa","venturina","zirconia","Rubí Zafiro","Corindon","Piedra de Luna Azul","Coral","otro"])
        forma = st.selectbox("Forma", ["redonda","disco","gota","rectangular","cuadrada","satélite","rondel","rombo","swarovzky","rondela","cubo", "tubo","cruz","flor","ovalo","nugget","papa","luneta","irregular","corazon","esfera","dona","cilindro","redondo","otro"])
        color = st.text_input("Color")
        descripcion = st.text_input("Descripción")

    with col2:
        textura = st.selectbox("Textura", ["lisa","facetada"])
        largo = st.text_input("Largo")
        ancho = st.text_input("Ancho")
        costo_tira = st.text_input("Costo Tira")
        cantidad = st.text_input("Cantidad")
        proveedor = st.selectbox("Proveedor", ["MUNDO JOYA","KARATI","COLORE","LUNA IRIS"])

    submitted = st.form_submit_button("Registrar Producto")
    if submitted:
        if not id_material:
            st.error("El ID no puede quedar vacío")
        else:
            conexion = conectar_db()
            if conexion:
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM MATERIAL WHERE ID_MATERIAL=%s", (id_material,))
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
                        INSERT INTO MATERIAL
                        (ID_MATERIAL, TIPO, PIEDRA, FORMA, COLOR, DESCRIPCION, TEXTURA, LARGO, ANCHO, COSTO_TIRA, CANTIDAD, COSTO_CUENTA, PROVEEDOR)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        datos = (id_material, tipo, piedra, forma, color, descripcion, textura, largo_f, ancho_f, costo_tira_f, cantidad_i, costo_cuenta, proveedor)
                        cursor.execute(sql, datos)
                        conexion.commit()
                        st.success(f"Producto registrado correctamente: {id_material}")
                    except ValueError:
                        st.error("Verifica que los campos numéricos sean correctos")
                    except Error as e:
                        st.error(f"No se pudo registrar el producto: {e}")
                    finally:
                        cursor.close()
                        conexion.close()

# =========================
# Calculadora de Pulseras
# =========================
st.title("💰 Calculadora de Pulseras")

tipo_hilo = st.selectbox("Tipo de Hilo", ["Nylon", "Negro"])

ids_material = obtener_ids_material()
material_seleccionados = []
cantidades = []

st.markdown("### Selección de Materiales (Máx. 5)")
for i in range(5):
    col1, col2 = st.columns(2)
    with col1:
        mat_id = st.selectbox(f"ID Material {i+1}", options=ids_material, key=f"id_{i}")
    with col2:
        cant = st.number_input(f"Cantidad {i+1}", min_value=0, value=0, step=1, key=f"cant_{i}")
    material_seleccionados.append(mat_id)
    cantidades.append(cant)

if st.button("Calcular Precio"):
    costo_total_cuentas = sum([cantidades[i] * obtener_costo_cuenta(material_seleccionados[i]) for i in range(5)])
    costo_hilo = 2.4 if tipo_hilo == "Nylon" else 4.0
    costo_mano = 40.0
    costo_empaque = 10.0
    costos_fijos = costo_hilo + costo_mano + costo_empaque
    marketing = 0.15 * (costo_total_cuentas + costos_fijos)
    precio_real = costo_total_cuentas + costos_fijos + marketing
    precio_real = precio_real + 0.30 * precio_real

    # Clasificación
    if precio_real <= 160:
        clasificacion = "C"
        precio_clasificado = 160.0
    elif precio_real <= 200:
        clasificacion = "B"
        precio_clasificado = 190.0
    elif precio_real <= 250:
        clasificacion = "A"
        precio_clasificado = 250.0
    else:
        clasificacion = "A+"
        precio_clasificado = round(precio_real, 2)

    st.write(f"**Costo total:** ${costo_total_cuentas + costos_fijos:.2f}")
    st.write(f"**Precio real:** ${precio_real:.2f}")
    st.success(f"**Clasificación:** {clasificacion}, Precio Clasificado: ${precio_clasificado:.2f}")

    # Guardar globals para registro
    st.session_state['costo_total'] = costo_total_cuentas + costos_fijos
    st.session_state['precio_real'] = precio_real
    st.session_state['clasificacion'] = clasificacion
    st.session_state['precio_clasificado'] = precio_clasificado

st.markdown("### Registro de Pulsera Final")
id_producto = st.text_input("ID Producto Pulsera")
descripcion_pulsera = st.text_input("Descripción Pulsera")

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
