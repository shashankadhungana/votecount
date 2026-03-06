import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
st.set_page_config(page_title="Nepal Election 2082 Live", layout="wide")
st_autorefresh(interval=30000, key="nepal_final")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=5)
def fetch_live_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for entry in data:
            const_name = str(entry.get('name', 'Unknown'))
            # Look for the list of candidates inside each constituency
            candidates = entry.get('candidates', [])
            for c in candidates:
                # Sanitization: Ensure NO values are None
                cand_name = str(c.get('name', 'Unknown Candidate'))
                party_val = str(c.get('party', 'Independent'))
                vote_count = c.get('votes', 0)
                
                try:
                    vote_count = int(vote_count)
                except:
                    vote_count = 0
                
                rows.append({
                    "Constituency": const_name,
                    "Candidate": cand_name,
                    "Party": party_val,
                    "Votes": vote_count
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame()

df = fetch_live_data()

# --- DASHBOARD UI ---
st.title("🇳🇵 Nepal House of Representatives Election 2082")
st.markdown("### First-Past-The-Post (FPTP) Live Tracker")

if not df.empty:
    # 1. THE BIG RACE: JHAPA-5 (Balen Shah vs KP Oli)
    # We find this dynamically from the data
    jhapa = df[df['Constituency'].str.contains("Jhapa-5", case=False)].sort_values('Votes', ascending=False)
    
    if not jhapa.empty:
        st.divider()
        st.subheader("🔥 Key Battle: Jhapa-5")
        # Ensure we only create columns if candidates exist
        display_count = min(len(jhapa), 3)
        cols = st.columns(display_count)
        for i in range(display_count):
            row = jhapa.iloc[i]
            # FIX: Ensure label is always a string
            label_text = str(row['Candidate'])
            val_text = f"{int(row['Votes']):,} 🗳️"
            delta_text = str(row['Party'])
            cols[i].metric(label_text, val_text, delta_text)

    # 2. NATIONAL SEAT TALLY
    st.divider()
    # To find winners: group by constituency and pick the candidate with max votes
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seat_tally = winners['Party'].value_counts().reset_index()
    seat_tally.columns = ['Party', 'Seats']

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("National Seat Distribution")
        fig = px.bar(seat_tally, x='Seats', y='Party', orientation='h', color='Party',
                     title="Seats Leading (FPTP)")
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.write("### Live Leaderboard")
        st.dataframe(seat_tally, hide_index=True, use_container_width=True)

    # 3. LIVE SEARCH
    st.divider()
    with st.expander("🔍 Search and Filter Results"):
        query = st.text_input("Search Candidate, Party or Constituency")
        if query:
            filtered = df[df.apply(lambda x: query.lower() in str(x).lower(), axis=1)]
            st.dataframe(filtered.sort_values('Votes', ascending=False), use_container_width=True)
        else:
            st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.info("🔄 Connecting to live election stream. Please wait...")

# --- FOOTER ---
st.sidebar.markdown(f"**Last Sync:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
