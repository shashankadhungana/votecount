import requests
import streamlit as st
import time

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=30)
def fetch_live_data():
    """Fetches raw JSON data with browser headers for R2 access."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(SOURCE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        st.sidebar.error(f"Data Fetch Failed: Check URL or Internet Connection ({e})")
        return []

def get_party_meta(party_input):
    """
    Standardizes party identification using deep keyword detection.
    Maps symbols and colors based on official 2082 (2026) standards.
    """
    if not party_input:
        return {"symbol": "🔲", "color": "#6c757d", "name": "Independent"}
        
    p_name = str(party_input).strip().lower()
    
    # Official 2082 Mapping with specific detection keywords
    mapping = {
        "Nepali Congress": {
            "symbol": "🌳", 
            "color": "#28a745", 
            "keywords": ["congress", "nc", "🌳", "nepali congress", "tree"]
        },
        "CPN (UML)": {
            "symbol": "☀️", 
            "color": "#dc3545", 
            "keywords": ["uml", "sun", "surya", "cpn uml", "cpn(uml)", "☀️"]
        },
        "Rastriya Swatantra Party": {
            "symbol": "🔔", 
            "color": "#007bff", 
            "keywords": ["rsp", "bell", "ghanti", "swatantra", "🔔"]
        },
        "CPN (Maoist Centre)": {
            "symbol": "☭", 
            "color": "#c82333", 
            "keywords": ["maoist", "centre", "maobadi", "hammer", "sickle", "☭"]
        },
        "Rastriya Prajatantra Party": {
            "symbol": "🚜", 
            "color": "#ffc107", 
            "keywords": ["rpp", "prajatantra", "plough", "🚜"]
        },
        "Janmat Party": {
            "symbol": "📢", 
            "color": "#fd7e14", 
            "keywords": ["janmat", "ck raut", "loudspeaker", "📢"]
        },
        "Nagarik Unmukti Party": {
            "symbol": "🏠", 
            "color": "#6f42c1", 
            "keywords": ["nup", "unmukti", "house", "🏠"]
        },
        "Nepal Communist Party": {
            "symbol": "⭐", 
            "color": "#ff0000", 
            "keywords": ["communist", "star", "ncp", "⭐"]
        },
        "Independent": {
            "symbol": "🔲", 
            "color": "#6c757d", 
            "keywords": ["ind", "independent", "alone", "🔲"]
        }
    }
    
    # Check every keyword for a partial match in the raw party string
    for official_name, meta in mapping.items():
        if any(kw in p_name for kw in meta["keywords"]):
            res = meta.copy()
            res["name"] = official_name
            return res
            
    return {"symbol": "🔲", "color": "#6c757d", "name": "Independent"}

def process_election_data(raw_data):
    """Processes raw JSON into UI components with ultra-robust data discovery."""
    parties_list = []
    featured_list = []
    hot_seats_list = []

    if not raw_data:
        return [], [], []

    # 1. Aggregate Party Stats (Leading/Won)
    counts = {}
    for item in raw_data:
        cands = item.get('candidates', [])
        p_raw = None
        
        # We prioritize the party of the first candidate (current leader)
        if isinstance(cands, list) and len(cands) > 0:
            leader = cands[0]
            # Try every possible key where party info might hide
            p_raw = (leader.get('party') or 
                     leader.get('party_name') or 
                     leader.get('partyName') or 
                     leader.get('party_id') or
                     leader.get('party_symbol') or
                     leader.get('symbol'))
        
        # Fallback to root item keys
        if not p_raw:
            p_raw = (item.get('leading_party') or 
                     item.get('party_name') or 
                     item.get('party') or 
                     "Independent")
            
        meta = get_party_meta(p_raw)
        standard_name = meta["name"]
        counts[standard_name] = counts.get(standard_name, 0) + 1

    # Format the party list for the UI
    for name, leads in counts.items():
        meta = get_party_meta(name)
        parties_list.append({
            "name": name,
            "symbol": meta["symbol"],
            "leads": leads,
            "color": meta["color"]
        })

    # 2. Extract Featured Leaders (Stars)
    stars = ["balen", "gagan", "rabi", "oli", "deuba", "kulman", "ck raut", "harka"]
    
    for item in raw_data:
        cands = item.get('candidates', [])
        if not isinstance(cands, list) or len(cands) < 1:
            continue
        
        c1 = cands[0]
        c2 = cands[1] if len(cands) > 1 else {}
        
        c1_name = str(c1.get('name', '')).lower()
        c2_name = str(c2.get('name', '')).lower()
        
        # If a major candidate is found
        if any(star in c1_name or star in c2_name for star in stars):
            # Extract party using deep discovery keys
            p1_raw = (c1.get('party') or c1.get('party_name') or c1.get('partyName') or 'Independent')
            p2_raw = (c2.get('party') or c2.get('party_name') or c2.get('partyName') or 'Independent')
            
            m1 = get_party_meta(p1_raw)
            m2 = get_party_meta(p2_raw)
            
            featured_list.append({
                "constituency": item.get('name') or item.get('constituency') or 'N/A',
                "c1": {
                    "name": c1.get('name', 'N/A'),
                    "party": m1["name"],
                    "votes": c1.get('votes', 0),
                    "symbol": m1["symbol"]
                },
                "c2": {
                    "name": c2.get('name', 'N/A'),
                    "party": m2["name"],
                    "votes": c2.get('votes', 0),
                    "symbol": m2["symbol"]
                }
            })

    # 3. Detect Hot Seats (Margin < 2000)
    for item in raw_data:
        cands = item.get('candidates', [])
        if isinstance(cands, list) and len(cands) >= 2:
            try:
                v1 = int(cands[0].get('votes', 0))
                v2 = int(cands[1].get('votes', 0))
                margin = abs(v1 - v2)
                # Ensure the race has actually started
                if margin < 2000 and (v1 > 0 or v2 > 0):
                    p_raw = cands[0].get('party') or cands[0].get('party_name') or 'IND'
                    meta = get_party_meta(p_raw)
                    hot_seats_list.append({
                        "area": item.get('name', 'Unknown Area'),
                        "leading": cands[0].get('name', 'N/A'),
                        "margin": margin,
                        "party": meta["name"]
                    })
            except: continue

    return parties_list, featured_list[:6], sorted(hot_seats_list, key=lambda x: x['margin'])[:10]
