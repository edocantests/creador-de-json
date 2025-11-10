import streamlit as st
import json
from io import BytesIO

st.set_page_config(page_title="Editor JSON", page_icon="📝", layout="wide")

st.title("📝 Editor de Archivos JSON")
st.markdown("---")

# Inicializar el estado de la sesión
if 'json_data' not in st.session_state:
    st.session_state.json_data = None
if 'json_text' not in st.session_state:
    st.session_state.json_text = ""

# Sección de carga de archivo
st.header("1️⃣ Cargar archivo JSON")
uploaded_file = st.file_uploader("Selecciona un archivo JSON", type=['json'])

if uploaded_file is not None:
    try:
        # Leer el archivo JSON
        json_data = json.load(uploaded_file)
        st.session_state.json_data = json_data
        st.session_state.json_text = json.dumps(json_data, indent=2, ensure_ascii=False)
        st.success("✅ Archivo cargado correctamente")
    except json.JSONDecodeError as e:
        st.error(f"❌ Error al leer el archivo JSON: {e}")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Sección de edición
if st.session_state.json_data is not None:
    st.markdown("---")
    st.header("2️⃣ Editar JSON")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Vista Previa")
        st.json(st.session_state.json_data)
    
    with col2:
        st.subheader("Editor de Texto")
        edited_text = st.text_area(
            "Edita el JSON aquí:",
            value=st.session_state.json_text,
            height=400,
            key="json_editor"
        )
        
        if st.button("🔄 Actualizar Vista Previa", type="primary"):
            try:
                # Validar y actualizar el JSON
                updated_json = json.loads(edited_text)
                st.session_state.json_data = updated_json
                st.session_state.json_text = edited_text
                st.success("✅ JSON actualizado correctamente")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON inválido: {e}")
    
    # Sección de descarga
    st.markdown("---")
    st.header("3️⃣ Descargar JSON modificado")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        indent_spaces = st.number_input("Espacios de indentación", min_value=0, max_value=8, value=2)
    
    with col2:
        sort_keys = st.checkbox("Ordenar claves alfabéticamente")
    
    # Preparar el archivo para descarga
    try:
        json_string = json.dumps(
            st.session_state.json_data,
            indent=indent_spaces,
            ensure_ascii=False,
            sort_keys=sort_keys
        )
        
        st.download_button(
            label="⬇️ Descargar JSON",
            data=json_string,
            file_name="archivo_modificado.json",
            mime="application/json",
            type="primary"
        )
    except Exception as e:
        st.error(f"❌ Error al preparar la descarga: {e}")

else:
    st.info("👆 Por favor, carga un archivo JSON para comenzar")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    <small>Editor JSON | Desarrollado con Streamlit</small>
    </div>
    """,
    unsafe_allow_html=True
)
