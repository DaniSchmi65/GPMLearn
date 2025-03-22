
import streamlit as st
import random
import pandas as pd
from typing import Tuple
import openai

# GPT API-Schlüssel setzen
openai.api_key = st.secrets["openai_api_key"]

# -------------------------------
# Funktionen
# -------------------------------

@st.cache_data
def lade_fragen(pfad: str) -> pd.DataFrame:
    df = pd.read_excel(pfad)
    df.columns = ["Frage"]  # Nur eine Spalte mit Fragen
    return df

def frage_stellen(df: pd.DataFrame) -> str:
    return df.sample(1).iloc[0, 0]

def gpt_bewertung(user_antwort: str, frage: str, kontext: str) -> Tuple[str, bool]:
    prompt = f"""
Du bist ein Prüfer in einer Lernanwendung. Der Benutzer hat folgende Frage beantwortet:

Frage: {frage}

Antwort des Nutzers: {user_antwort}

Hier ist der relevante Wissenskontext aus Studienunterlagen:

{kontext}

Bewerte die Antwort streng, aber fair. Sage, ob die Antwort richtig, teilweise richtig oder falsch ist.
Gib Verbesserungsvorschläge, wenn nötig.

Antwort im Format:

Bewertung: [Richtig | Teilweise richtig | Falsch]
Feedback: <Begründung und Verbesserungsvorschlag>
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        antwort = response.choices[0].message.content
        richtig = "Bewertung: Richtig" in antwort
        return antwort, richtig
    except Exception as e:
        return f"Fehler bei der GPT-Anfrage: {e}", False

# -------------------------------
# App UI
# -------------------------------

st.set_page_config(page_title="GPT Lerntrainer", layout="centered")
st.title("🎓 GPT-gestützter Lerntrainer")

# Fortschrittszähler (Session State)
if "richtig" not in st.session_state:
    st.session_state.richtig = 0
if "falsch" not in st.session_state:
    st.session_state.falsch = 0
if "aktuelle_frage" not in st.session_state:
    st.session_state.aktuelle_frage = ""

# Fragen laden
fragen_df = lade_fragen("PrüfungsfragenInternSauber.xlsx")

# Kontext vorbereiten (aus PDF – hier als Platzhalter)
with open("kontext_basis.txt", "r", encoding="utf-8") as f:
    kontext_text = f.read()

# Neue Frage anzeigen
if st.button("🎲 Neue Frage laden") or st.session_state.aktuelle_frage == "":
    st.session_state.aktuelle_frage = frage_stellen(fragen_df)
    st.session_state.user_antwort = ""

st.markdown(f"**Frage:** {st.session_state.aktuelle_frage}")
user_antwort = st.text_area("📝 Deine Antwort", value=st.session_state.get("user_antwort", ""), height=150)

if st.button("✅ Antwort prüfen"):
    st.session_state.user_antwort = user_antwort
    bewertung, ist_richtig = gpt_bewertung(user_antwort, st.session_state.aktuelle_frage, kontext_text)
    st.markdown("---")
    st.markdown(bewertung)

    if ist_richtig:
        st.session_state.richtig += 1
    else:
        st.session_state.falsch += 1

# Fortschritt anzeigen
st.markdown("---")
st.markdown(f"**✅ Richtig:** {st.session_state.richtig}  ❌ Falsch:** {st.session_state.falsch}")

if st.button("🔄 Zähler zurücksetzen"):
    st.session_state.richtig = 0
    st.session_state.falsch = 0

