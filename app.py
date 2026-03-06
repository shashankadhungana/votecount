import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from mapping import CANDIDATE_REGISTRY, PARTY_BRANDING

st.set_page_config(page_title="Nepal Votes 2082 Live", layout="wide", page_icon="🇳🇵")
st_autorefresh(interval=30000, key="nepal_sync")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=5)
def get_live_results():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = str(const.get('name', 'Unknown'))
            for c in const.get('candidates', []):
                cand_name = str(c.get('name', 'Unknown'))
                
                # DATA MAPPING LOGIC
                # 1. Look up candidate in our registry
                # 2. Fallback to raw JSON party
                # 3. Last resort: "Independent"
                mapped_party = CANDIDATE_REGISTRY.get(cand_name) or c.get('party') or "Independent"
                brand = PARTY_BRANDING.get(mapped_party, PARTY_BRANDING["Independent"])
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand_name,
                    "Party": mapped_party,
                    "Symbol": brand['symbol'],
                    "Color": brand['color'],
                    "Votes": int(c.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

df = get_live_results()

# --- THE LIVE INTERFACE ---
st.title("🇳🇵 Nepal Election 2082 Live Dashboard")
st.info("Election Date: March 5, 2026 | Counting Status: LIVE")

if not df.empty:
    # 1. STAR CONTESTS (AUTO-MAPPED)
    st.subheader("🔥 High-Stakes Battlegrounds")
    col1, col2, col3 = st.columns(3)
    
    # Jhapa-5: Balen vs Oli
    jhapa = df[df['Constituency'] == "Jhapa-5"].sort_values('Votes', ascending=False)
    if not jhapa.empty:
        top = jhapa.iloc[0]
        col1.metric(f"{top['Symbol']} {top['Candidate']}", f"{top['Votes']:,} 🗳️", f"Leading in Jhapa-5")

    # Sarlahi-4: Amresh Singh vs Gagan Thapa
    sarlahi = df[df['Constituency'] == "Sarlahi-4"].sort_values('Votes', ascending=False)
    if not sarlahi.empty:
        top_s = sarlahi.iloc[0]
        col2.metric(f"{top_s['Symbol']} {top_s['Candidate']}", f"{top_s['Votes']:,} 🗳️", f"Leading in Sarlahi-4")

    # Kathmandu-1: Ranju Neupane
    ktm1 = df[df['Constituency'] == "Kathmandu-1"].sort_values('Votes', ascending=False)
    if not ktm1.empty:
        top_k = ktm1.iloc[0]
        col3.metric(f"{top_k['Symbol']} {top_k['Candidate']}", f"{top_k['Votes']:,} 🗳️", f"Leading in Kathmandu-1")

    # 2. SEAT SHARE SUMMARY
    st.divider()
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seats = winners['Party'].value_counts().reset_index()
    seats.columns = ['Party', 'FPTP Leads']

    # Apply colors
    colors = {p: PARTY_BRANDING.get(p, PARTY_BRANDING["Independent"])['color'] for p in seats['Party']}
    fig = px.bar(seats, x='FPTP Leads', y='Party', color='Party', orientation='h', color_discrete_map=colors)
    st.plotly_chart(fig, use_container_width=True)

    # 3. FULL CANDIDATE DATA SHEET
    st.divider()
    with st.expander("🔍 Full Candidate & Party Datasheet"):
        st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.warning("🔄 Fetching live stream from Election Commission...")
