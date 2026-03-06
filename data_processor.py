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
    """Returns official symbols and colors for 2082 parties with ultra-robust matching."""
    if not party_name:
        return {"symbol": "🔲", "color": "#6c757d"}
        
    p_name = str(party_name).strip()
    
    # Comprehensive Mapping for 2082 (2026) Election with aliases
    mapping = {
        "Nepali Congress": {"symbol": "🌳", "color": "#28a745", "keywords": ["congress", "nc"]},
        "CPN (UML)": {"symbol": "☀️", "color": "#dc3545", "keywords": ["uml", "cpn uml", "cpn(uml)"]},
        "Rastriya Swatantra Party": {"symbol": "🔔", "color": "#007bff", "keywords": ["rsp", "swatantra", "bell"]},
        "CPN (Maoist Centre)": {"symbol": "☭", "color": "#c82333", "keywords": ["maoist", "centre", "center"]},
        "Rastriya Prajatantra Party": {"symbol": "🚜", "color": "#ffc107", "keywords": ["rpp", "prajatantra"]},
        "Janmat Party": {"symbol": "📢", "color": "#fd7e14", "keywords": ["janmat", "ck raut"]},
        "Nagarik Unmukti Party": {"symbol": "🏠", "color": "#6f42c1", "keywords": ["nup", "unmukti"]},
        "Nepal Communist Party": {"symbol": "⭐", "color": "#ff0000", "keywords": ["communist", "ncp"]},
        "Ujyalo Nepal Party": {"symbol": "💡", "color": "#f8f9fa", "keywords": ["ujyalo", "bulb", "kulman"]},
        "Independent": {"symbol": "🔲", "color": "#6c757d", "keywords": ["ind", "independent", "swatantra"]}
    }
    
    p_name_lower = p_name.lower()
    
    # 1. Look for keyword matches first (most robust)
    for main_name, data in mapping.items():
        if any(kw in p_name_lower for kw in data["keywords"]):
            return data
            
    # 2. Check direct key match
    if p_name in mapping:
        return mapping[p_name]
            
    return mapping["Independent"]

def process_election_data(raw_data):
    """Processes raw JSON into validated UI components with multi-key fallback."""
    parties_list = []
    featured_list = []
    hot_seats_list = []

    if not raw_data:
        return [], [], []

    # 1. Aggregate Party Stats
    counts = {}
    for item in raw_data:
        # Determine leading party by checking root key or the first candidate's party info
        cands = item.get('candidates', [])
        p_raw = None
        
        if cands and isinstance(cands, list):
            # Check candidate level first as it's more granular
            p_raw = cands[0].get('party') or cands[0].get('party_name') or cands[0].get('partyName')
            
        if not p_raw:
            p_raw = item.get('leading_party') or item.get('party_name') or 'Independent'
            
        meta = get_party_meta(p_raw)
        p_final_name = next((k for k, v in get_party_meta(p_raw).items() if k != "symbol" and k != "color" and k != "keywords"), p_raw)
        
        # Standardize party name for counting
        standard_name = "Independent"
        for official_name, m in {
            "Nepali Congress": ["congress", "nc"], 
            "CPN (UML)": ["uml"], 
            "Rastriya Swatantra Party": ["rsp"],
            "CPN (Maoist Centre)": ["maoist"]
        }.items():
            if any(kw in str(p_raw).lower() for kw in m):
                standard_name = official_name
                break
        
        counts[standard_name] = counts.get(standard_name, 0) + 1

    for name, leads in counts.items():
        meta = get_party_meta(name)
        parties_list.append({
            "name": name,
            "symbol": meta["symbol"],
            "leads": leads,
            "color": meta["color"]
        })

    # 2. Extract Featured Leaders
    stars = ["balen", "gagan", "rabi", "oli", "deuba", "kulman", "ck raut", "harka", "mahendra", "rabin"]
    
    for item in raw_data:
        cands = item.get('candidates', [])
        if not isinstance(cands, list) or len(cands) < 1:
            continue
        
        c1 = cands[0]
        c2 = cands[1] if len(cands) > 1 else {}
        
        c1_name = str(c1.get('name', '')).lower()
        c2_name = str(c2.get('name', '')).lower()
        
        if any(star in c1_name or star in c2_name for star in stars):
            p1_raw = c1.get('party') or c1.get('party_name') or c1.get('partyName') or 'Independent'
            p2_raw = c2.get('party') or c2.get('party_name') or c2.get('partyName') or 'Independent'
            
            featured_list.append({
                "constituency": item.get('name') or item.get('constituency') or 'N/A',
                "c1": {
                    "name": c1.get('name', 'N/A'),
                    "party": p1_raw,
                    "votes": c1.get('votes', 0),
                    "symbol": get_party_meta(p1_raw)["symbol"]
                },
                "c2": {
                    "name": c2.get('name', 'N/A'),
                    "party": p2_raw,
                    "votes": c2.get('votes', 0),
                    "symbol": get_party_meta(p2_raw)["symbol"]
                }
            })

    # 3. Detect Hot Seats
    for item in raw_data:
        cands = item.get('candidates', [])
        if isinstance(cands, list) and len(cands) >= 2:
            try:
                v1 = int(cands[0].get('votes', 0))
                v2 = int(cands[1].get('votes', 0))
                margin = abs(v1 - v2)
                if margin < 2000 and (v1 > 0 or v2 > 0):
                    p_raw = cands[0].get('party') or cands[0].get('party_name') or 'IND'
                    hot_seats_list.append({
                        "area": item.get('name', 'Unknown'),
                        "leading": cands[0].get('name', 'N/A'),
                        "margin": margin,
                        "party": p_raw
                    })
            except: continue

    return parties_list, featured_list[:6], sorted(hot_seats_list, key=lambda x: x['margin'])[:10]