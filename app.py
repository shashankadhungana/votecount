import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- ROBUST NEPAL PARTY CONFIG ---
# We add every possible variation of the name to prevent "Independent" bug
PARTY_MAP = {
    "Rastriya Swatantra Party": ["rsp", "bell", "swatantra party", "घण्टी"],
    "Nepali Congress": ["nc", "congress", "रुख", "tree"],
    "CPN (UML)": ["uml", "sun", "सूर्य", "cpn uml"],
    "CPN (Maoist Centre)": ["maoist", "center", "dahal", "माओवादी"],
    "Rastriya Prajatantra Party": ["rpp", "plough", "lingden", "हलो"],
    "Janamat Party": ["janamat", "raut", "horn"],
    "Nagarik Unmukti Party": ["nup", "dhrishita", "civil liberation"]
}

# The colors and symbols associated with the keys above
PARTY_DETAILS = {
    "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#00adef"},
    "Nepali Congress": {"symbol": "🌳", "color": "#ff0000"},
    "CPN (UML)": {"symbol": "☀️", "color": "#e21b22"},
    "CPN (Maoist Centre)": {"symbol": "☭", "color": "#dd0000"},
    "Rastriya Prajatantra Party": {"symbol": "🚜", "color": "#ffcc00"},
    "Janamat Party": {"symbol": "📢", "color": "#00ff00"},
    "Independent": {"symbol": "👤", "color": "#808080"}
}

def identify_party(raw_name):
    """
    Cleans and matches the party name from JSON to our database.
    """
    name = str(raw_name).lower().strip()
    
    for official_name, variations in PARTY_MAP.items():
        if any(v in name for v in variations):
            return official_name
    
    return "Independent" # Default if no keywords match

# --- UPDATED DATA LOADING ---
@st.cache_data(ttl=10)
def load_and_fix_data():
    try:
        r = requests.get("https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json", timeout=10)
        data = r.json()
        rows = []
        for const in data:
            c_name = const.get('name', 'Unknown')
            for cand in const.get('candidates', []):
                # IMPORTANT: We identify the party here!
                party_label = identify_party(cand.get('party', 'Independent'))
                meta = PARTY_DETAILS.get(party_label, PARTY_DETAILS["Independent"])
                
                rows.append({
                    "Constituency": c_name,
                    "Candidate": cand.get('name', 'N/A'),
                    "Party": party_label,
                    "Symbol": meta['symbol'],
                    "Votes": int(cand.get('votes', 0)),
                    "Color": meta['color']
                })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

df = load_and_fix_data()

# --- DISPLAY LOGIC ---
st.title("🇳🇵 Nepal Election Live (Fixed Party Detection)")

if not df.empty:
    # Party-wise Seat Count (Winner in each constituency)
    winners = df.sort_values(['Constituency', 'Votes'], ascending=[True, False]).drop_duplicates('Constituency')
    seats = winners['Party'].value_counts().reset_index()
    seats.columns = ['Party', 'Seats']
    
    # Apply Meta to Seat Table
    seats['Symbol'] = seats['Party'].apply(lambda x: PARTY_DETAILS.get(x, PARTY_DETAILS['Independent'])['symbol'])
    
    st.subheader("Live Seat Tally (FPTP)")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Visualizing with Correct Colors
        color_map = {p: PARTY_DETAILS.get(p, PARTY_DETAILS['Independent'])['color'] for p in seats['Party']}
        fig = px.bar(seats, x='Seats', y='Party', orientation='h', color='Party', color_discrete_map=color_map)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.dataframe(seats[['Symbol', 'Party', 'Seats']], hide_index=True)
else:
    st.error("Could not load data. Check if your JSON URL is public.")
