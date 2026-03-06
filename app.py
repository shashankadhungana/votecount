import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CONFIG & THEME ---
st.set_page_config(page_title="Nepal Election 2026: The PM Race", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_live")

# Live Data Source
SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# PM Contenders and their specific Constituencies
PM_CONTENDERS = {
    "Balen Shah": {"constituency": "Jhapa-5", "party": "Rastriya Swatantra Party", "symbol": "🔔", "color": "#00adef"},
    "KP Sharma Oli": {"constituency": "Jhapa-5", "party": "CPN (UML)", "symbol": "☀️", "color": "#e21b22"},
    "Gagan Thapa": {"constituency": "Sarlahi-4", "party": "Nepali Congress", "symbol": "🌳", "color": "#ff0000"}
}

# --- DATA PROCESSING ---
def flatten_data(data):
    rows = []
    for const in data:
        c_name = const.get('name', 'Unknown')
        for cand in const.get('candidates', []):
            rows.append({
                "Constituency": c_name,
                "Candidate": cand.get('name', 'Unknown'),
                "Party": cand.get('party', 'Independent'),
                "Votes": int(cand.get('votes', 0))
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=10)
def load_live_results():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        return flatten_data(r.json())
    except:
        return pd.DataFrame()

df = load_live_results()

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #DC143C;'>🇳🇵 Nepal General Election 2026 Live</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>The Battle for Singha Durbar</h4>", unsafe_allow_html=True)

if not df.empty:
    # --- SECTION 1: THE PM RACE (The "Big Three") ---
    st.divider()
    st.subheader("🔥 High-Stakes PM Race Tracker")
    pm_cols = st.columns(len(PM_CONTENDERS))

    for i, (name, info) in enumerate(PM_CONTENDERS.items()):
        with pm_cols[i]:
            # Filter data for this specific candidate
            match = df[(df['Candidate'].str.contains(name, case=False)) & 
                       (df['Constituency'] == info['constituency'])]
            
            votes = match['Votes'].sum() if not match.empty else 0
            
            # Find the closest rival in that constituency
            rivals = df[(df['Constituency'] == info['constituency']) & 
                        (~df['Candidate'].str.contains(name, case=False))]
            rival_votes = rivals['Votes'].max() if not rivals.empty else 0
            margin = votes - rival_votes

            # Visual Card
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; background-color: #f0f2f6; border-left: 10px solid {info['color']};">
                <h2 style="margin:0;">{info['symbol']} {name}</h2>
                <p style="margin:0; color: gray;">{info['party']}</p>
                <p style="margin:0; font-weight: bold;">{info['constituency']}</p>
                <hr>
                <h1 style="margin:0; color: {info['color']};">{votes:,}</h1>
                <p style="margin:0;">Lead: <span style="color: {'green' if margin > 0 else 'red'};">{margin:+,}</span></p>
            </div>
            """, unsafe_allow_html=True)

    # --- SECTION 2: PARTY STANDINGS ---
    st.divider()
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("National Party Lead (Seats & Votes)")
        party_votes = df.groupby('Party')['Votes'].sum().reset_index().sort_values('Votes', ascending=False)
        fig = px.bar(party_votes, x='Votes', y='Party', color='Party', orientation='h',
                     title="National Popular Vote Share",
                     color_discrete_map={k: v['color'] for k, v in PM_CONTENDERS.items()})
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Latest Constituency Winners")
        # Showing the top candidate for each constituency (simulated "Wins")
        winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
        st.dataframe(winners[['Constituency', 'Candidate', 'Votes']], hide_index=True)

    # --- SECTION 3: SEARCH ---
    st.divider()
    query = st.text_input("🔍 Search any Constituency (e.g. Kathmandu, Jhapa, Chitwan)")
    if query:
        search_results = df[df['Constituency'].str.contains(query, case=False)]
        st.table(search_results.sort_values('Votes', ascending=False))

else:
    st.error("Unable to reach Election Server. Retrying in 30 seconds...")

# --- SIDEBAR INFO ---
st.sidebar.title("Election 2082 B.S.")
st.sidebar.info("""
**Major Contests:**
- **Jhapa-5:** Balen Shah 🔔 vs KP Oli ☀️
- **Sarlahi-4:** Gagan Thapa 🌳
- **Chitwan-2:** Rabi Lamichhane 🔔
""")
