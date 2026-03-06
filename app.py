import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- DASHBOARD CONFIG ---
st.set_page_config(page_title="Nepal Election 2082 Live", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_refresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# --- PARTY MAPPING (Based on March 2026 Data) ---
PARTY_META = {
    "Rastriya Swatantra Party": {"abbr": "RSP", "symbol": "🔔", "color": "#00adef", "keywords": ["rsp", "swatantra", "bell", "घण्टी"]},
    "CPN (UML)": {"abbr": "UML", "symbol": "☀️", "color": "#e21b22", "keywords": ["uml", "cpn-uml", "sun", "सूर्य"]},
    "Nepali Congress": {"abbr": "NC", "symbol": "🌳", "color": "#ff0000", "keywords": ["nc", "congress", "tree", "रुख"]},
    "Nepali Communist Party": {"abbr": "NCP", "symbol": "⭐", "color": "#dd0000", "keywords": ["ncp", "maobadi", "maoist"]},
    "Rastriya Prajatantra Party": {"abbr": "RPP", "symbol": "🚜", "color": "#ffcc00", "keywords": ["rpp", "plough", "halo"]},
    "Shram Sanskriti Party": {"abbr": "SSP", "symbol": "⚒️", "color": "#4B0082", "keywords": ["shram", "sanskriti"]}
}

def identify_party(raw_name):
    name = str(raw_name).lower()
    for official, meta in PARTY_META.items():
        if any(k in name for k in meta['keywords']):
            return official
    return "Independent"

@st.cache_data(ttl=10)
def load_live_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for entry in data:
            c_name = entry.get('name', 'Unknown')
            for cand in entry.get('candidates', []):
                p_name = identify_party(cand.get('party', ''))
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name', 'Unknown'),
                    "Party": p_name,
                    "Votes": int(cand.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

df = load_live_data()

# --- HEADER ---
st.title("🇳🇵 Nepal Election 2082: Live Vote Count")
st.info("Tracking 165 FPTP Constituencies + 110 PR Seat Projections")

if not df.empty:
    # 1. PM RACE TRACKER (Jhapa-5 Focus)
    st.subheader("🔥 Key PM Contenders")
    pm_cols = st.columns(3)
    
    # Specific logic for Jhapa-5
    jhapa5 = df[df['Constituency'] == "Jhapa-5"]
    
    # Balen Shah
    with pm_cols[0]:
        balen = jhapa5[jhapa5['Candidate'].str.contains("Balen", case=False)]
        votes = balen['Votes'].sum() if not balen.empty else 0
        st.metric("Balendra Shah 🔔", f"{votes:,} votes", "Leading" if votes > 0 else "")

    # KP Oli
    with pm_cols[1]:
        oli = jhapa5[jhapa5['Candidate'].str.contains("Oli", case=False)]
        votes = oli['Votes'].sum() if not oli.empty else 0
        st.metric("KP Sharma Oli ☀️", f"{votes:,} votes", delta=None)

    # Gagan Thapa
    with pm_cols[2]:
        gagan = df[df['Candidate'].str.contains("Gagan", case=False)]
        votes = gagan['Votes'].sum() if not gagan.empty else 0
        st.metric("Gagan Thapa 🌳", f"{votes:,} votes")

    # 2. SEAT PROJECTIONS (The Race to 138)
    st.divider()
    st.subheader("📊 Path to Majority (FPTP + PR)")
    
    # FPTP Leads
    fptp_winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    fptp_counts = fptp_winners['Party'].value_counts()
    
    # PR Projections (Based on national vote share)
    total_national_votes = df['Votes'].sum()
    party_vote_share = df.groupby('Party')['Votes'].sum()
    
    final_projections = []
    for party in party_vote_share.index:
        share = party_vote_share[party] / total_national_votes
        fptp = fptp_counts.get(party, 0)
        pr = round(share * 110) if share >= 0.03 else 0 # 3% Threshold
        
        meta = PARTY_META.get(party, {"symbol": "👤", "color": "#808080"})
        final_projections.append({
            "Party": f"{meta['symbol']} {party}",
            "FPTP Leads": fptp,
            "PR Projected": pr,
            "Total Seats": fptp + pr,
            "Color": meta['color']
        })

    proj_df = pd.DataFrame(final_projections).sort_values("Total Seats", ascending=False)
    
    # Progress Bars for top 3
    for _, row in proj_df.head(3).iterrows():
        st.write(f"**{row['Party']}** ({row['Total Seats']} / 138)")
        st.progress(min(row['Total Seats'] / 138, 1.0))

    # 3. DETAILED DATA
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        fig = px.bar(proj_df, x="Total Seats", y="Party", color="Party", orientation='h',
                     color_discrete_map={r['Party']: r['Color'] for r in final_projections})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("### Live Leaderboard")
        st.dataframe(proj_df[["Party", "FPTP Leads", "PR Projected", "Total Seats"]], hide_index=True)

else:
    st.warning("🔄 Fetching live data from Election Commission...")
