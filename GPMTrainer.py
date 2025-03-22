import streamlit as st
import openai
import pandas as pd
import random

from llama_index import load_index_from_storage
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.storage.storage_context import StorageContext

import os
st.write("📂 index_storage Inhalt:")
st.write(os.listdir("index_storage"))

# 🔐 OpenAI API-Key laden
openai.api_key = st.secrets["openai_api_key"]

# 📦 Vektorindex laden
storage_context = StorageContext.from_defaults(persist_dir="index_storage")
index = load_index_from_storage(storage_context)

# 🔎 Nur Top 3 passende Abschnitte an GPT weitergeben
query_engine = RetrieverQueryEngine.from_index(index, similarity_top_k=3)

# 📄 Fragen aus Excel laden
@st.cache_data
def lade_fragen(pfad: str) -> pd.DataFrame:
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
    st.session_state.aktuelle_frage = ""
if "user_antwort" not in st.session_state:
    st.session_state.user_antwort = ""

# 🎲 Neue zufällige Frage
if st.button("🎲 Neue Frage"):
    st.session_state.aktuelle_frage = fragen_df.sample(1).iloc[0, 0]
    st.session_state.user_antwort = ""

# 📋 Anzeige der aktuellen Frage
st.title("📚 GPT Lerntrainer")
st.markdown("**Frage:**")
st.markdown(st.session_state.aktuelle_frage)

antwort = st.text_area("✍️ Deine Antwort", value=st.session_state.user_antwort, height=150)

# ✅ Antwort prüfen per GPT
if st.button("✅ Antwort prüfen"):
    st.session_state.user_antwort = antwort
    frage = st.session_state.aktuelle_frage

    with st.spinner("GPT denkt nach..."):
        try:
            # Hole Kontext aus PDF-Wissensdatenbank
            context = query_engine.query(frage).response

            prompt = f"""
Du bist ein strenger, aber hilfsbereiter Lerncoach. Vergleiche die folgende Nutzerantwort mit dem relevanten Wissen aus den Studienunterlagen.

Frage: {frage}
Antwort des Nutzers: {antwort}
Relevanter Kontext: {context}

Gib eine präzise Rückmeldung:
- Ist die Antwort richtig, teilweise richtig oder falsch?
- Was fehlt oder könnte besser sein?
- Optional: Formuliere eine Musterantwort.

Antworte bitte strukturiert.
"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            output = response.choices[0].message.content
            st.markdown("### 🤖 GPT-Feedback:")
            st.markdown(output)

            # Zähler erhöhen (einfaches Matching)
            if "richtig" in output.lower():
                st.session_state.richtig += 1
            else:
                st.session_state.falsch += 1

        except Exception as e:
            st.error(f"Fehler bei der GPT-Anfrage:\n\n{str(e)}")

# 📊 Auswertung
st.markdown(f"✅ **Richtig**: {st.session_state.richtig} ❌ **Falsch**: {st.session_state.falsch}")
if st.button("🔄 Zähler zurücksetzen"):
    st.session_state.richtig = 0
    st.session_state.falsch = 0
