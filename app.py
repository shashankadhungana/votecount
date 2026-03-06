import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
st.set_page_config(page_title="Nepal 2082 Election Live", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_live")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# --- UPDATED MARCH 2026 PARTY RULES ---
# These keywords are designed to catch exactly what the EC reports
PARTY_RULES = {
    "Rastriya Swatantra Party": {
        "keys": ["rsp", "rastriya swatantra", "swatantra party", "bell", "ghanti", "balen", "घण्टी"], 
        "color": "#00adef", "symbol": "🔔"
    },
    "Nepali Congress": {
        "keys": ["nc", "nepali congress", "congress", "tree", "rukh", "gagan", "रुख"], 
        "color": "#ff0000", "symbol": "🌳"
    },
    "CPN (UML)": {
        "keys": ["uml", "surya", "sun", "oli", "सूर्य", "unified marxist"], 
        "color": "#e21b22", "symbol": "☀️"
    },
    "Nepali Communist Party": {
        "keys": ["ncp", "maoist", "maobadi", "माओवादी", "prachanda", "centre"], 
        "color": "#dd0000", "symbol": "⭐"
    },
    "Shram Sanskriti Party": {
        "keys": ["shram", "sanskriti", "harka", "sampang", "dharan", "sp"], 
        "color": "#4B0082", "symbol": "⚒️"
    },
    "Rastriya Prajatantra Party": {
        "keys": ["rpp", "halo", "plough", "lingden", "हलो", "prajatantra"], 
        "color": "#ffcc00", "symbol": "🚜"
    }
}

def map_party(val):
    if not val: return "Independent", "👤", "#808080"
    text = str(val).lower().strip()
    for party, meta in PARTY_RULES.items():
        if any(k in text for k in meta['keys']):
            return party, meta['symbol'], meta['color']
    return "Independent", "👤", "#808080"

@st.cache_data(ttl=5)
def get_clean_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            for cand in const.get('candidates', []):
                p_raw = cand.get('party', '') or cand.get('party_name', '')
                p_name, p_sym, p_color = map_party(p_raw)
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name', 'N/A'),
                    "Party": p_name,
                    "Symbol": p_sym,
                    "Color": p_color,
                    "Votes": int(cand.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

df = get_clean_data()

# --- THE LIVE DASHBOARD ---
st.title("🇳🇵 Nepal House of Representatives Election 2082")
st.markdown(f"**Last Refreshed:** {pd.Timestamp.now().strftime('%H:%M:%S')}")

if not df.empty:
    # 1. THE BIG BATTLE: JHAPA-5
    st.divider()
    st.subheader("🔥 Jhapa-5: Balen Shah vs KP Oli")
    jhapa = df[df['Constituency'] == "Jhapa-5"].sort_values('Votes', ascending=False)
    
    if not jhapa.empty:
        c1, c2, c3 = st.columns(3)
        top = jhapa.iloc[0]
        c1.metric("Leading", f"{top['Candidate']} {top['Symbol']}", f"{top['Votes']:,} 🗳️")
        if len(jhapa) > 1:
            runner = jhapa.iloc[1]
            c2.metric("Runner-up", f"{runner['Candidate']} {runner['Symbol']}", f"{runner['Votes']:,}")
            c3.metric("Lead Margin", f"{top['Votes'] - runner['Votes']:,}", delta_color="normal")

    # 2. SEAT SHARE SUMMARY
    st.divider()
    # Winner in each of the 165 seats
    fptp_winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seats = fptp_winners['Party'].value_counts().reset_index()
    seats.columns = ['Party', 'FPTP Leads']

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Current FPTP Seat Leads")
        # Map colors for the chart
        chart_colors = [map_party(p)[2] for p in seats['Party']]
        fig = px.bar(seats, x='FPTP Leads', y='Party', color='Party', orientation='h',
                     color_discrete_sequence=chart_colors)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.write("### Tally")
        st.table(seats)

    # 3. ALL CANDIDATES
    with st.expander("🔍 View All Candidate Results"):
        st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.warning("🔄 Fetching data from the Election Commission source...")
