import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Election Dashboard", page_icon="🗳️", layout="wide")

# Refresh every 30 seconds
st_autorefresh(interval=30000, key="datarefresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=30)
def load_data():
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # If data is a list of dicts, pandas can usually load it directly
        # or we might need to normalize it if it's nested.
        df = pd.json_normalize(data)
        
        # Standardizing column names (Edit these if your JSON keys are different!)
        # Map: 'json_key': 'Display Name'
        column_mapping = {
            'name': 'Constituency',
            'candidate_name': 'Candidate',
            'party_name': 'Party',
            'votes': 'Votes'
        }
        df = df.rename(columns=column_mapping)
        
        # Ensure Votes are numeric
        if 'Votes' in df.columns:
            df['Votes'] = pd.to_numeric(df['Votes'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR DEBUG ---
with st.sidebar:
    st.header("Settings")
    show_raw = st.checkbox("Show Raw Data (Debug)")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()

if show_raw:
    st.write("Raw JSON Data Structure:")
    st.json(requests.get(SOURCE_URL).json())

# --- MAIN DASHBOARD LOGIC ---
if not df.empty and 'Votes' in df.columns:
    # 1. Calculate Aggregates
    # Grouping by Candidate/Party to get national totals
    # (Adjust 'Candidate' or 'Party' based on what's in your JSON)
    group_col = 'Candidate' if 'Candidate' in df.columns else df.columns[0]
    national_totals = df.groupby(group_col)['Votes'].sum().reset_index().sort_values(by='Votes', ascending=False)
    
    # Safety check: ensure we have rows before calling .iloc[0]
    if len(national_totals) > 0:
        winner = national_totals.iloc[0]
        total_votes = national_totals['Votes'].sum()

        # 2. Top Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Leading", str(winner[group_col]))
        m2.metric("Total Votes", f"{total_votes:,.0f}")
        m3.metric("Data Points", len(df))

        # 3. Charts
        c1, c2 = st.columns([2, 1])
        
        with c1:
            fig = px.bar(national_totals, x='Votes', y=group_col, orientation='h', 
                         title="Votes by Candidate/Party", color='Votes',
                         color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.subheader("Leaderboard")
            st.dataframe(national_totals, hide_index=True, use_container_width=True)

        # 4. Detailed View
        st.divider()
        st.subheader("All Records")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Data loaded but no vote counts found in the expected format.")
else:
    st.error("Dashboard is empty. Please enable 'Show Raw Data' in the sidebar to inspect the JSON structure.")
