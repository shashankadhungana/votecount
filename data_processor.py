import requests
import streamlit as st
import time

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=30) # High frequency cache for live results
def fetch_live_data():
    """Fetches raw JSON data with enhanced error handling and timeout."""
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        st.sidebar.error(f"Data Fetch Failed: {e}")
        return []

def process_election_data(raw_data):
    """Processes raw JSON into validated UI components with proper symbol mapping."""
    parties_list = []
    featured_list = []
    hot_seats_list = []

    if not raw_data:
        return [], [], []

    # Official 2082 (2026) Party Mappings
    party_meta = {
        "Nepali Congress": {"symbol": "🌳", "color": "#28a745"},
        "CPN (UML)": {"symbol": "☀️", "color": "#dc3545"},
        "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#007bff"},
        "CPN (Maoist Centre)": {"symbol": "☭", "color": "#c82333"},
        "RPP": {"symbol": "🚜", "color": "#ffc107"},
        "Janmat Party": {"symbol": "📢", "color": "#fd7e14"},
        "Nagarik Unmukti Party": {"symbol": "🏠", "color": "#6f42c1"},
        "Independent": {"symbol": "🔲", "color": "#6c757d"}
    }

    # 1. Aggregate Party Stats
    counts = {}
    for item in raw_data:
        p_name = item.get('leading_party', 'Independent')
        counts[p_name] = counts.get(p_name, 0) + 1

    for name, leads in counts.items():
        meta = party_meta.get(name, party_meta["Independent"])
        parties_list.append({
            "name": name,
            "symbol": meta["symbol"],
            "leads": leads,
            "color": meta["color"]
        })

    # 2. Extract Clash Cards (Famous Leaders / High Demand)
    # We check for substring matches for major names
    stars = ["balen", "gagan", "rabi", "oli", "deuba", "kulman", "ck raut"]
    
    for item in raw_data:
        cands = item.get('candidates', [])
        if len(cands) < 1: continue
        
        c1 = cands[0]
        c2 = cands[1] if len(cands) > 1 else {}
        
        c1_name = str(c1.get('name', '')).lower()
        c2_name = str(c2.get('name', '')).lower()
        
        if any(star in c1_name or star in c2_name for star in stars):
            featured_list.append({
                "constituency": item.get('name', 'N/A'),
                "c1": {
                    "name": c1.get('name', 'N/A'),
                    "party": c1.get('party', 'IND'),
                    "votes": c1.get('votes', 0),
                    "symbol": party_meta.get(c1.get('party'), party_meta["Independent"])["symbol"]
                },
                "c2": {
                    "name": c2.get('name', 'N/A'),
                    "party": c2.get('party', 'IND'),
                    "votes": c2.get('votes', 0),
                    "symbol": party_meta.get(c2.get('party'), party_meta["Independent"])["symbol"]
                }
            })

    # 3. Detect Hot Seats (Margins < 1500)
    for item in raw_data:
        cands = item.get('candidates', [])
        if len(cands) >= 2:
            try:
                v1 = int(cands[0].get('votes', 0))
                v2 = int(cands[1].get('votes', 0))
                margin = abs(v1 - v2)
                if margin < 1500:
                    hot_seats_list.append({
                        "area": item.get('name', 'Unknown'),
                        "leading": cands[0].get('name', 'N/A'),
                        "margin": margin,
                        "party": cands[0].get('party', 'IND')
                    })
            except: continue

    return parties_list, featured_list[:6], sorted(hot_seats_list, key=lambda x: x['margin'])[:10]