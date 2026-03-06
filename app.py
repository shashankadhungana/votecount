import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- NEPAL ELECTION SETTINGS ---
TOTAL_FPTP_SEATS = 165
TOTAL_PR_SEATS = 110
MAJORITY_MARK = 138

PARTY_META = {
    "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#00adef", "alias": "RSP"},
    "Nepali Congress": {"symbol": "🌳", "color": "#ff0000", "alias": "NC"},
    "CPN (UML)": {"symbol": "☀️", "color": "#e21b22", "alias": "UML"},
    "CPN (Maoist Centre)": {"symbol": "☭", "color": "#dd0000", "alias": "Maoist"},
    "Rastriya Prajatantra Party": {"symbol": "🚜", "color": "#ffcc00", "alias": "RPP"},
    "Independent": {"symbol": "👤", "color": "#808080", "alias": "IND"}
}

st.set_page_config(page_title="Nepal 2026: Seat Projection", layout="wide")
st_autorefresh(interval=30000, key="projection_refresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=10)
def load_and_project():
    try:
        r = requests.get(SOURCE_URL)
        data = r.json()
        
        # 1. Process FPTP (Leading in each constituency)
        fptp_rows = []
        for const in data:
            c_name = const.get('name')
            cands = sorted(const.get('candidates', []), key=lambda x: x['votes'], reverse=True)
            if cands:
                fptp_rows.append({
                    "Constituency": c_name,
                    "Leader": cands[0]['name'],
                    "Party": cands[0]['party'],
                    "Votes": cands[0]['votes']
                })
        
        fptp_df = pd.DataFrame(fptp_rows)
        fptp_leads = fptp_df['Party'].value_counts().to_dict()

        # 2. Process PR (Based on total national vote share)
        # In Nepal, PR seats are allocated if party gets >3% vote
        all_cands = []
        for const in data: all_cands.extend(const.get('candidates', []))
        
        votes_df = pd.DataFrame(all_cands)
        total_votes = votes_df['votes'].sum()
        party_votes = votes_df.groupby('party')['votes'].sum()
        
        pr_projections = {}
        for party, v in party_votes.items():
            share = v / total_votes
            if share >= 0.03: # 3% Threshold
                pr_projections[party] = round(share * TOTAL_PR_SEATS)
        
        return fptp_leads, pr_projections, total_votes
    except:
        return {}, {}, 0

fptp_leads, pr_leads, total_v = load_and_project()

# --- UI: THE RACE TO 138 ---
st.title("🗳️ Nepal 2026: The Race to 138")
st.subheader("Combined FPTP Leads + PR Projections")

# Combine Data
all_parties = set(list(fptp_leads.keys()) + list(pr_leads.keys()))
projection_data = []

for p in all_parties:
    f = fptp_leads.get(p, 0)
    r = pr_leads.get(p, 0)
    meta = PARTY_META.get(p, {"symbol": "🗳️", "color": "#333333"})
    projection_data.append({
        "Party": f"{meta['symbol']} {p}",
        "FPTP Leads": f,
        "PR Projected": r,
        "Total Projected": f + r,
        "Color": meta['color']
    })

proj_df = pd.DataFrame(projection_data).sort_values("Total Projected", ascending=False)

# 1. MAJORITY PROGRESS BAR (The "Wick" Chart)
st.write("### Majority Progress")
for _, row in proj_df.head(4).iterrows():
    cols = st.columns([1, 4])
    cols[0].write(f"**{row['Party']}**")
    progress = min(row['Total Projected'] / MAJORITY_MARK, 1.0)
    cols[1].progress(progress, text=f"{row['Total Projected']} / 138 seats")

# 2. SEAT DISTRIBUTION CHART
st.divider()
fig = px.bar(proj_df, x="Party", y=["FPTP Leads", "PR Projected"], 
             title="Projected Seat Composition",
             color_discrete_sequence=["#004d99", "#66b3ff"])
st.plotly_chart(fig, use_container_width=True)

# 3. DETAILED TABLE
st.subheader("Live Seat Tally")
st.table(proj_df[["Party", "FPTP Leads", "PR Projected", "Total Projected"]])

st.sidebar.markdown(f"""
### Election Stats
- **Total Votes:** {total_v:,}
- **FPTP Counted:** {len(fptp_leads)} / 165
- **PR Threshold:** 3.0%
---
*Projections are based on live vote-share trends and subject to change as more rural ballots are opened.*
""")
