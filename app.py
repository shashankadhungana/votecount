import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
st.set_page_config(page_title="Nepal 2026 Live", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_live")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# --- SMART PARTY DETECTOR ---
# This looks for any piece of the name/symbol in the data
PARTY_RULES = {
    "Rastriya Swatantra Party": {"keys": ["rsp", "bell", "ghanti", "balen", "घण्टी"], "color": "#00adef", "symbol": "🔔"},
    "CPN (UML)": {"keys": ["uml", "surya", "sun", "oli", "सूर्य"], "color": "#e21b22", "symbol": "☀️"},
    "Nepali Congress": {"keys": ["nc", "congress", "tree", "rukh", "gagan", "रुख"], "color": "#ff0000", "symbol": "🌳"},
    "Nepali Communist Party": {"keys": ["ncp", "maoist", "maobadi", "माओवादी"], "color": "#dd0000", "symbol": "⭐"},
    "RPP": {"keys": ["rpp", "halo", "plough", "lingden", "हलो"], "color": "#ffcc00", "symbol": "🚜"},
    "Shram Sanskriti Party": {"keys": ["shram", "sanskriti", "sampaang", "harka"], "color": "#4B0082", "symbol": "⚒️"}
}

def map_party(val):
    text = str(val).lower()
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
                # We search all candidate fields for the party name
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

# --- DISPLAY ---
st.title("🇳🇵 Nepal General Election 2082 Live")
st.write(f"**Live Count:** {pd.Timestamp.now().strftime('%H:%M:%S')}")

if not df.empty:
    # 1. THE PM BATTLE: BALEN VS OLI (Jhapa-5)
    st.divider()
    st.subheader("🔥 High-Stakes Battle: Jhapa-5")
    j5 = df[df['Constituency'] == "Jhapa-5"].sort_values('Votes', ascending=False)
    
    if not j5.empty:
        c1, c2 = st.columns(2)
        top = j5.iloc[0]
        c1.metric(f"Leader: {top['Candidate']} {top['Symbol']}", f"{top['Votes']:,} 🗳️", f"{top['Party']}")
        if len(j5) > 1:
            runner = j5.iloc[1]
            c2.metric(f"Runner-up: {runner['Candidate']} {runner['Symbol']}", f"{runner['Votes']:,}", f"Gap: {top['Votes']-runner['Votes']:,}")

    # 2. NATIONAL SEAT PROJECTION (Race to 138)
    st.divider()
    st.subheader("📊 Seat Projections (FPTP + PR)")
    
    # Winners in 165 FPTP seats
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    fptp_leads = winners['Party'].value_counts()

    # PR Projections (Based on 110 seats)
    total_votes = df['Votes'].sum()
    party_votes = df.groupby('Party')['Votes'].sum()
    
    projection_data = []
    for party in party_votes.index:
        share = party_votes[party] / total_votes if total_votes > 0 else 0
        fptp = fptp_leads.get(party, 0)
        pr = round(share * 110) if share >= 0.03 else 0 # 3% Threshold
        
        _, sym, color = map_party(party)
        projection_data.append({
            "Party": f"{sym} {party}",
            "Total": fptp + pr,
            "Color": color
        })

    proj_df = pd.DataFrame(projection_data).sort_values("Total", ascending=False)
    
    # Progress towards 138 majority
    for _, row in proj_df.head(3).iterrows():
        st.write(f"**{row['Party']}** ({row['Total']} / 138)")
        st.progress(min(row['Total'] / 138, 1.0))

    # 3. LEADERBOARD TABLE
    st.divider()
    st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.error("Waiting for data sync with R2.dev bucket...")
