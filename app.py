import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Live Election Dashboard",
    page_icon="🗳️",
    layout="wide"
)

# Refresh every 60 seconds
st_autorefresh(interval=60000, key="datarefresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=60) # Cache for 60 seconds to save bandwidth
def load_data():
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        data = response.json()
        
        # Flattening the data (Assuming standard Election JSON structure)
        # We look for a list of constituencies and their candidates
        rows = []
        for constituency in data:
            const_name = constituency.get('name', 'Unknown')
            region = constituency.get('region', 'N/A')
            for candidate in constituency.get('candidates', []):
                rows.append({
                    "Constituency": const_name,
                    "Region": region,
                    "Candidate": candidate.get('name'),
                    "Party": candidate.get('party'),
                    "Votes": candidate.get('votes', 0),
                    "Status": candidate.get('status', 'Pending')
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Error loading live data: {e}")
        return pd.DataFrame()

df = load_data()

# --- HEADER ---
st.title("🗳️ Real-Time Election Results")
if not df.empty:
    total_votes = df['Votes'].sum()
    st.markdown(f"**Total Votes Counted:** {total_votes:,} | **Last Updated:** {pd.Timestamp.now().strftime('%H:%M:%S')}")
    st.divider()

    # --- TOP METRICS ---
    # Aggregate data for national view
    party_totals = df.groupby('Party')['Votes'].sum().reset_index().sort_values(by='Votes', ascending=False)
    leading_party = party_totals.iloc[0]

    m1, m2, m3 = st.columns(3)
    m1.metric("Leading Party", leading_party['Party'])
    m2.metric("Leader Vote Count", f"{leading_party['Votes']:,}")
    m3.metric("Constituencies Reported", f"{df['Constituency'].nunique()}")

    # --- CHARTS ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Vote Share by Party")
        fig_bar = px.bar(
            party_totals, 
            x='Votes', 
            y='Party', 
            orientation='h',
            color='Party',
            text_auto=',.0f',
            title="National Vote Standings"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("Top 5 Candidates")
        top_5 = df.sort_values(by='Votes', ascending=False).head(5)
        st.table(top_5[['Candidate', 'Votes', 'Party']])

    # --- DRILL DOWN ---
    st.divider()
    st.subheader("Search by Constituency")
    selected_const = st.selectbox("Select a Region/Constituency", df['Constituency'].unique())
    
    const_data = df[df['Constituency'] == selected_const]
    
    col_a, col_b = st.columns(2)
    with col_a:
        fig_pie = px.pie(const_data, values='Votes', names='Candidate', title=f"Results for {selected_const}")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_b:
        st.dataframe(const_data[['Candidate', 'Party', 'Votes', 'Status']], hide_index=True, use_container_width=True)

else:
    st.warning("Waiting for data stream... Please check the SOURCE_URL connection.")

# --- SIDEBAR ---
st.sidebar.header("Dashboard Controls")
if st.sidebar.button("Force Data Refresh"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("""
---
**Note:** This dashboard pulls live data from Cloudflare R2 storage. 
Data is updated automatically every minute.
""")
