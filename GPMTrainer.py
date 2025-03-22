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
        persist_dir="index_storage"
    )
    index = load_index_from_storage(storage_context)
    engine = index.as_query_engine()
except Exception as e:
    st.error(f"❌ Fehler beim Laden des Index: {e}")
    st.stop()

# ✅ Prüfen
if st.button("Antwort prüfen"):
    with st.spinner("🔍 Antwort wird geprüft..."):

        query = f"""
Du bist ein strenger, aber hilfsbereiter Lerncoach.

Frage: {st.session_state.aktuelle_frage}
Antwort des Nutzers: {antwort}

Deine Aufgabe:
1. Bewerte, ob die Antwort korrekt, teilweise korrekt oder falsch ist.
2. Gib konstruktives Feedback zur Antwort – nenne Verbesserungsmöglichkeiten.
3. Gib eine Beispielantwort, wie sie idealerweise aussehen sollte.
4. Antworte in freundlichem, motivierendem Ton.
"""
        result = engine.query(query)
        response_text = str(result)

        # GPT-Antwort anzeigen
        st.markdown("### 💡 GPT Rückmeldung:")
        st.write(response_text)

        # Bewertung: nur wenn korrekt UND kein "nicht korrekt"
        if "korrekt" in response_text.lower() and "nicht korrekt" not in response_text.lower():
            st.success("✅ Deine Antwort scheint korrekt oder weitgehend korrekt zu sein.")
            st.session_state.richtig += 1
        else:
            st.warning("❌ Die Antwort war unvollständig oder falsch.")
            st.session_state.falsch += 1

        # Neue Frage zufällig auswählen
        st.session_state.aktuelle_frage = random.choice(fragen_df["Frage"].tolist())

# 📊 Statistik
st.markdown("---")
st.markdown(f"**✅ Richtig beantwortet:** {st.session_state.richtig}")
st.markdown(f"**❌ Falsch beantwortet:** {st.session_state.falsch}")

if st.button("Zähler zurücksetzen"):
    st.session_state.richtig = 0
    st.session_state.falsch = 0
    st.success("🔄 Zähler zurückgesetzt.")
