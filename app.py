import streamlit as st
import time
from data_processor import fetch_live_data, process_election_data

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Nepal Election 2082 Live",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern UI, Animations, and Clash Cards
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Live Animation */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 0, 0, 0.1);
        color: #ff4b4b;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 0, 0, 0.2);
        margin-bottom: 10px;
    }
    .dot {
        height: 8px;
        width: 8px;
        background-color: #ff4b4b;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        animation: blink 1.5s infinite;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }

    /* Stats Box */
    .stats-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    .stat-card {
        background: #1e1e1e;
        border: 1px solid #333;
        padding: 15px 25px;
        border-radius: 12px;
        flex: 1;
        min-width: 150px;
        text-align: center;
    }
    .stat-val { font-size: 1.8rem; font-weight: 800; color: #fff; line-height: 1;}
    .stat-label { font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px;}

    /* Clash Card Style */
    .clash-container {
        display: flex;
        gap: 20px;
        margin-bottom: 40px;
        overflow-x: auto;
        padding-bottom: 10px;
    }
    .clash-card {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
        border: 1px solid #444;
        border-radius: 16px;
        min-width: 320px;
        padding: 20px;
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease;
    }
    .clash-card:hover { transform: translateY(-5px); border-color: #666; }
    .vs-badge {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #ff4b4b;
        color: white;
        font-weight: 900;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        z-index: 2;
    }
    .candidate-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 10px 0;
    }
    .cand-info { display: flex; align-items: center; gap: 10px; }
    .cand-name { font-weight: 700; color: #eee; font-size: 0.95rem; }
    .cand-party { font-size: 0.7rem; color: #888; }
    .cand-votes { font-weight: 800; color: #fff; font-size: 1.1rem; }
    
    /* Hot Seat Row */
    .hot-seat-row {
        background: #151515;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #ffaa00;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATA INITIALIZATION ---
raw_json = fetch_live_data()
parties_data, featured_clashes, hot_seats = process_election_data(raw_json)

# --- HEADER SECTION ---
col_head, col_live = st.columns([4, 1])

with col_head:
    st.title("🇳🇵 Nepal Election 2082 (2026) Live Vote Count")
    st.subheader(f"General Election • Last Updated: {time.strftime('%H:%M:%S')}")

with col_live:
    st.markdown('<div class="live-indicator"><span class="dot"></span>LIVE UPDATES</div>', unsafe_allow_html=True)

# --- QUICK STATS BAR ---
st.markdown(f"""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-val">165⬡</div>
            <div class="stat-label">Constituencies</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">7◈</div>
            <div class="stat-label">Provinces</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">61◉</div>
            <div class="stat-label">Parties</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">275◆</div>
            <div class="stat-label">Total Seats</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- FEATURED CLASHES ---
if featured_clashes:
    st.markdown("### 🔥 Featured High-Stakes Battles")
    clash_html = '<div class="clash-container">'
    for clash in featured_clashes:
        clash_html += f"""
        <div class="clash-card">
            <div style="font-size: 0.75rem; color: #ff4b4b; font-weight: 700; margin-bottom: 10px;">{clash['constituency']}</div>
            <div class="vs-badge">VS</div>
            <div class="candidate-row">
                <div class="cand-info">
                    <span style="font-size: 1.5rem;">{clash['c1']['symbol']}</span>
                    <div>
                        <div class="cand-name">{clash['c1']['name']}</div>
                        <div class="cand-party">{clash['c1']['party']}</div>
                    </div>
                </div>
                <div class="cand-votes">{clash['c1']['votes']:,}</div>
            </div>
            <div style="height: 40px;"></div>
            <div class="candidate-row">
                <div class="cand-info">
                    <span style="font-size: 1.5rem;">{clash['c2']['symbol']}</span>
                    <div>
                        <div class="cand-name">{clash['c2']['name']}</div>
                        <div class="cand-party">{clash['c2']['party']}</div>
                    </div>
                </div>
                <div class="cand-votes">{clash['c2']['votes']:,}</div>
            </div>
        </div>
        """
    clash_html += '</div>'
    st.markdown(clash_html, unsafe_allow_html=True)
else:
    st.info("Loading high-stakes battle data...")

# --- MAIN DASHBOARD ---
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("### 🏛️ Leading Parties (Overall)")
    if parties_data:
        total_leads = sum([p['leads'] for p in parties_data])
        for p in sorted(parties_data, key=lambda x: x['leads'], reverse=True):
            percent = (p['leads'] / total_leads) * 100 if total_leads > 0 else 0
            st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 5px;">
                        <span>{p['symbol']} {p['name']}</span>
                        <span>{p['leads']} Leading</span>
                    </div>
                    <div style="background: #333; height: 8px; border-radius: 4px; width: 100%;">
                        <div style="background: {p['color']}; height: 8px; border-radius: 4px; width: {percent}%;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🎯 Hot Seats (Close Contests)")
    if hot_seats:
        for hs in hot_seats:
            st.markdown(f"""
                <div class="hot-seat-row">
                    <div>
                        <div style="font-weight: 700; color: #fff;">{hs['area']}</div>
                        <div style="font-size: 0.75rem; color: #888;">Leading: {hs['candidate']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #ffaa00; font-weight: 800; font-size: 0.9rem;">Margin: {hs['margin']}</div>
                        <div style="font-size: 0.6rem; color: #555;">BATTLEGROUND</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #555; font-size: 0.8rem;'>"
    "Data synchronized from cloud storage. Last synchronization: " + time.strftime('%H:%M:%S') + "</div>", 
    unsafe_allow_html=True
)

if st.button("Manual Refresh Data"):
    st.rerun()