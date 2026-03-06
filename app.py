import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
st.set_page_config(page_title="Election Live 2026", page_icon="🗳️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

def flatten_json(data):
    """
    Deep-flattens nested election JSON (Constituencies -> Candidates).
    """
    rows = []
    if isinstance(data, list):
        for item in data:
            # Check if this item has a sub-list (like 'candidates')
            base_info = {k: v for k, v in item.items() if not isinstance(v, (list, dict))}
            
            # Look for the nested list
            nested_list_key = next((k for k, v in item.items() if isinstance(v, list)), None)
            
            if nested_list_key:
                for sub_item in item[nested_list_key]:
                    new_row = base_info.copy()
                    new_row.update(sub_item)
                    rows.append(new_row)
            else:
                rows.append(base_info)
    return pd.DataFrame(rows)

@st.cache_data(ttl=10)
def load_and_clean_data():
    try:
        r = requests.get(SOURCE_URL, timeout=10)
        r.raise_for_status()
        raw_json = r.json()
        
        df = flatten_json(raw_json)
        
        # Standardize column names to lowercase for logic
        df.columns = [str(c).lower() for c in df.columns]
        
        # Identify columns dynamically
        v_col = next((c for c in df.columns if 'vote' in c or 'count' in c), None)
        n_col = next((c for c in df.columns if 'candidate' in c or 'name' in c), None)
        
        if v_col:
            df[v_col] = pd.to_numeric(df[v_col], errors='coerce').fillna(0)
            
        return df, v_col, n_col
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame(), None, None

df, vote_col, name_col = load_and_clean_data()

# --- DASHBOARD UI ---
st.title("🗳️ Election 2026 Live Tracker")

if not df.empty and vote_col and name_col:
    # 1. TOP STATS
    total_votes = df[vote_col].sum()
    # Handle duplicates in names by grouping
    summary = df.groupby(name_col)[vote_col].sum().reset_index().sort_values(by=vote_col, ascending=False)
    
    m1, m2, m3 = st.columns(3)
    if not summary.empty:
        winner = summary.iloc[0]
        m1.metric("Leading Candidate", str(winner[name_col]))
        m2.metric("Total Votes Counted", f"{total_votes:,.0f}")
        m3.metric("Reporting Areas", len(df[df.columns[0]].unique()))

    # 2. VISUALS
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Results Overview")
        fig = px.bar(summary, x=vote_col, y=name_col, orientation='h', 
                     color=vote_col, color_continuous_scale='RdBu')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
    with col_right:
        st.subheader("Leaderboard")
        st.dataframe(summary, hide_index=True, use_container_width=True)

    # 3. FULL DATA
    with st.expander("Search Detailed Results"):
        search = st.text_input("Filter by Candidate or Constituency")
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            st.write(df[mask])
        else:
            st.write(df)
else:
    st.info("🔄 Processing data stream... If this persists, verify the JSON format in the sidebar.")
    with st.sidebar:
        if st.checkbox("Debug: View Raw JSON"):
            st.json(requests.get(SOURCE_URL).json())
