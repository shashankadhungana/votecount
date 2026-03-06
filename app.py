import streamlit as st
import time
from data_processor import fetch_live_data, process_election_data

# --- APP CONFIG ---
st.set_page_config(
    page_title="Nepal Election 2082 Live",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- MODERN UI STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; background-color: #0e1117; }

    /* Custom Header */
    .main-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; border-bottom: 1px solid #333; padding-bottom: 1rem; }
    .title-area h1 { font-weight: 800; margin: 0; font-size: 2.2rem; color: #fff; letter-spacing: -1px; }
    .title-area p { color: #888; margin: 0; font-size: 0.9rem; }

    /* Live Badge */
    .live-badge { background: rgba(255, 75, 75, 0.1); border: 1px solid #ff4b4b; color: #ff4b4b; padding: 4px 12px; border-radius: 50px; font-weight: 700; font-size: 0.75rem; display: flex; align-items: center; gap: 6px; }
    .pulse { width: 8px; height: 8px; background: #ff4b4b; border-radius: 50%; box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); animation: pulse-red 2s infinite; }
    @keyframes pulse-red { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); } }

    /* Metric Cards */
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 2rem; }
    .metric-card { background: #1a1c23; border: 1px solid #333; padding: 1.2rem; border-radius: 12px; text-align: center; }
    .metric-val { font-size: 1.8rem; font-weight: 800; color: #fff; display: block; }
    .metric-lbl { font-size: 0.7rem; color: #666; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; }

    /* Clash Cards */
    .clash-card { background: #1a1c23; border: 1px solid #333; border-radius: 16px; min-width: 320px; padding: 20px; position: relative; transition: all 0.3s ease; }
    .clash-card:hover { border-color: #007bff; transform: translateY(-3px); background: #232731; }
    .constituency-tag { position: absolute; top: -10px; left: 20px; background: #007bff; color: white; padding: 2px 10px; font-size: 0.7rem; border-radius: 4px; font-weight: 700; }
    .vs-marker { text-align: center; color: #444; font-weight: 800; font-size: 0.8rem; margin: 10px 0; position: relative; }
    .vs-marker::before, .vs-marker::after { content: ''; position: absolute; top: 50%; width: 40%; height: 1px; background: #333; }
    .vs-marker::before { left: 0; } .vs-marker::after { right: 0; }
    
    .cand-box { display: flex; justify-content: space-between; align-items: center; }
    .cand-name { font-weight: 600; color: #fff; font-size: 1rem; }
    .cand-party { font-size: 0.7rem; color: #777; }
    .cand-votes { font-weight: 800; color: #fff; font-size: 1.2rem; }

    /* Hot Seats */
    .hot-row { display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid #222; }
    .hot-row:last-child { border-bottom: none; }
    .margin-tag { background: rgba(255, 193, 7, 0.1); color: #ffc107; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
raw_data = fetch_live_data()
parties, featured, hot_seats = process_election_data(raw_data)

# --- UI HEADER ---
st.markdown(f"""
    <div class="main-header">
        <div class="title-area">
            <h1>🇳🇵 Nepal Election 2082 Live</h1>
            <p>House of Representatives (HoR) Dashboard • Updated {time.strftime('%H:%M:%S')}</p>
        </div>
        <div class="live-badge"><span class="pulse"></span>LIVE UPDATES</div>
    </div>
""", unsafe_allow_html=True)

# --- TOP METRICS ---
st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card"><span class="metric-val">165⬡</span><span class="metric-lbl">Constituencies</span></div>
        <div class="metric-card"><span class="metric-val">7◈</span><span class="metric-lbl">Provinces</span></div>
        <div class="metric-card"><span class="metric-val">61◉</span><span class="metric-lbl">Parties</span></div>
        <div class="metric-card"><span class="metric-val">275◆</span><span class="metric-lbl">Total Seats</span></div>
    </div>
""", unsafe_allow_html=True)

# --- FEATURED HIGH-STAKES BATTLES ---
if featured:
    st.markdown("### 🔥 High-Stakes Battles")
    cols = st.columns(len(featured) if len(featured) < 3 else 3)
    for idx, f in enumerate(featured):
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="clash-card">
                    <div class="constituency-tag">{f['constituency']}</div>
                    <div class="cand-box">
                        <div>
                            <div class="cand-name">{f['c1']['symbol']} {f['c1']['name']}</div>
                            <div class="cand-party">{f['c1']['party']}</div>
                        </div>
                        <div class="cand-votes">{f['c1']['votes']:,}</div>
                    </div>
                    <div class="vs-marker">VS</div>
                    <div class="cand-box">
                        <div>
                            <div class="cand-name">{f['c2']['symbol']} {f['c2']['name']}</div>
                            <div class="cand-party">{f['c2']['party']}</div>
                        </div>
                        <div class="cand-votes">{f['c2']['votes']:,}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.write("") # Spacing

# --- TWO COLUMN BODY ---
st.markdown("<br>", unsafe_allow_html=True)
col_l, col_r = st.columns([1, 1], gap="large")

with col_l:
    st.markdown("### 🏛️ Party Standing")
    if parties:
        for p in sorted(parties, key=lambda x: x['leads'], reverse=True):
            total_leads = sum([x['leads'] for x in parties])
            p_width = (p['leads'] / total_leads) * 100 if total_leads > 0 else 0
            st.markdown(f"""
                <div style="margin-bottom:1.5rem">
                    <div style="display:flex; justify-content:space-between; font-weight:600; margin-bottom:6px;">
                        <span>{p['symbol']} {p['name']}</span>
                        <span>{p['leads']} <span style='color:#666; font-weight:400;'>Leads</span></span>
                    </div>
                    <div style="height:10px; background:#222; border-radius:10px; overflow:hidden;">
                        <div style="height:100%; width:{p_width}%; background:{p['color']}; transition: width 1s;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Awaiting party data...")

with col_r:
    st.markdown("### 🎯 Hot Seats (Close Race)")
    if hot_seats:
        st.markdown('<div style="background:#1a1c23; border:1px solid #333; border-radius:12px; padding:10px;">', unsafe_allow_html=True)
        for h in hot_seats:
            st.markdown(f"""
                <div class="hot-row">
                    <div>
                        <div style="font-weight:700; color:#fff;">{h['area']}</div>
                        <div style="font-size:0.7rem; color:#888;">Leading: {h['leading']} ({h['party']})</div>
                    </div>
                    <div><span class="margin-tag">Gap: {h['margin']}</span></div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No narrow margins detected currently.")

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align:center; color:#555; font-size:0.8rem;'>Election 2082 Live Tracker • Built for Real-time Decision Support</p>", unsafe_allow_html=True)

if st.button("🔄 Refresh Data Now"):
    st.rerun()