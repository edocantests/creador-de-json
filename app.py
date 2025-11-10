"""
Aplicación Streamlit: Generador de JSON Schema desde Texto
Autor: Asistente Claude
Descripción: Convierte descripciones en lenguaje natural a JSON schemas estructurados
"""

import streamlit as st
import json
import re
from datetime import datetime
from typing import Dict, Any, List

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Generador de JSON Schema",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def analizar_texto_y_generar_schema(texto: str) -> Dict[str, Any]:
    """
    Analiza el texto de entrada y genera un JSON schema estructurado.
    
    Args:
        texto: Descripción en lenguaje natural
        
    Returns:
        Diccionario con el schema JSON generado
    """
    
    # Schema base
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Schema Generado",
        "description": "Schema generado automáticamente desde texto",
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Convertir texto a minúsculas para análisis
    texto_lower = texto.lower()
    
    # Detectar campos mediante patrones comunes
    patrones = [
        # Patrón: "campo nombre (tipo)"
        r'campo\s+(\w+)\s+\((\w+)\)',
        # Patrón: "nombre: tipo"
        r'(\w+)\s*:\s*(\w+)',
        # Patrón: "- nombre (tipo)"
        r'-\s*(\w+)\s+\((\w+)\)',
        # Patrón: "nombre es un/una tipo"
        r'(\w+)\s+es\s+un[ao]?\s+(\w+)',
    ]
    
    campos_detectados = []
    
    for patron in patrones:
        matches = re.finditer(patron, texto_lower, re.MULTILINE)
        for match in matches:
            nombre_campo = match.group(1)
            tipo_campo = match.group(2) if len(match.groups()) > 1 else "string"
            campos_detectados.append((nombre_campo, tipo_campo))
    
    # Si no se detectaron campos con patrones, intentar análisis por palabras clave
    if not campos_detectados:
        campos_detectados = detectar_campos_por_palabras_clave(texto)
    
    # Mapeo de tipos comunes a tipos JSON Schema
    tipo_mapping = {
        "texto": "string",
        "cadena": "string",
        "string": "string",
        "str": "string",
        "numero": "number",
        "entero": "integer",
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "decimal": "number",
        "booleano": "boolean",
        "bool": "boolean",
        "boolean": "boolean",
        "fecha": "string",
        "date": "string",
        "email": "string",
        "correo": "string",
        "url": "string",
        "array": "array",
        "lista": "array",
        "arreglo": "array",
        "objeto": "object",
        "object": "object"
    }
    
    # Construir propiedades del schema
    for nombre, tipo in campos_detectados:
        tipo_json = tipo_mapping.get(tipo, "string")
        
        propiedad = {"type": tipo_json}
        
        # Añadir formato especial para ciertos tipos
        if tipo in ["email", "correo"]:
            propiedad["format"] = "email"
        elif tipo in ["fecha", "date"]:
            propiedad["format"] = "date"
        elif tipo == "url":
            propiedad["format"] = "uri"
        elif tipo_json == "array":
            propiedad["items"] = {"type": "string"}
        
        # Añadir descripción si se menciona "obligatorio" o "requerido"
        if re.search(rf'\b{nombre}\b.*\b(obligatorio|requerido|required)\b', texto_lower):
            schema["required"].append(nombre)
            propiedad["description"] = f"Campo {nombre} (obligatorio)"
        else:
            propiedad["description"] = f"Campo {nombre}"
        
        schema["properties"][nombre] = propiedad
    
    # Si no se detectó ningún campo, crear un ejemplo genérico
    if not schema["properties"]:
        schema["properties"] = {
            "ejemplo": {
                "type": "string",
                "description": "No se detectaron campos específicos. Este es un ejemplo genérico."
            }
        }
        schema["required"] = ["ejemplo"]
    
    return schema


def detectar_campos_por_palabras_clave(texto: str) -> List[tuple]:
    """
    Detecta posibles campos basándose en palabras clave comunes.
    
    Args:
        texto: Texto de entrada
        
    Returns:
        Lista de tuplas (nombre_campo, tipo_campo)
    """
    campos = []
    palabras = texto.lower().split()
    
    # Palabras clave que sugieren tipos de datos
    palabras_clave = {
        "nombre": "string",
        "apellido": "string",
        "direccion": "string",
        "ciudad": "string",
        "pais": "string",
        "email": "email",
        "correo": "email",
        "telefono": "string",
        "edad": "integer",
        "precio": "number",
        "cantidad": "integer",
        "fecha": "date",
        "descripcion": "string",
        "titulo": "string",
        "url": "url",
        "activo": "boolean",
        "habilitado": "boolean"
    }
    
    for palabra, tipo in palabras_clave.items():
        if palabra in palabras:
            campos.append((palabra, tipo))
    
    return campos


def validar_json(json_str: str) -> tuple[bool, str]:
    """
    Valida si un string es JSON válido.
    
    Args:
        json_str: String con el JSON a validar
        
    Returns:
        Tupla (es_valido, mensaje)
    """
    try:
        json.loads(json_str)
        return True, "✅ JSON válido"
    except json.JSONDecodeError as e:
        return False, f"❌ Error en JSON: {str(e)}"


def formatear_json(data: Dict[str, Any]) -> str:
    """
    Formatea un diccionario a JSON con indentación.
    
    Args:
        data: Diccionario a formatear
        
    Returns:
        String con JSON formateado
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


# ============================================================================
# INICIALIZACIÓN DEL ESTADO DE LA SESIÓN
# ============================================================================

if 'historial' not in st.session_state:
    st.session_state.historial = []

if 'schema_actual' not in st.session_state:
    st.session_state.schema_actual = None

if 'json_editado' not in st.session_state:
    st.session_state.json_editado = ""


# ============================================================================
# INTERFAZ DE USUARIO
# ============================================================================

# Título y descripción
st.title("📋 Generador de JSON Schema")
st.markdown("""
Esta aplicación convierte descripciones en lenguaje natural a esquemas JSON estructurados.

**Ejemplos de entrada:**
- "Usuario con campos: nombre (string), edad (integer), email (email), activo (boolean)"
- "Producto: titulo es un texto, precio es un numero, cantidad es un entero"
- "Datos obligatorios: id, nombre y fecha de creación"
""")

st.divider()

# Layout de dos columnas
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Entrada de Texto")
    
    # Área de texto para entrada
    texto_entrada = st.text_area(
        "Describe la estructura de datos que necesitas:",
        height=200,
        placeholder="Ejemplo: Usuario con nombre (texto), edad (entero), email (correo) y activo (booleano). Los campos nombre y email son obligatorios.",
        help="Describe los campos y sus tipos. Puedes usar formato libre o estructurado."
    )
    
    # Botones de acción
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        generar_btn = st.button("🚀 Generar Schema", type="primary", use_container_width=True)
    
    with col_btn2:
        limpiar_btn = st.button("🗑️ Limpiar", use_container_width=True)
    
    with col_btn3:
        ejemplo_btn = st.button("💡 Cargar Ejemplo", use_container_width=True)

with col2:
    st.subheader("📊 Schema Generado")
    
    # Contenedor para el resultado
    resultado_container = st.container()

# ============================================================================
# LÓGICA DE BOTONES
# ============================================================================

# Botón: Cargar ejemplo
if ejemplo_btn:
    texto_entrada = """
    Usuario con los siguientes campos:
    - nombre (texto) - obligatorio
    - email (correo) - obligatorio
    - edad (entero)
    - telefono (texto)
    - activo (booleano)
    - fecha_registro (fecha)
    """
    st.rerun()

# Botón: Limpiar
if limpiar_btn:
    st.session_state.schema_actual = None
    st.session_state.json_editado = ""
    st.rerun()

# Botón: Generar schema
if generar_btn:
    if texto_entrada.strip():
        with st.spinner("Analizando texto y generando schema..."):
            # Generar el schema
            schema = analizar_texto_y_generar_schema(texto_entrada)
            st.session_state.schema_actual = schema
            st.session_state.json_editado = formatear_json(schema)
            
            # Agregar al historial
            st.session_state.historial.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "texto": texto_entrada[:100] + "..." if len(texto_entrada) > 100 else texto_entrada,
                "schema": schema
            })
            
        st.success("✅ Schema generado exitosamente!")
    else:
        st.warning("⚠️ Por favor, ingresa un texto para generar el schema.")

# ============================================================================
# MOSTRAR RESULTADO
# ============================================================================

with resultado_container:
    if st.session_state.schema_actual:
        # Tabs para visualización y edición
        tab1, tab2 = st.tabs(["👁️ Visualización", "✏️ Edición"])
        
        with tab1:
            st.json(st.session_state.schema_actual)
        
        with tab2:
            json_editado = st.text_area(
                "Edita el JSON:",
                value=st.session_state.json_editado,
                height=300,
                key="json_editor"
            )
            
            # Validar JSON editado
            es_valido, mensaje = validar_json(json_editado)
            
            if es_valido:
                st.success(mensaje)
                st.session_state.json_editado = json_editado
            else:
                st.error(mensaje)
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar JSON Schema",
            data=st.session_state.json_editado,
            file_name=f"schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.info("👆 Ingresa un texto y presiona 'Generar Schema' para comenzar.")

# ============================================================================
# SIDEBAR: HISTORIAL Y CONFIGURACIÓN
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.markdown("### 📚 Historial de Conversiones")
    
    if st.session_state.historial:
        st.caption(f"Total: {len(st.session_state.historial)} conversiones")
        
        for i, item in enumerate(reversed(st.session_state.historial[-5:])):
            with st.expander(f"🕐 {item['timestamp']}", expanded=False):
                st.caption(f"**Texto:** {item['texto']}")
                if st.button(f"Cargar", key=f"load_{i}"):
                    st.session_state.schema_actual = item['schema']
                    st.session_state.json_editado = formatear_json(item['schema'])
                    st.rerun()
        
        if st.button("🗑️ Limpiar Historial"):
            st.session_state.historial = []
            st.rerun()
    else:
        st.info("No hay conversiones en el historial.")
    
    st.divider()
    
    st.markdown("### ℹ️ Información")
    st.markdown("""
    **Tipos soportados:**
    - `string` (texto)
    - `integer` (entero)
    - `number` (número)
    - `boolean` (booleano)
    - `array` (lista)
    - `object` (objeto)
    
    **Formatos especiales:**
    - `email` (correo)
    - `date` (fecha)
    - `uri` (URL)
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("💡 **Tip:** Usa lenguaje natural para describir tu estructura de datos. La app intentará detectar automáticamente los campos y tipos.")
