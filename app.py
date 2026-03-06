import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Nepal Election 2082 Live", layout="wide")
st_autorefresh(interval=30000, key="nepal_fix")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# This dictionary helps the script "find" the party even if the JSON is messy
LOOKUP = {
    "Rastriya Swatantra Party": ["rsp", "bell", "ghanti", "balen", "swatantra"],
    "CPN (UML)": ["uml", "sun", "surya", "oli"],
    "Nepali Congress": ["nc", "congress", "tree", "rukh", "gagan"],
    "Nepali Communist Party": ["ncp", "maoist", "maobadi", "prachanda"],
    "RPP": ["rpp", "plough", "halo", "lingden"]
}

def auto_detect_party(val):
    """Scans the text for keywords to identify the party correctly."""
    text = str(val).lower()
    for party, keywords in LOOKUP.items():
        if any(k in text for k in keywords):
            return party
    return "Independent"

@st.cache_data(ttl=5)
def load_and_fix():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            # The candidates list might be called 'candidates' or 'data'
            cands = const.get('candidates', [])
            for c in cands:
                # We try to find 'party' or 'party_name' or 'group'
                raw_party = next((v for k, v in c.items() if 'party' in k.lower()), "Independent")
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": next((v for k, v in c.items() if 'name' in k.lower()), "Unknown"),
                    "Party": auto_detect_party(raw_party),
                    "Votes": int(next((v for k, v in c.items() if 'vote' in k.lower()), 0))
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame()

df = load_and_fix()

# --- THE DASHBOARD ---
st.title("🇳🇵 Nepal General Election 2082 Live")

if not df.empty:
    # 1. LIVE PM BATTLE (Jhapa-5)
    st.subheader("🔥 The Battle for Jhapa-5")
    j5 = df[df['Constituency'] == "Jhapa-5"].sort_values('Votes', ascending=False)
    if not j5.empty:
        p1, p2 = st.columns(2)
        top = j5.iloc[0]
        p1.metric(f"Leader: {top['Candidate']}", f"{top['Votes']:,} 🗳️", f"{top['Party']}")
        if len(j5) > 1:
            sec = j5.iloc[1]
            p2.metric(f"Runner-up: {sec['Candidate']}", f"{sec['Votes']:,}", f"Margin: {top['Votes']-sec['Votes']:,}", delta_color="inverse")

    # 2. NATIONAL SEAT TALLY
    st.divider()
    # Winner in each of the 165 seats
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    tally = winners['Party'].value_counts().reset_index()
    tally.columns = ['Party', 'FPTP Seats']

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("National Seat Share")
        fig = px.bar(tally, x='FPTP Seats', y='Party', orientation='h', color='Party',
                     color_discrete_map={"Rastriya Swatantra Party": "#00adef", "CPN (UML)": "#e21b22", "Nepali Congress": "#ff0000"})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("### Tally Table")
        st.table(tally)

    # 3. SEARCH
    st.divider()
    query = st.text_input("🔍 Search for a Candidate or Constituency")
    if query:
        st.dataframe(df[df.apply(lambda x: query.lower() in str(x).lower(), axis=1)])
else:
    st.warning("Connecting to Election Commission stream...")
