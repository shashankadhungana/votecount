import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from mapping import PARTY_BRANDING

st.set_page_config(page_title="Nepal Election 2082 Live", layout="wide")
st_autorefresh(interval=30000, key="nepal_full_sync")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

def get_party_info(raw_party_text):
    """Automatically matches any party text to our branding rules."""
    text = str(raw_party_text).lower()
    for official_name, meta in PARTY_BRANDING.items():
        if any(keyword in text for keyword in meta['keywords']):
            return official_name, meta['symbol'], meta['color']
    return raw_party_text, "🗳️", "#555555" # Returns raw text if no keyword match

@st.cache_data(ttl=5)
def fetch_all_candidates():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        all_rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            for cand in const.get('candidates', []):
                p_raw = cand.get('party', 'Independent')
                p_name, p_sym, p_color = get_party_info(p_raw)
                
                all_rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name', 'N/A'),
                    "Party": p_name,
                    "Symbol": p_sym,
                    "Color": p_color,
                    "Votes": int(cand.get('votes', 0))
                })
        return pd.DataFrame(all_rows)
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame()

df = fetch_all_candidates()

# --- THE INTERFACE ---
st.title("🇳🇵 Nepal Election 2082: All-Candidate Tracker")
st.write(f"**Total Candidates Tracked:** {len(df):,} | **Counting Status:** LIVE")

if not df.empty:
    # 1. THE BIG PICTURE (FPTP SEATS)
    st.divider()
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seat_tally = winners['Party'].value_counts().reset_index()
    seat_tally.columns = ['Party', 'Seats']

    col_map, col_list = st.columns([2, 1])
    with col_map:
        st.subheader("Leading in 165 Constituencies")
        fig = px.bar(seat_tally, x='Seats', y='Party', orientation='h', color='Party',
                     title="Current Seat Share (FPTP)")
        st.plotly_chart(fig, use_container_width=True)
    with col_list:
        st.dataframe(seat_tally, hide_index=True)

    # 2. THE SEARCH (Access "All" Candidates)
    st.divider()
    st.subheader("🔍 Search any Candidate or Constituency")
    query = st.text_input("Type name (e.g., Balen, Kathmandu, Gagan, Jhapa-5)")
    
    if query:
        search_results = df[df.apply(lambda x: query.lower() in str(x).lower(), axis=1)]
        st.dataframe(search_results.sort_values('Votes', ascending=False), use_container_width=True)
    else:
        # Show top 50 by default
        st.write("Top 50 Candidates by Votes:")
        st.dataframe(df.sort_values('Votes', ascending=False).head(50), use_container_width=True)

else:
    st.info("🔄 Processing Election Commission ballot data...")
