import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- SETTINGS ---
st.set_page_config(page_title="Nepal Election 2082 Live", layout="wide")
st_autorefresh(interval=30000, key="nepal_live_sync")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=5)
def load_and_reflect_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        
        rows = []
        for const in data:
            c_name = str(const.get('name', 'Unknown Constituency'))
            # Iterate through candidates and take EXACT values
            for cand in const.get('candidates', []):
                rows.append({
                    "Constituency": c_name,
                    "Candidate": str(cand.get('name', 'Unknown')),
                    "Party": str(cand.get('party', 'No Data')), # Takes raw text from JSON
                    "Votes": int(cand.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Sync failed: {e}")
        return pd.DataFrame()

df = load_and_reflect_data()

# --- HEADER ---
st.title("🇳🇵 Nepal Election 2082 (2026) Live Tracker")
st.markdown("---")

if not df.empty:
    # 1. LIVE HIGHLIGHT: JHAPA-5 (Balen Shah vs KP Oli)
    # This automatically finds the candidates in Jhapa-5 regardless of party label
    jhapa_data = df[df['Constituency'].str.contains("Jhapa-5", case=False)].sort_values('Votes', ascending=False)
    
    if not jhapa_data.empty:
        st.subheader("🔥 Key Battle: Jhapa-5")
        cols = st.columns(min(len(jhapa_data), 3))
        for i in range(min(len(jhapa_data), 3)):
            row = jhapa_data.iloc[i]
            cols[i].metric(
                label=str(row['Candidate']), 
                value=f"{row['Votes']:,} 🗳️", 
                delta=str(row['Party']) # Shows exactly what's in the JSON 'party' field
            )

    # 2. NATIONAL SEAT TALLY
    # Logic: The party leading in each of the 165 FPTP seats
    st.divider()
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seat_tally = winners['Party'].value_counts().reset_index()
    seat_tally.columns = ['Party Name from Source', 'Seats Leading']

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("FPTP Seat Distribution")
        fig = px.bar(
            seat_tally, 
            x='Seats Leading', 
            y='Party Name from Source', 
            orientation='h',
            title="Leading Seats by Party (Raw Data Labels)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.write("### Live Leaderboard")
        st.dataframe(seat_tally, hide_index=True, use_container_width=True)

    # 3. FULL DATA TABLE (Transparency)
    st.divider()
    with st.expander("🔍 View/Search All Raw Candidate Data"):
        st.write("This table shows exactly what the JSON source is sending.")
        st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.info("🔄 Connecting to live data stream from Election Commission source...")

# --- SIDEBAR ---
st.sidebar.markdown(f"**Last Sync:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
