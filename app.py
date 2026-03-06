import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Nepal Election Fix", layout="wide")
st_autorefresh(interval=20000, key="refresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# Robust Mapping
PARTY_LOOKUP = {
    "Rastriya Swatantra Party": ["rsp", "bell", "bell", "घण्टी", "swatantra"],
    "Nepali Congress": ["nc", "congress", "tree", "रुख"],
    "CPN (UML)": ["uml", "sun", "सूर्य", "cpn-uml"],
    "CPN (Maoist)": ["maoist", "center", "maobadi", "माओवादी"],
    "RPP": ["rpp", "plough", "halo", "हलो"]
}

def clean_party(raw_val):
    if not raw_val: return "Independent"
    val = str(raw_val).lower()
    for official, aliases in PARTY_LOOKUP.items():
        if any(alias in val for alias in aliases):
            return official
    return "Independent"

@st.cache_data(ttl=5)
def fetch_and_debug():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        
        rows = []
        # We handle both list of dicts and nested dicts
        for entry in data:
            # 1. Get Constituency Name
            c_name = entry.get('name') or entry.get('constituency') or "Unknown"
            
            # 2. Find the candidates list (it might be called 'candidates' or something else)
            candidates = []
            for key in ['candidates', 'data', 'results', 'list']:
                if key in entry and isinstance(entry[key], list):
                    candidates = entry[key]
                    break
            
            # 3. Process each candidate
            for cand in candidates:
                # DYNAMICALLY FIND THE PARTY FIELD
                # We check every key in the candidate object for 'party' or 'group'
                raw_party = "Independent"
                for k, v in cand.items():
                    if 'party' in k.lower() or 'group' in k.lower() or 'symbol' in k.lower():
                        raw_party = v
                        break
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name') or cand.get('candidate_name') or "Unknown",
                    "Raw_Party": raw_party,
                    "Party": clean_party(raw_party),
                    "Votes": int(cand.get('votes') or cand.get('count') or 0)
                })
        return pd.DataFrame(rows), data
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), None

df, raw_json = fetch_and_debug()

st.title("🇳🇵 Nepal Election 2026: Live Tally")

if not df.empty:
    # Seat Count
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seat_tally = winners['Party'].value_counts().reset_index()
    seat_tally.columns = ['Party', 'Seats']

    st.header("FPTP Seat Tally")
    st.bar_chart(data=seat_tally, x='Party', y='Seats')
    st.table(seat_tally)

    st.header("All Candidate Results")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No data found. Please check the 'Raw JSON Debug' below.")

# --- THE FIXER: DEBUG SECTION ---
st.divider()
with st.expander("🛠️ DEBUG: Inspect JSON Structure (Open this if it still shows Independent)"):
    if raw_json:
        st.write("The script sees these keys in your first entry:")
        st.write(list(raw_json[0].keys()) if len(raw_json) > 0 else "Empty List")
        st.write("Full JSON Preview:")
        st.json(raw_json[0] if len(raw_json) > 0 else {})
