import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- NEPAL PARTY CONFIGURATION ---
PARTY_META = {
    "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#00adef", "alias": "RSP"},
    "Nepali Congress": {"symbol": "🌳", "color": "#ff0000", "alias": "NC"},
    "CPN (UML)": {"symbol": "☀️", "color": "#e21b22", "alias": "UML"},
    "Nepal Communist Party": {"symbol": "⭐", "color": "#dd0000", "alias": "NCP"},
    "Rastriya Prajatantra Party": {"symbol": "🚜", "color": "#ffcc00", "alias": "RPP"},
    "Ujyalo Nepal Party": {"symbol": "💡", "color": "#f9d71c", "alias": "UNP"},
    "Janamat Party": {"symbol": "📢", "color": "#00ff00", "alias": "Janamat"},
    "Independent": {"symbol": "👤", "color": "#808080", "alias": "IND"}
}

def get_party_info(party_name):
    # Matches name or tries to find a partial match
    for p, meta in PARTY_META.items():
        if p.lower() in str(party_name).lower():
            return meta
    return {"symbol": "🗳️", "color": "#333333", "alias": "Other"}

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nepal Election 2026 Live", page_icon="🇳🇵", layout="wide")
st_autorefresh(interval=30000, key="nepal_refresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

def flatten_nepal_data(data):
    rows = []
    # Assumes structure: [ { name: "Jhapa-5", candidates: [...] }, ... ]
    for const in data:
        c_name = const.get('name', 'Unknown')
        for cand in const.get('candidates', []):
            p_name = cand.get('party', 'Independent')
            meta = get_party_info(p_name)
            rows.append({
                "Constituency": c_name,
                "Candidate": cand.get('name', 'N/A'),
                "Party": p_name,
                "Symbol": meta['symbol'],
                "Votes": int(cand.get('votes', 0)),
                "Color": meta['color']
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=10)
def load_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        return flatten_nepal_data(r.json())
    except:
        return pd.DataFrame()

df = load_data()

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🇳🇵 Nepal Election 2026 Live Results</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>Last Update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)

if not df.empty:
    # 1. TOP STATS
    party_summary = df.groupby('Party')['Votes'].sum().reset_index().sort_values('Votes', ascending=False)
    total_v = df['Votes'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Votes Polled", f"{total_v:,}")
    with col2:
        top_p = party_summary.iloc[0]
        st.metric("Leading Party", f"{get_party_info(top_p['Party'])['symbol']} {top_p['Party']}")
    with col3:
        st.metric("Reporting Constituencies", df['Constituency'].nunique())

    # 2. MAIN VISUALS
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("National Vote Standings")
        fig = px.bar(party_summary, x='Votes', y='Party', orientation='h',
                     color='Party', color_discrete_map={p: m['color'] for p, m in PARTY_META.items()})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Top Candidates")
        top_cands = df.sort_values('Votes', ascending=False).head(10)
        # Add symbol to name for display
        top_cands['Display'] = top_cands['Symbol'] + " " + top_cands['Candidate']
        st.table(top_cands[['Display', 'Votes', 'Constituency']])

    # 3. DRILL DOWN
    st.divider()
    st.subheader("Find Your Constituency")
    selected = st.selectbox("Search (e.g., Kathmandu-4, Jhapa-5)", sorted(df['Constituency'].unique()))
    
    const_df = df[df['Constituency'] == selected].sort_values('Votes', ascending=False)
    
    # Show winner card for constituency
    winner = const_df.iloc[0]
    st.info(f"🏆 **Current Leader in {selected}:** {winner['Symbol']} {winner['Candidate']} ({winner['Party']}) with {winner['Votes']:,} votes")
    st.table(const_df[['Candidate', 'Party', 'Symbol', 'Votes']])

else:
    st.warning("Data is currently loading or source is unreachable. Please check back in a few moments.")

# --- FOOTER ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/2/23/Flag_of_Nepal.svg", width=100)
st.sidebar.markdown("""
### 2026 Election Guide
* **NC:** Tree (रुख)
* **UML:** Sun (सूर्य)
* **RSP:** Bell (घण्टी)
* **RPP:** Plough (हलो)
* **UNP:** Bulb (बत्ती)
""")
