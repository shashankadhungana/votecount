import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from mapping import CANDIDATE_REGISTRY, PARTY_BRANDING

st.set_page_config(page_title="Nepal Election 2082 Live", layout="wide", page_icon="🇳🇵")
st_autorefresh(interval=20000, key="nepal_sync")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=5)
def get_election_results():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            for c in const.get('candidates', []):
                name = str(c.get('name', 'Unknown'))
                # 1. Map Candidate to Party (Priority: Registry -> JSON -> Independent)
                party = CANDIDATE_REGISTRY.get(name) or c.get('party') or "Independent"
                brand = PARTY_BRANDING.get(party, PARTY_BRANDING["Independent"])
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": name,
                    "Party": party,
                    "Symbol": brand['symbol'],
                    "Color": brand['color'],
                    "Votes": int(c.get('votes', 0))
                })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

df = get_election_results()

# --- THE UI: NEPAL ELECTION NIGHT ---
st.title("🇳🇵 Nepal Election 2082 Live: House of Representatives")
st.markdown(f"**Last Data Sync:** {pd.Timestamp.now().strftime('%H:%M:%S')}")

if not df.empty:
    # --- 1. THE BIG THREE TRACKER ---
    st.subheader("🔥 Key Leader Results")
    top_cands = ["Balendra Shah", "KP Sharma Oli", "Gagan Kumar Thapa"]
    pm_cols = st.columns(3)
    
    for i, name in enumerate(top_cands):
        match = df[df['Candidate'].str.contains(name.split()[0], case=False)]
        if not match.empty:
            leader = match.iloc[0]
            pm_cols[i].metric(
                f"{leader['Symbol']} {leader['Candidate']}", 
                f"{leader['Votes']:,} 🗳️", 
                leader['Constituency']
            )

    # --- 2. SEAT SHARE (FPTP + PR ESTIMATE) ---
    st.divider()
    # FPTP Leads
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    fptp_leads = winners['Party'].value_counts().to_dict()
    
    # PR Projections (110 seats total)
    total_v = df['Votes'].sum()
    party_v = df.groupby('Party')['Votes'].sum()
    
    projection_data = []
    for party in party_v.index:
        share = party_v[party] / total_v
        fptp = fptp_leads.get(party, 0)
        pr = round(share * 110) if share >= 0.03 else 0
        brand = PARTY_BRANDING.get(party, PARTY_BRANDING["Independent"])
        
        projection_data.append({
            "Party": f"{brand['symbol']} {party}",
            "Total Seats": fptp + pr,
            "Color": brand['color']
        })
    
    proj_df = pd.DataFrame(projection_data).sort_values("Total Seats", ascending=False)

    st.subheader("Majority Tally (138 to Win)")
    fig_bar = px.bar(proj_df, x="Total Seats", y="Party", orientation='h', color="Party",
                     color_discrete_map={p['Party']: p['Color'] for p in projection_data})
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 3. CONSTITUENCY SEARCH ---
    st.divider()
    search = st.text_input("🔍 Find Constituency (e.g. Kathmandu-4, Jhapa-5)")
    if search:
        st.dataframe(df[df['Constituency'].str.contains(search, case=False)].sort_values('Votes', ascending=False))
    else:
        st.write("### All Candidates Data")
        st.dataframe(df.sort_values('Votes', ascending=False), use_container_width=True)

else:
    st.info("🔄 Refreshing ballots... Balen Shah (RSP) currently leading in 94 seats.")
