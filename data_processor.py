import requests
import streamlit as st
import time

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=30)
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

def get_party_meta(party_name):
    """Returns official symbols and colors for 2082 parties."""
    p_name = str(party_name).strip()
    
    # Comprehensive Mapping for 2082 (2026) Election
    mapping = {
        "Nepali Congress": {"symbol": "🌳", "color": "#28a745"},
        "Congress": {"symbol": "🌳", "color": "#28a745"},
        "CPN (UML)": {"symbol": "☀️", "color": "#dc3545"},
        "UML": {"symbol": "☀️", "color": "#dc3545"},
        "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#007bff"},
        "RSP": {"symbol": "🔔", "color": "#007bff"},
        "Nepal Communist Party": {"symbol": "⭐", "color": "#c82333"},
        "CPN (Maoist Centre)": {"symbol": "☭", "color": "#c82333"},
        "Maoist": {"symbol": "☭", "color": "#c82333"},
        "Rastriya Prajatantra Party": {"symbol": "🚜", "color": "#ffc107"},
        "RPP": {"symbol": "🚜", "color": "#ffc107"},
        "Janmat Party": {"symbol": "📢", "color": "#fd7e14"},
        "Janmat": {"symbol": "📢", "color": "#fd7e14"},
        "Nagarik Unmukti Party": {"symbol": "🏠", "color": "#6f42c1"},
        "Ujyalo Nepal Party": {"symbol": "💡", "color": "#f8f9fa"},
        "UNP": {"symbol": "💡", "color": "#f8f9fa"},
        "Independent": {"symbol": "🔲", "color": "#6c757d"},
        "IND": {"symbol": "🔲", "color": "#6c757d"}
    }
    
    # Try exact match, then fuzzy match
    if p_name in mapping:
        return mapping[p_name]
    
    for key in mapping:
        if key.lower() in p_name.lower():
            return mapping[key]
            
    return mapping["Independent"]

def process_election_data(raw_data):
    """Processes raw JSON into validated UI components with robust key checking."""
    parties_list = []
    featured_list = []
    hot_seats_list = []

    if not raw_data:
        return [], [], []

    # 1. Aggregate Party Stats
    counts = {}
    for item in raw_data:
        # Check multiple possible keys for the leading party
        p_name = item.get('leading_party') or item.get('party_name') or item.get('party') or 'Independent'
        counts[p_name] = counts.get(p_name, 0) + 1

    for name, leads in counts.items():
        meta = get_party_meta(name)
        parties_list.append({
            "name": name,
            "symbol": meta["symbol"],
            "leads": leads,
            "color": meta["color"]
        })

    # 2. Extract Featured Leaders
    stars = ["balen", "gagan", "rabi", "oli", "deuba", "kulman", "ck raut", "harka"]
    
    for item in raw_data:
        cands = item.get('candidates', [])
        if len(cands) < 1: continue
        
        c1 = cands[0]
        c2 = cands[1] if len(cands) > 1 else {}
        
        c1_name = str(c1.get('name', '')).lower()
        c2_name = str(c2.get('name', '')).lower()
        
        if any(star in c1_name or star in c2_name for star in stars):
            p1_name = c1.get('party') or c1.get('party_name') or 'Independent'
            p2_name = c2.get('party') or c2.get('party_name') or 'Independent'
            
            featured_list.append({
                "constituency": item.get('name') or item.get('constituency') or 'N/A',
                "c1": {
                    "name": c1.get('name', 'N/A'),
                    "party": p1_name,
                    "votes": c1.get('votes', 0),
                    "symbol": get_party_meta(p1_name)["symbol"]
                },
                "c2": {
                    "name": c2.get('name', 'N/A'),
                    "party": p2_name,
                    "votes": c2.get('votes', 0),
                    "symbol": get_party_meta(p2_name)["symbol"]
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
                if margin < 1500 and margin > 0:
                    p_name = cands[0].get('party') or cands[0].get('party_name') or 'IND'
                    hot_seats_list.append({
                        "area": item.get('name', 'Unknown'),
                        "leading": cands[0].get('name', 'N/A'),
                        "margin": margin,
                        "party": p_name
                    })
            except: continue

    return parties_list, featured_list[:6], sorted(hot_seats_list, key=lambda x: x['margin'])[:10]