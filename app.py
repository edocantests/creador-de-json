import streamlit as st
import json
import re

st.set_page_config(page_title="TXT to JSON Optimizer", page_icon="🧠", layout="centered")

st.title("🧠 TXT → JSON Optimizer for AI")
st.write("Upload a `.txt` file and convert it into a structured JSON format optimized for AI models.")

uploaded_file = st.file_uploader("📤 Upload your TXT file", type=["txt"])

def split_text_into_sections(text, max_length=500):
    """
    Split the text into logical sections using punctuation and length limits.
    """
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    sections, current_section = [], ""

    for sentence in sentences:
        if len(current_section) + len(sentence) < max_length:
            current_section += " " + sentence
        else:
            sections.append(current_section.strip())
            current_section = sentence

    if current_section:
        sections.append(current_section.strip())

    return sections

if uploaded_file:
    # Read and decode text
    text = uploaded_file.read().decode("utf-8").strip()
    st.subheader("📄 Preview of Uploaded Text")
    st.text_area("Text content:", text[:1000] + ("..." if len(text) > 1000 else ""), height=200)

    # Split and process text
    sections = split_text_into_sections(text)

    data = {
        "metadata": {
            "source": uploaded_file.name,
            "total_sections": len(sections)
        },
        "data": [
            {
                "section_id": i + 1,
                "content": sec,
                "tokens_estimated": len(sec.split())
            }
            for i, sec in enumerate(sections)
        ]
    }

    json_output = json.dumps(data, indent=2, ensure_ascii=False)

    # Display result
    st.subheader("✅ JSON Output Preview")
    st.code(json_output[:1000] + ("..." if len(json_output) > 1000 else ""), language="json")

    # Download button
    st.download_button(
        label="📥 Download JSON File",
        data=json_output.encode("utf-8"),
        file_name=uploaded_file.name.replace(".txt", ".json"),
        mime="application/json"
    )

st.markdown("---")
st.caption("Created with ❤️ using Streamlit")
