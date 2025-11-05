import streamlit as st
import json
import pandas as pd
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(
    page_title="JSON Editor & Downloader",
    page_icon="📄",
    layout="wide"
)

# Título de la aplicación
st.title("📄 JSON Editor & Downloader")
st.markdown("Pega tu código JSON, edítalo y descárgalo como archivo.")

# Sidebar para información
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Características:**
    - ✅ Validación de JSON
    - 📊 Vista previa de datos
    - 💾 Descarga en formato JSON
    - 🎨 Editor con sintaxis resaltada
    """)

# Inicializar variables de sesión
if 'json_data' not in st.session_state:
    st.session_state.json_data = None
if 'json_valid' not in st.session_state:
    st.session_state.json_valid = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""

# Ejemplo de JSON por defecto
default_json = """{
    "usuarios": [
        {
            "id": 1,
            "nombre": "Juan Pérez",
            "email": "juan@example.com",
            "activo": true
        },
        {
            "id": 2,
            "nombre": "María García",
            "email": "maria@example.com",
            "activo": false
        }
    ],
    "configuracion": {
        "tema": "oscuro",
        "idioma": "es"
    }
}"""

# Dividir en dos columnas
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Editor JSON")
    
    # Área de texto para ingresar JSON
    json_input = st.text_area(
        "Ingresa tu código JSON:",
        value=default_json,
        height=400,
        placeholder="Pega tu JSON aquí...",
        help="Asegúrate de que el JSON esté bien formateado"
    )
    
    # Botones de acción
    col1_1, col1_2, col1_3 = st.columns(3)
    
    with col1_1:
        if st.button("🔄 Validar JSON", use_container_width=True):
            try:
                json_data = json.loads(json_input)
                st.session_state.json_data = json_data
                st.session_state.json_valid = True
                st.session_state.error_message = ""
                st.success("✅ JSON válido!")
            except json.JSONDecodeError as e:
                st.session_state.json_valid = False
                st.session_state.error_message = f"Error en JSON: {str(e)}"
                st.error(f"❌ Error en JSON: {str(e)}")
    
    with col1_2:
        if st.button("🧹 Limpiar", use_container_width=True):
            st.session_state.json_data = None
            st.session_state.json_valid = False
            st.rerun()
    
    with col1_3:
        if st.button("📋 Ejemplo", use_container_width=True):
            st.rerun()

with col2:
    st.subheader("📊 Vista Previa")
    
    if st.session_state.json_valid and st.session_state.json_data:
        # Mostrar datos en formato expandible
        with st.expander("🔍 Ver JSON formateado", expanded=True):
            st.json(st.session_state.json_data)
        
        # Mostrar como tabla si es una lista
        if isinstance(st.session_state.json_data, list):
            st.subheader("📋 Vista de Tabla")
            df = pd.DataFrame(st.session_state.json_data)
            st.dataframe(df, use_container_width=True)
        elif isinstance(st.session_state.json_data, dict):
            # Intentar encontrar listas dentro del diccionario
            list_found = False
            for key, value in st.session_state.json_data.items():
                if isinstance(value, list) and len(value) > 0:
                    st.subheader(f"📋 Tabla: {key}")
                    df = pd.DataFrame(value)
                    st.dataframe(df, use_container_width=True)
                    list_found = True
            
            if not list_found:
                st.info("💡 El JSON es un objeto. Puedes verlo expandido arriba.")
    
    elif st.session_state.error_message:
        st.error(f"**Error:** {st.session_state.error_message}")
        st.info("💡 **Sugerencias:**\n- Verifica que todas las comillas estén cerradas\n- Asegúrate de que no haya comas extra al final\n- Verifica la estructura de corchetes y llaves")
    
    else:
        st.info("👈 Ingresa JSON y haz clic en 'Validar JSON' para comenzar")

# Sección de descarga
st.markdown("---")
st.subheader("💾 Descargar JSON")

if st.session_state.json_valid and st.session_state.json_data:
    # Opciones de formato
    col3, col4, col5 = st.columns([2, 1, 1])
    
    with col3:
        filename = st.text_input(
            "Nombre del archivo:",
            value=f"datos_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="El archivo se guardará con extensión .json"
        )
    
    with col4:
        indent = st.selectbox(
            "Indentación:",
            options=[2, 4, 0],
            index=1,
            help="Espacios de indentación (0 para minificado)"
        )
    
    with col5:
        ensure_ascii = st.checkbox(
            "Caracteres ASCII",
            value=False,
            help="Forzar caracteres ASCII (útil para compatibilidad)"
        )
    
    # Preparar JSON para descarga
    try:
        json_str = json.dumps(
            st.session_state.json_data,
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=True
        )
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar JSON",
            data=json_str,
            file_name=f"{filename}.json",
            mime="application/json",
            use_container_width=True,
            help="Haz clic para descargar el archivo JSON"
        )
        
        # Mostrar información del archivo
        file_size = len(json_str.encode('utf-8'))
        st.caption(f"📏 Tamaño aproximado: {file_size} bytes")
        
    except Exception as e:
        st.error(f"Error al preparar descarga: {str(e)}")

else:
    st.warning("⚠️ Necesitas un JSON válido para poder descargar")

# Información adicional
with st.expander("📚 Consejos para trabajar con JSON"):
    st.markdown("""
    **Sintaxis JSON válida:**
    - Las cadenas deben usar comillas dobles `"texto"`
    - No comas finales en arrays u objetos
    - Valores permitidos: string, number, object, array, true, false, null
    
    **Ejemplo de JSON válido:**
    ```json
    {
        "nombre": "Ejemplo",
        "numero": 42,
        "activo": true,
        "lista": [1, 2, 3],
        "objeto": {
            "clave": "valor"
        }
    }
    ```
    """)

# Footer
st.markdown("---")
st.caption("Creado con Streamlit | JSON Editor & Downloader")
