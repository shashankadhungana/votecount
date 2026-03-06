import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import hashlib
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
st.set_page_config(page_title="Nepal Live Election 2082", layout="wide")
st_autorefresh(interval=30000, key="auto_sync")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

# --- SMART DATA EXTRACTOR ---
def get_dynamic_color(name):
    """Generates a consistent color for any party name using its hash."""
    # Pre-defined colors for the giants of 2026
    known = {
        "RSP": "#00adef", "NC": "#ff0000", "UML": "#e21b22", 
        "MAOIST": "#dd0000", "RPP": "#ffcc00", "SSP": "#4B0082"
    }
    name_upper = str(name).upper()
    for k, v in known.items():
        if k in name_upper: return v
    # If unknown, generate a color from the string itself
    return "#" + hashlib.md5(name_upper.encode()).hexdigest()[:6]

@st.cache_data(ttl=5)
def load_and_extract_logic():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        
        extracted_rows = []
        for entry in data:
            constituency = entry.get('name') or entry.get('constituency') or "Unknown"
            # Find the candidates list regardless of the key name
            cands_key = next((k for k in entry.keys() if isinstance(entry[k], list)), None)
            
            if cands_key:
                for cand in entry[cands_key]:
                    # AUTOMATICALLY detect fields for party, name, and votes
                    p_val = next((v for k, v in cand.items() if 'party' in k.lower() or 'group' in k.lower()), "Independent")
                    n_val = next((v for k, v in cand.items() if 'name' in k.lower() or 'cand' in k.lower()), "N/A")
                    v_val = next((v for k, v in cand.items() if 'vote' in k.lower() or 'count' in k.lower()), 0)
                    
                    extracted_rows.append({
                        "Constituency": constituency,
                        "Candidate": n_val,
                        "Party": str(p_val).strip(),
                        "Votes": int(v_val),
                        "Color": get_dynamic_color(p_val)
                    })
        return pd.DataFrame(extracted_rows)
    except Exception as e:
        st.error(f"Sync failed: {e}")
        return pd.DataFrame()

df = load_and_extract_logic()

# --- DYNAMIC UI ---
st.title("🇳🇵 Nepal Election 2082: Auto-Data Dashboard")

if not df.empty:
    # 1. LIVE SUMMARY
    # Extract ALL parties found in the data
    found_parties = df['Party'].unique()
    
    # 2. FPTP SEAT LEADS (Dynamic)
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seat_tally = winners['Party'].value_counts().reset_index()
    seat_tally.columns = ['Party', 'Seats']
    
    # 3. TOP BATTLE: Jhapa-5 (Auto-extracted)
    jhapa = df[df['Constituency'].str.contains("Jhapa-5", case=False)].sort_values('Votes', ascending=False)
    if not jhapa.empty:
        st.subheader("🔥 Top Contest: Jhapa-5")
        cols = st.columns(min(len(jhapa), 3))
        for i, (_, row) in enumerate(jhapa.head(len(cols)).iterrows()):
            cols[i].metric(row['Candidate'], f"{row['Votes']:,} 🗳️", f"{row['Party']}")

    # 4. NATIONAL CHART (No hardcoded parties)
    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("National Seat Distribution (FPTP)")
        # Map colors dynamically based on the labels actually in the chart
        current_colors = {p: get_dynamic_color(p) for p in seat_tally['Party']}
        fig = px.bar(seat_tally, x='Seats', y='Party', orientation='h', color='Party',
                     color_discrete_map=current_colors)
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.write("### Live Party Tally")
        st.dataframe(seat_tally, hide_index=True)

    # 5. ALL LIVE DATA
    st.divider()
    with st.expander("🔍 Browse All Constituencies and Parties"):
        st.write("Parties detected in current stream:", ", ".join(found_parties))
        st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.info("🔄 Checking data stream for candidates and parties...")

st.sidebar.markdown(f"**Last Data Pull:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
