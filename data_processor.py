import requests
import streamlit as st
import time

SOURCE_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"

@st.cache_data(ttl=60)
def fetch_live_data():
    """Fetches raw JSON data from the source URL with retry logic."""
    # We use a session for better connection pooling
    session = requests.Session()
    retries = 3
    for i in range(retries):
        try:
            response = session.get(SOURCE_URL, timeout=15)
            response.raise_for_status()
            data = response.json()
            # Basic validation: Check if we got a list
            if isinstance(data, list):
                return data
            else:
                st.warning(f"Unexpected data format: Received {type(data)}")
                return []
        except Exception as e:
            if i < retries - 1:
                time.sleep(1) # Wait before retry
                continue
            st.error(f"⚠️ Connection Error: Could not reach the data source. (Attempt {i+1})")
            return []
    return []

def process_election_data(raw_data):
    """Processes raw JSON with ultra-safe guards to prevent blank screens."""
    parties_list = []
    featured_list = []
    hot_seats_list = []

    # If data is empty, return early to let app.py handle "No Data" state
    if not raw_data or not isinstance(raw_data, list):
        return [], [], []

    party_symbols = {
        "Nepali Congress": "🌳",
        "CPN (UML)": "☀️",
        "Rastriya Swatantra Party": "🔔",
        "CPN (Maoist Centre)": "☭",
        "RPP": "🚜",
        "Independent": "🔲"
    }

    # 1. Process Party Stats (Leading/Won)
    party_counts = {}
    for item in raw_data:
        # Use .get() everywhere to avoid KeyErrors
        lead_party = item.get('leading_party') or item.get('party_name') or 'Independent'
        party_counts[lead_party] = party_counts.get(lead_party, 0) + 1

    colors = ["#00adef", "#008000", "#ff0000", "#e21b22", "#ffcc00", "#888888"]
    for i, (name, leads) in enumerate(party_counts.items()):
        parties_list.append({
            "name": name,
            "symbol": party_symbols.get(name, "🚩"),
            "leads": leads,
            "wins": 0,
            "color": colors[i % len(colors)]
        })

    # 2. Process Featured Leaders (Clash Cards)
    # These are names commonly looked for in Nepal elections
    featured_names = ["Balen Shah", "Gagan Thapa", "Rabi Lamichhane", "KP Sharma Oli", "Sher Bahadur Deuba", "Arzu Rana"]
    
    for item in raw_data:
        candidates = item.get('candidates', [])
        if not candidates or not isinstance(candidates, list):
            continue
        
        # Extract top 2 candidates safely
        c1 = candidates[0] if len(candidates) > 0 else {}
        c2 = candidates[1] if len(candidates) > 1 else {}
        
        c1_name = c1.get('name', 'N/A')
        c2_name = c2.get('name', 'N/A')
        
        # If any of our "stars" are in this constituency, add to featured
        if any(f_name.lower() in str(c1_name).lower() or f_name.lower() in str(c2_name).lower() for f_name in featured_names):
            featured_list.append({
                "constituency": item.get('name') or item.get('id') or "Unknown Area",
                "c1": {
                    "name": c1_name,
                    "party": c1.get('party', 'IND'),
                    "votes": c1.get('votes', 0),
                    "symbol": party_symbols.get(c1.get('party'), "🚩")
                },
                "c2": {
                    "name": c2_name,
                    "party": c2.get('party', 'IND'),
                    "votes": c2.get('votes', 0),
                    "symbol": party_symbols.get(c2.get('party'), "🚩")
                }
            })

    # 3. Process Hot Seats (Close Margins)
    for item in raw_data:
        candidates = item.get('candidates', [])
        if len(candidates) >= 2:
            try:
                v1 = int(candidates[0].get('votes', 0))
                v2 = int(candidates[1].get('votes', 0))
                margin = abs(v1 - v2)
                
                # A margin less than 1000 is a "Hot Seat"
                if margin < 1000:
                    hot_seats_list.append({
                        "area": item.get('name', 'Unknown'),
                        "candidate": candidates[0].get('name', 'N/A'),
                        "margin": margin
                    })
            except (ValueError, TypeError):
                continue

    # Sort hot seats by smallest margin first
    hot_seats_list = sorted(hot_seats_list, key=lambda x: x['margin'])

    return parties_list, featured_list[:6], hot_seats_list[:8]