import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- SETUP ---
st.set_page_config(page_title="Nepal Election 2082 Live", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_live_sync")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# --- OFFICIAL PARTY REGISTRY ---
# We use the exact abbreviations expected in the 2026 cycle
OFFICIAL_PARTIES = {
    "RSP": {"name": "Rastriya Swatantra Party", "color": "#00adef", "symbol": "🔔"},
    "NC": {"name": "Nepali Congress", "color": "#ff0000", "symbol": "🌳"},
    "UML": {"name": "CPN (UML)", "color": "#e21b22", "symbol": "☀️"},
    "NCP": {"name": "Nepali Communist Party", "color": "#dd0000", "symbol": "⭐"},
    "RPP": {"name": "Rastriya Prajatantra Party", "color": "#ffcc00", "symbol": "🚜"},
    "SSP": {"name": "Shram Sanskriti Party", "color": "#4B0082", "symbol": "⚒️"}
}

def get_party_details(raw_party_code):
    """Zero-logic mapping: Returns official info or the raw string itself."""
    code = str(raw_party_code).strip().upper()
    if code in OFFICIAL_PARTIES:
        return OFFICIAL_PARTIES[code]
    # If not in our list, return the raw data with a default color
    return {"name": code, "color": "#555555", "symbol": "🗳️"}

@st.cache_data(ttl=5)
def load_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            for cand in const.get('candidates', []):
                p_code = cand.get('party', 'UNKNOWN')
                details = get_party_details(p_code)
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name', 'N/A'),
                    "Party": details['name'],
                    "Symbol": details['symbol'],
                    "Color": details['color'],
                    "Votes": int(cand.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- THE UI ---
st.title("🇳🇵 Nepal House of Representatives Election 2082")
st.markdown("### First-Past-The-Post (FPTP) Live Tracker")

if not df.empty:
    # 1. TOP HIGHLIGHT: JHAPA-5 (Balen vs Oli)
    st.divider()
    jhapa = df[df['Constituency'] == "Jhapa-5"].sort_values('Votes', ascending=False)
    if not jhapa.empty:
        st.subheader("🔥 Key Battle: Jhapa-5")
        cols = st.columns(len(jhapa.head(3)))
        for i, (_, row) in enumerate(jhapa.head(3).iterrows()):
            cols[i].metric(
                label=f"{row['Symbol']} {row['Candidate']}",
                value=f"{row['Votes']:,} 🗳️",
                delta=row['Party']
            )

    # 2. NATIONAL SEAT COUNT
    st.divider()
    # Logic: Get the leader of every single constituency
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seat_tally = winners.groupby('Party').size().reset_index(name='Seats').sort_values('Seats', ascending=False)

    col_main, col_side = st.columns([2, 1])
    with col_main:
        st.subheader("Current Leading Seats (National)")
        fig = px.bar(
            seat_tally, x='Seats', y='Party', orientation='h', 
            color='Party', color_discrete_map={row['Party']: get_party_details(row['Party'])['color'] for _, row in seat_tally.iterrows()}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_side:
        st.write("### Tally Table")
        st.dataframe(seat_tally, hide_index=True, use_container_width=True)

    # 3. LIVE SEARCH
    st.divider()
    with st.expander("🔍 Search All 165 Constituencies"):
        search = st.text_input("Enter Constituency or Candidate Name")
        if search:
            st.write(df[df.apply(lambda x: search.lower() in str(x).lower(), axis=1)])
        else:
            st.write(df.sort_values('Votes', ascending=False))

else:
    st.info("🔄 Connecting to live data stream...")

# --- FOOTER ---
st.sidebar.markdown(f"**Last Update:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
if st.sidebar.button("Force Clear Cache"):
    st.cache_data.clear()
    st.rerun()
