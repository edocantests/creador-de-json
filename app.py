"""
Streamlit app: PDF -> JSON optimizado para IA

Funciones principales:
- Subir PDF
- Extraer texto y metadatos (pdfplumber)
- Normalizar y limpiar texto
- Chunking configurable (tamaño y solapamiento)
- (Opcional) calcular embeddings con sentence-transformers
- Descargar JSON con schema pensado para IA

Author: Generado por ChatGPT
"""

import streamlit as st
import pdfplumber
import json
import uuid
import re
from datetime import datetime
from langdetect import detect, DetectorFactory
from sentence_transformers import SentenceTransformer
import numpy as np
import nltk
from typing import List, Dict, Any

# asegurar reproducibilidad en langdetect
DetectorFactory.seed = 0

# Descargar recursos de NLTK en runtime si no existen
nltk_downloaded = False
try:
    nltk.data.find("tokenizers/punkt")
    nltk_downloaded = True
except Exception:
    try:
        nltk.download("punkt")
        nltk_downloaded = True
    except Exception:
        nltk_downloaded = False

from nltk.tokenize import sent_tokenize

# --------------------------
# Utilidades
# --------------------------

def clean_text(text: str) -> str:
    """Limpieza básica del texto extraído del PDF."""
    if text is None:
        return ""
    # normalizar espacios y saltos de línea
    text = text.replace("\r", "\n")
    # eliminar múltiples saltos de línea
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # eliminar espacios repetidos
    text = re.sub(r'[ \t]{2,}', ' ', text)
    # recortar espacios al inicio/fin
    text = text.strip()
    return text

def chunk_text_by_sentences(text: str, max_tokens: int = 200, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Dividir texto en chunks basados en oraciones.
    max_tokens: aproximación de "tamaño del chunk" medida en tokens/words (no en tokens reales del modelo).
    overlap: cantidad de palabras solapadas entre chunks.
    Retorna lista de dict {id, text, start_sentence, end_sentence, word_count}
    """
    if not text:
        return []

    # tokenizar oraciones
    try:
        sentences = sent_tokenize(text)
    except Exception:
        # fallback simple: dividir por puntos
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

    # convertir a palabras para contar
    sent_words = [s.split() for s in sentences]
    chunks = []
    i = 0
    while i < len(sentences):
        words_count = 0
        chunk_sents = []
        j = i
        while j < len(sentences) and words_count + len(sent_words[j]) <= max_tokens:
            chunk_sents.append(sentences[j])
            words_count += len(sent_words[j])
            j += 1
        # si no crece (una oración muy larga), forzar avance de una oración
        if i == j:
            chunk_sents.append(sentences[j])
            words_count = len(sent_words[j])
            j += 1
        chunk_text = " ".join(chunk_sents).strip()
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": chunk_text,
            "start_sentence": i,
            "end_sentence": j - 1,
            "word_count": words_count
        })
        # avanzar considerando overlap (en palabras -> convertir overlap a oraciones aproximadas)
        # estrategia simple: retroceder por palabras equivalentes
        # Aquí simplificamos retrocediendo 'overlap' palabras contadas como oraciones
        if overlap <= 0:
            i = j
        else:
            # contar cuantas oraciones retroceden para aproximar el overlap
            k = j - 1
            overlap_words = 0
            while k >= 0 and overlap_words < overlap:
                overlap_words += len(sent_words[k])
                k -= 1
            i = max(0, k + 1)

    return chunks

def estimate_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang
    except Exception:
        return "und"  # undefined

def compute_embeddings(chunks: List[Dict[str, Any]], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """
    Compute embeddings for each chunk using sentence-transformers.
    Returns list of vectors (lists of floats).
    """
    if not chunks:
        return []
    model = SentenceTransformer(model_name)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    # convertir a listas serializables
    embeddings_list = [emb.astype(float).tolist() if isinstance(emb, np.ndarray) else list(map(float, emb)) for emb in embeddings]
    return embeddings_list

# --------------------------
# Schema JSON (document-level)
# --------------------------
def build_schema(document_meta: Dict[str, Any],
                 pages: List[Dict[str, Any]],
                 chunks: List[Dict[str, Any]],
                 embeddings: List[List[float]] = None) -> Dict[str, Any]:
    """
    Crea el JSON final con el siguiente esquema recomendado:
    {
      "schema_version": "1.0",
      "id": uuid,
      "title": optional,
      "source_filename": filename,
      "created_at": ISO,
      "language": "en",
      "metadata": {...},  # autor, producer, number_of_pages, etc.
      "pages": [ { page_number, text, cleaned_text, word_count, char_count } ],
      "chunks": [ { id, text, start_sentence, end_sentence, word_count, page_refs: [page_numbers] } ],
      "embeddings": { "model": name, "vectors": [[...], ... ] }  # optional
    }
    """
    payload = {
        "schema_version": "1.0",
        "id": str(uuid.uuid4()),
        "title": document_meta.get("title"),
        "source_filename": document_meta.get("filename"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "language": document_meta.get("language", "und"),
        "metadata": {
            "author": document_meta.get("author"),
            "producer": document_meta.get("producer"),
            "num_pages": document_meta.get("num_pages"),
        },
        "pages": pages,
        "chunks": chunks
    }
    if embeddings is not None:
        payload["embeddings"] = {
            "model": document_meta.get("embedding_model", "sentence-transformers"),
            "vectors": embeddings
        }
    return payload

# --------------------------
# Streamlit UI
# --------------------------

st.set_page_config(page_title="PDF → JSON (optimizado para IA)", layout="wide")

st.title("Convertidor PDF → JSON optimizado para IA")
st.markdown(
    "Suba un archivo PDF, ajuste las opciones de chunking y genere un JSON listo para indexar o procesar por modelos de lenguaje."
)

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Subir archivo .PDF", type=["pdf"])
    max_words = st.number_input("Tamaño aproximado del chunk (palabras)", min_value=50, max_value=2000, value=300, step=50, help="Tamaño objetivo por chunk en palabras.")
    overlap_words = st.number_input("Solapamiento entre chunks (palabras)", min_value=0, max_value=1000, value=50, step=25)
    detect_lang = st.checkbox("Detectar idioma del documento", value=True)
    compute_emb = st.checkbox("Calcular embeddings (sentence-transformers)", value=False)

with col2:
    if compute_emb:
        emb_model = st.selectbox("Modelo de embeddings (local)", options=["all-MiniLM-L6-v2", "all-mpnet-base-v2"], index=0)
        st.info("Calcular embeddings descargará y usará un modelo local (puede requerir GPU o tardar en CPU).")
    else:
        emb_model = None
    st.markdown("**Salida**")
    st.write("Se generará un archivo JSON con el schema recomendado. Puede descargarlo al terminar.")

process_btn = st.button("Procesar PDF")

if process_btn:
    if not uploaded_file:
        st.error("Por favor suba un archivo PDF primero.")
    else:
        with st.spinner("Extrayendo y procesando PDF..."):
            # leer PDF con pdfplumber
            try:
                pdf = pdfplumber.open(uploaded_file)
            except Exception as e:
                st.error(f"Error al abrir PDF: {e}")
                st.stop()

            pages_data = []
            all_text = []
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    raw = page.extract_text() or ""
                except Exception:
                    raw = ""
                cleaned = clean_text(raw)
                pages_data.append({

