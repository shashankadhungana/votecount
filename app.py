import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- SETTINGS ---
st.set_page_config(page_title="Nepal Election 2026", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_refresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# Party Meta with Flexible Keys
PARTY_META = {
    "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#00adef"},
    "Nepali Congress": {"symbol": "🌳", "color": "#ff0000"},
    "CPN (UML)": {"symbol": "☀️", "color": "#e21b22"},
    "CPN (Maoist Centre)": {"symbol": "☭", "color": "#dd0000"},
    "Rastriya Prajatantra Party": {"symbol": "🚜", "color": "#ffcc00"},
    "Independent": {"symbol": "👤", "color": "#808080"}
}

def get_party_meta(name):
    name_str = str(name).lower()
    for key, meta in PARTY_META.items():
        if key.lower() in name_str or (hasattr(meta, 'get') and name_str in key.lower()):
            return meta
    return {"symbol": "🗳️", "color": "#333333"}

@st.cache_data(ttl=10)
def load_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            for cand in const.get('candidates', []):
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name', 'N/A'),
                    "Party": cand.get('party', 'Independent'),
                    "Votes": int(cand.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- HEADER ---
st.title("🇳🇵 Nepal Election 2026 Live Dashboard")
st.markdown("---")

if not df.empty:
    # 1. CALCULATE SEAT PROJECTIONS
    # FPTP Leads
    fptp_df = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    fptp_leads = fptp_df['Party'].value_counts().to_dict()

    # PR Projections (3% threshold)
    total_votes = df['Votes'].sum()
    party_votes = df.groupby('Party')['Votes'].sum()
    
    projection_list = []
    for party in party_votes.index:
        votes = party_votes[party]
        share = votes / total_votes if total_votes > 0 else 0
        
        fptp = fptp_leads.get(party, 0)
        pr = round(share * 110) if share >= 0.03 else 0 # 110 PR seats
        
        meta = get_party_meta(party)
        projection_list.append({
            "Party": party,
            "Symbol": meta['symbol'],
            "FPTP": fptp,
            "PR": pr,
            "Total": fptp + pr,
            "Color": meta['color']
        })

    proj_df = pd.DataFrame(projection_list)

    if not proj_df.empty:
        proj_df = proj_df.sort_values("Total", ascending=False)

        # --- TOP METRIC: RACE TO 138 ---
        st.subheader("Race to Majority (138 Seats)")
        cols = st.columns(min(len(proj_df), 4))
        for i, row in enumerate(proj_df.head(len(cols)).to_dict('records')):
            with cols[i]:
                st.metric(f"{row['Symbol']} {row['Party']}", f"{row['Total']} Seats")
                progress = min(row['Total'] / 138, 1.0)
                st.progress(progress)

        # --- CHARTS ---
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(proj_df, x="Total", y="Party", orientation='h', 
                         color="Party", color_discrete_map={r['Party']: r['Color'] for r in projection_list},
                         title="Total Projected Seat Share (FPTP + PR)")
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("Leaderboard")
            st.dataframe(proj_df[["Symbol", "Party", "FPTP", "PR", "Total"]], hide_index=True)

    # --- SEARCH ---
    st.divider()
    search = st.text_input("🔍 Search Constituency Results")
    if search:
        st.write(df[df['Constituency'].str.contains(search, case=False)])

else:
    st.info("Waiting for election data to sync...")

# --- FOOTER ---
st.sidebar.markdown(f"**Last Sync:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.rerun()
