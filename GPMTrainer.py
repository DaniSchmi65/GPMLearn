import streamlit as st
import pandas as pd
import random
import openai
import os
import importlib.metadata
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.query_engine import RetrieverQueryEngine

# 🧪 Zeige LlamaIndex-Version
version = importlib.metadata.version("llama-index")
st.write(f"✅ LlamaIndex Version: {version}")

# 📁 Verzeichnisinhalt debuggen (optional)
if os.path.exists("index_storage"):
    st.write("📁 Inhalt von index_storage:", os.listdir("index_storage"))
else:
    st.error("❌ index_storage-Verzeichnis nicht gefunden!")

# 🔐 OpenAI API-Key laden
openai.api_key = st.secrets["openai_api_key"]

# 📄 Fragen aus Excel laden
@st.cache_data
def lade_fragen(pfad):
    df = pd.read_excel(pfad)
    df.columns = ["Frage"]
    return df

fragen_df = lade_fragen("fragen.xlsx")

# 🧠 Session State initialisieren
if "richtig" not in st.session_state:
    st.session_state.richtig = 0
if "falsch" not in st.session_state:
    st.session_state.falsch = 0
if "aktuelle_frage" not in st.session_state:
    st.session_state.aktuelle_frage = random.choice(fragen_df["Frage"].tolist())

st.title("🧠 GPT-Lerntrainer")
st.subheader("Beantworte die folgende Frage:")

# ❓ Frage anzeigen
st.markdown(f"**Frage:** {st.session_state.aktuelle_frage}")

# ✍️ Eingabe
antwort = st.text_area("Deine Antwort:")

# 📦 Vektorindex laden
try:
    storage_context = StorageContext.from_defaults(
        persist_dir="index_storage",
        vector_store_namespace="default",
        docstore_namespace="default",
        index_store_namespace="default"
    )
    index = load_index_from_storage(storage_context)
    engine = RetrieverQueryEngine.from_index(index)
except Exception as e:
    st.error(f"❌ Fehler beim Laden des Index: {e}")
    st.stop()

# ✅ Prüfen
if st.button("Antwort prüfen"):
    with st.spinner("🔍 Antwort wird geprüft..."):
        query = f"Bewerte die folgende Antwort auf die Frage:\n\nFrage: {st.session_state.aktuelle_frage}\nAntwort: {antwort}\n\nGib an, ob die Antwort korrekt ist. Wenn nicht, erkläre warum und gib Hinweise, was fehlt oder verbessert werden kann."
        result = engine.query(query)
        response_text = str(result)

        if "korrekt" in response_text.lower():
            st.success("✅ Deine Antwort scheint korrekt oder weitgehend korrekt zu sein.")
            st.session_state.richtig += 1
        else:
            st.warning("❌ Die Antwort war unvollständig oder falsch.")
            st.session_state.falsch += 1

        st.markdown("### 💡 GPT Rückmeldung:")
        st.write(response_text)

        # Neue Frage wählen
        st.session_state.aktuelle_frage = random.choice(fragen_df["Frage"].tolist())

# 📊 Statistik
st.markdown("---")
st.markdown(f"**✅ Richtig beantwortet:** {st.session_state.richtig}")
st.markdown(f"**❌ Falsch beantwortet:** {st.session_state.falsch}")

if st.button("Zähler zurücksetzen"):
    st.session_state.richtig = 0
    st.session_state.falsch = 0
    st.success("🔄 Zähler zurückgesetzt.")
