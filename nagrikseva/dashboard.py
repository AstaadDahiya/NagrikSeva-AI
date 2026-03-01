"""
NagrikSeva AI — Streamlit Admin Dashboard
===========================================
Real-time analytics dashboard for administrators.
Run with: streamlit run dashboard.py
"""

import os
import sys
import requests
import logging
from datetime import datetime, timezone

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

# Add current dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

load_dotenv()

logger = logging.getLogger(__name__)

# ---------- Page Config ----------

st.set_page_config(
    page_title="NagrikSeva AI — Command Center",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Custom CSS ----------

st.markdown("""
<style>
    /* Dark theme overrides with saffron & navy */
    .stApp {
        background-color: #0a0f1c;
    }
    
    .main-header {
        background: linear-gradient(135deg, #FF6600 0%, #FF8533 50%, #003366 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        padding: 0.5rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #0d1526 0%, #162035 100%);
        border: 1px solid #1e3055;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 51, 102, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(255, 102, 0, 0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF6600;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #8899aa;
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .status-open { color: #ff4444; font-weight: 600; }
    .status-in_progress { color: #ffaa00; font-weight: 600; }
    .status-resolved { color: #00cc66; font-weight: 600; }
    .status-escalated { color: #ff6600; font-weight: 600; }
    .status-incomplete { color: #888888; font-weight: 600; }
    
    .sidebar .sidebar-content {
        background-color: #0a0f1c;
    }
    
    .stDataFrame {
        border: 1px solid #1e3055;
        border-radius: 8px;
    }
    
    div[data-testid="stSidebar"] {
        background-color: #0d1526;
        border-right: 1px solid #1e3055;
    }
    
    .refresh-badge {
        background: #162035;
        border: 1px solid #1e3055;
        border-radius: 8px;
        padding: 0.3rem 0.8rem;
        font-size: 0.75rem;
        color: #667788;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Plotly Theme ----------

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#ccddee", family="Inter, sans-serif"),
    margin=dict(l=40, r=40, t=50, b=40),
)

SAFFRON_COLORS = [
    "#FF6600", "#FF8533", "#FFa366", "#003366", "#004d99",
    "#0066cc", "#3399ff", "#66b3ff", "#00cc66", "#ff4444",
]


# ---------- Data Loading ----------

@st.cache_data(ttl=30)
def load_stats():
    """Load aggregated statistics (cached for 30s)."""
    try:
        return database.get_stats()
    except Exception as e:
        logger.error(f"Failed to load stats: {e}")
        return {
            "total": 0, "by_status": {}, "by_category": {},
            "by_language": {}, "by_ward": {},
            "today_count": 0, "avg_call_duration": 0,
        }


@st.cache_data(ttl=30)
def load_grievances(limit=50):
    """Load recent grievances (cached for 30s)."""
    try:
        return database.get_all_grievances(limit=limit)
    except Exception as e:
        logger.error(f"Failed to load grievances: {e}")
        return []


# ---------- Sidebar ----------

st.sidebar.markdown("## 🇮🇳 NagrikSeva AI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Overview", "📈 Analytics", "📋 Live Feed", "📞 Outbound Campaign", "🔍 Ticket Lookup"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<div class="refresh-badge">🔄 Auto-refresh: 30s</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f'<div class="refresh-badge">⏰ {datetime.now().strftime("%I:%M:%S %p")}</div>',
    unsafe_allow_html=True,
)


# ========== PAGE 1: OVERVIEW ==========

if page == "📊 Overview":
    st.markdown('<h1 class="main-header">🇮🇳 NagrikSeva AI — Command Center</h1>', unsafe_allow_html=True)
    st.markdown("")
    
    stats = load_stats()
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['total']}</div>
            <div class="metric-label">Total Grievances</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['today_count']}</div>
            <div class="metric-label">Open Today</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        resolved = stats.get("by_status", {}).get("resolved", 0)
        total = stats.get("total", 1) or 1
        pct = round((resolved / total) * 100, 1)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pct}%</div>
            <div class="metric-label">Resolved Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_dur = stats.get("avg_call_duration", 0)
        minutes = int(avg_dur // 60)
        seconds = int(avg_dur % 60)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{minutes}m {seconds}s</div>
            <div class="metric-label">Avg Call Duration</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown("---")
    
    # Quick status overview
    col_a, col_b = st.columns(2)
    
    with col_a:
        status_data = stats.get("by_status", {})
        if status_data:
            fig = go.Figure(data=[go.Bar(
                x=list(status_data.keys()),
                y=list(status_data.values()),
                marker_color=["#ff4444", "#ffaa00", "#00cc66", "#ff6600", "#888888"][:len(status_data)],
                text=list(status_data.values()),
                textposition="auto",
            )])
            fig.update_layout(
                title="Grievances by Status",
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        cat_data = stats.get("by_category", {})
        if cat_data:
            filtered = {k: v for k, v in cat_data.items() if v > 0}
            if filtered:
                fig = px.pie(
                    names=list(filtered.keys()),
                    values=list(filtered.values()),
                    color_discrete_sequence=SAFFRON_COLORS,
                    title="Grievances by Category",
                )
                fig.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)


# ========== PAGE 2: ANALYTICS ==========

elif page == "📈 Analytics":
    st.markdown('<h1 class="main-header">📈 Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("")
    
    stats = load_stats()
    
    # Row 1: Category pie + Status bar
    col1, col2 = st.columns(2)
    
    with col1:
        cat_data = stats.get("by_category", {})
        filtered = {k: v for k, v in cat_data.items() if v > 0}
        if filtered:
            fig = px.pie(
                names=list(filtered.keys()),
                values=list(filtered.values()),
                color_discrete_sequence=SAFFRON_COLORS,
                title="Grievances by Category",
                hole=0.4,
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data yet.")
    
    with col2:
        status_data = stats.get("by_status", {})
        if status_data:
            colors = {
                "open": "#ff4444", "in_progress": "#ffaa00",
                "resolved": "#00cc66", "escalated": "#ff6600",
                "incomplete": "#888888",
            }
            fig = go.Figure(data=[go.Bar(
                x=list(status_data.keys()),
                y=list(status_data.values()),
                marker_color=[colors.get(s, "#666") for s in status_data.keys()],
                text=list(status_data.values()),
                textposition="auto",
            )])
            fig.update_layout(title="Grievances by Status", **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data yet.")
    
    st.markdown("---")
    
    # Row 2: Top wards
    ward_data = stats.get("by_ward", {})
    if ward_data:
        # Sort and take top 10
        sorted_wards = dict(sorted(ward_data.items(), key=lambda x: x[1], reverse=True)[:10])
        fig = go.Figure(data=[go.Bar(
            x=list(sorted_wards.values()),
            y=list(sorted_wards.keys()),
            orientation="h",
            marker_color="#FF6600",
            text=list(sorted_wards.values()),
            textposition="auto",
        )])
        fig.update_layout(
            title="Top 10 Wards by Grievance Count",
            yaxis=dict(autorange="reversed"),
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No ward data yet.")
    
    st.markdown("---")
    
    # Row 3: Language distribution
    lang_data = stats.get("by_language", {})
    filtered_lang = {k: v for k, v in lang_data.items() if v > 0}
    if filtered_lang:
        fig = px.pie(
            names=list(filtered_lang.keys()),
            values=list(filtered_lang.values()),
            color_discrete_sequence=["#FF6600", "#003366", "#00cc66"],
            title="Language Distribution",
        )
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No language data yet.")


# ========== PAGE 3: LIVE FEED ==========

elif page == "📋 Live Feed":
    st.markdown('<h1 class="main-header">📋 Live Feed</h1>', unsafe_allow_html=True)
    st.markdown("")
    
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
    
    grievances = load_grievances(50)
    
    if grievances:
        # Build DataFrame
        rows = []
        for g in grievances:
            created = g.get("created_at", "")
            if hasattr(created, "strftime"):
                created = created.strftime("%d %b %Y, %I:%M %p")
            
            rows.append({
                "Ticket ID": g.get("ticket_id", ""),
                "Name": g.get("citizen_name", ""),
                "Ward": g.get("ward", ""),
                "Category": g.get("category", ""),
                "Status": g.get("status", ""),
                "Language": g.get("language", ""),
                "Created At": created,
            })
        
        df = pd.DataFrame(rows)
        
        # Color-coded status using styled DataFrame
        def color_status(val):
            colors = {
                "open": "color: #ff4444",
                "in_progress": "color: #ffaa00",
                "resolved": "color: #00cc66",
                "escalated": "color: #ff6600",
                "incomplete": "color: #888888",
            }
            return colors.get(val, "")
        
        styled = df.style.map(color_status, subset=["Status"])
        st.dataframe(styled, use_container_width=True, height=600)
    else:
        st.info("No grievances recorded yet. Make a call to get started!")


# ========== PAGE 4: OUTBOUND CAMPAIGN ==========

elif page == "📞 Outbound Campaign":
    st.markdown('<h1 class="main-header">📞 Outbound Status Update Campaign</h1>', unsafe_allow_html=True)
    st.markdown("")
    
    hours = st.slider(
        "Call grievances older than (hours):",
        min_value=1,
        max_value=168,
        value=48,
        step=1,
    )
    
    st.markdown("")
    
    # Show count of eligible grievances
    try:
        eligible = database.get_open_old_grievances(hours=hours)
        st.info(f"📊 **{len(eligible)}** open grievances older than {hours} hours")
    except Exception:
        eligible = []
        st.warning("Could not load grievance data.")
    
    st.markdown("")
    
    if st.button("🚀 Launch Campaign", type="primary", disabled=len(eligible) == 0):
        with st.spinner("Launching outbound calls..."):
            try:
                base_url = os.getenv("BASE_URL", "http://localhost:8000")
                resp = requests.post(
                    f"{base_url}/outbound/trigger",
                    params={"hours": hours},
                    timeout=120,
                )
                result = resp.json()
                
                if result.get("status") == "campaign_complete":
                    st.success(
                        f"✅ Campaign complete! "
                        f"Triggered: {result.get('triggered', 0)}, "
                        f"Failed: {result.get('failed', 0)}, "
                        f"Skipped: {result.get('skipped', 0)}"
                    )
                elif result.get("status") == "no_grievances":
                    st.info(result.get("message", "No eligible grievances."))
                else:
                    st.error(f"Campaign error: {result}")
                    
            except Exception as e:
                st.error(f"Failed to trigger campaign: {e}")
    
    st.markdown("---")
    st.markdown("### Recent Outbound Call Logs")
    
    # Show recent outbound logs
    try:
        recent = load_grievances(20)
        logs = []
        for g in recent:
            for call_log in g.get("outbound_calls", []):
                called_at = call_log.get("called_at", "")
                if hasattr(called_at, "strftime"):
                    called_at = called_at.strftime("%d %b %Y, %I:%M %p")
                logs.append({
                    "Ticket ID": g.get("ticket_id", ""),
                    "Phone": g.get("phone", ""),
                    "Called At": called_at,
                    "Outcome": call_log.get("outcome", ""),
                    "Message": call_log.get("message", "")[:60],
                })
        
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.info("No outbound calls made yet.")
    except Exception as e:
        st.warning(f"Could not load outbound logs: {e}")


# ========== PAGE 5: TICKET LOOKUP ==========

elif page == "🔍 Ticket Lookup":
    st.markdown('<h1 class="main-header">🔍 Ticket Lookup</h1>', unsafe_allow_html=True)
    st.markdown("")
    
    ticket_input = st.text_input(
        "Enter Ticket ID",
        placeholder="NS-20260301-1234",
        max_chars=20,
    )
    
    if ticket_input and st.button("🔎 Search", type="primary"):
        grievance = database.get_grievance(ticket_input.strip().upper())
        
        if grievance:
            # Status emoji
            emoji_map = {
                "open": "📋", "in_progress": "🔄",
                "resolved": "✅", "escalated": "⚠️",
                "incomplete": "❌",
            }
            status = grievance.get("status", "unknown")
            emoji = emoji_map.get(status, "📋")
            
            st.markdown(f"### {emoji} {ticket_input.upper()}")
            st.markdown("---")
            
            # Details in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**👤 Name:** {grievance.get('citizen_name', 'N/A')}")
                st.markdown(f"**📍 Ward:** {grievance.get('ward', 'N/A')}")
                st.markdown(f"**🏙 District:** {grievance.get('district', 'N/A')}")
                st.markdown(f"**📞 Phone:** {grievance.get('phone', 'N/A')}")
            
            with col2:
                st.markdown(f"**📁 Category:** {grievance.get('category', 'N/A')}")
                st.markdown(f"**📊 Status:** {status.replace('_', ' ').title()}")
                st.markdown(f"**🗣 Language:** {grievance.get('language', 'N/A')}")
                
                dur = grievance.get("call_duration_s", 0)
                if dur:
                    st.markdown(f"**⏱ Call Duration:** {dur}s")
            
            st.markdown("---")
            st.markdown(f"**📝 Description:** {grievance.get('description', 'N/A')}")
            
            notes = grievance.get("resolution_notes", "")
            if notes:
                st.markdown(f"**📋 Resolution Notes:** {notes}")
            
            # Timeline
            created = grievance.get("created_at", "")
            updated = grievance.get("updated_at", "")
            if hasattr(created, "strftime"):
                created = created.strftime("%d %b %Y, %I:%M %p")
            if hasattr(updated, "strftime"):
                updated = updated.strftime("%d %b %Y, %I:%M %p")
            
            st.markdown("---")
            st.markdown("### 📅 Timeline")
            st.markdown(f"- **Created:** {created}")
            st.markdown(f"- **Last Updated:** {updated}")
            
            # Outbound calls
            outbound_calls = grievance.get("outbound_calls", [])
            if outbound_calls:
                st.markdown("### 📞 Outbound Call History")
                for call_log in outbound_calls:
                    called_at = call_log.get("called_at", "")
                    if hasattr(called_at, "strftime"):
                        called_at = called_at.strftime("%d %b %Y, %I:%M %p")
                    st.markdown(
                        f"- **{called_at}** — "
                        f"{call_log.get('outcome', '')} — "
                        f"{call_log.get('message', '')}"
                    )
        else:
            st.error(f"❌ Ticket ID `{ticket_input}` not found.")
