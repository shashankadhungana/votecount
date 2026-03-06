import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Election Dashboard", page_icon="🗳️", layout="wide")

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="datarefresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=10)
def load_data():
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # If the data is nested (e.g., a list within a list), normalize it
        df = pd.json_normalize(data)
        
        # Convert all column names to lowercase for easier matching
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = load_data()

# --- DYNAMIC COLUMN DETECTOR ---
# This part finds which columns are 'Votes', 'Name', and 'Party' automatically
def find_col(possible_names, df):
    for name in possible_names:
        for col in df.columns:
            if name in col:
                return col
    return None

vote_col = find_col(['vote', 'count', 'total'], df)
name_col = find_col(['candidate', 'name', 'person'], df)
party_col = find_col(['party', 'group', 'affiliation'], df)
const_col = find_col(['constituency', 'area', 'region', 'district'], df)

# --- DASHBOARD UI ---
st.title("🗳️ Election Live Results")

if not df.empty and vote_col:
    # Ensure votes are numeric
    df[vote_col] = pd.to_numeric(df[vote_col], errors='coerce').fillna(0)
    
    # 1. TOTAL METRICS
    total_votes = df[vote_col].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Votes Counted", f"{total_votes:,.0f}")
    
    if name_col:
        # Grouping by candidate to get national totals
        summary = df.groupby(name_col)[vote_col].sum().reset_index().sort_values(by=vote_col, ascending=False)
        leader = summary.iloc[0]
        m2.metric("Current Leader", str(leader[name_col]))
        m3.metric("Lead Margin", f"{leader[vote_col]:,.0f}")

        # 2. NATIONAL CHART
        st.subheader("National Vote Standings")
        fig = px.bar(summary, x=vote_col, y=name_col, orientation='h', 
                     color=vote_col, color_continuous_scale='Viridis',
                     text_auto='.2s')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # 3. CONSTITUENCY DRILL-DOWN
    if const_col:
        st.divider()
        st.subheader("Results by Constituency")
        selected = st.selectbox("Select Area", sorted(df[const_col].unique()))
        area_df = df[df[const_col] == selected].sort_values(by=vote_col, ascending=False)
        st.table(area_df[[name_col, party_col, vote_col]] if party_col in area_df.columns else area_df[[name_col, vote_col]])

    # 4. DATA TABLE
    with st.expander("View Raw Data Table"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Connected to source, but could not find a 'Votes' column in the data.")
    st.write("Current Columns found:", list(df.columns))
    st.write("Preview of data:", df.head())

# --- SIDEBAR ---
st.sidebar.info(f"Connected to: {SOURCE_URL.split('/')[-1]}")
if st.sidebar.button("Clear Cache & Reload"):
    st.cache_data.clear()
    st.rerun()
