"""
NagrikSeva AI — Streamlit Admin Dashboard
===========================================
Replicates a dark Lovable-style UI with custom CSS.
Run with: streamlit run dashboard.py
"""

import os
import sys
import requests
import logging
from datetime import datetime, timezone, timedelta
import random

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

load_dotenv()
logger = logging.getLogger(__name__)

# ---------- Page Config ----------

st.set_page_config(
    page_title="NagrikSeva AI Platform",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Custom CSS ----------

st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp { background-color: #0b101b; color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1e293b; }
    [data-testid="stHeader"] { background-color: transparent; }
    
    /* Typography */
    .page-title { font-size: 1.6rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.2rem; margin-top: -1rem; }
    .page-subtitle { font-size: 0.85rem; color: #94a3b8; margin-bottom: 1.5rem; }
    
    /* Sidebar Branding */
    .sidebar-brand { display: flex; align-items: center; gap: 0.8rem; padding: 0.5rem 0 1.5rem 0; }
    .sidebar-logo { background: #1e293b; border-radius: 8px; padding: 0.4rem 0.6rem; color: #f97316; font-size: 1.2rem; border: 1px solid #334155; }
    .sidebar-title { font-weight: 700; font-size: 1.1rem; color: #f97316; line-height: 1.2; }
    .sidebar-subtitle { font-size: 0.65rem; color: #64748b; letter-spacing: 1px; text-transform: uppercase; }
    
    .status-online { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: #94a3b8; margin-top: 2rem; padding: 1rem 0; border-top: 1px solid #1e293b;}
    .dot-green { height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block; }
    .dot-red { height: 8px; width: 8px; background-color: #ef4444; border-radius: 50%; display: inline-block; }
    
    /* Metric Cards */
    .m-card { background-color: #131821; border: 1px solid #1e293b; border-radius: 8px; padding: 1.2rem; flex: 1; min-width: 200px; }
    .m-title { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 0.5rem; }
    .m-value { font-size: 1.8rem; font-weight: 700; color: #f8fafc; }
    .m-sub { font-size: 0.75rem; color: #94a3b8; margin-top: 0.3rem; }
    
    .m-val-orange { color: #f97316; }
    .m-val-yellow { color: #f59e0b; }
    .m-val-green { color: #10b981; }
    
    /* Styled Panels */
    .panel { background-color: #131821; border: 1px solid #1e293b; border-radius: 8px; padding: 1.2rem; margin-bottom: 1.2rem; height: 100%; }
    .panel-title { font-size: 0.9rem; font-weight: 600; color: #f8fafc; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;}
    
    /* Status Pills */
    .pill { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 500; display: inline-block; }
    .pill-open { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    .pill-progress { background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); }
    .pill-resolved { background-color: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
    .pill-escalated { background-color: rgba(249, 115, 22, 0.1); color: #f97316; border: 1px solid rgba(249, 115, 22, 0.2); }
    .pill-other { background-color: rgba(100, 116, 139, 0.1); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.2); }
    
    /* Custom Table styling */
    table.custom-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.8rem; }
    table.custom-table th { border-bottom: 1px solid #1e293b; padding: 0.8rem 0.5rem; color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 0.65rem; letter-spacing: 0.5px;}
    table.custom-table td { border-bottom: 1px solid #1e293b; padding: 0.8rem 0.5rem; color: #cbd5e1; }
    table.custom-table tr:last-child td { border-bottom: none; }
    table.custom-table tr:hover { background-color: rgba(30, 41, 59, 0.3); }
    
    .td-ticket { color: #f97316; font-weight: 500; }
    .td-dim { color: #64748b; }
    .td-icon { filter: grayscale(0.2); margin-right: 0.4rem; }
    
    /* Live Call Transcript */
    .live-call-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
    .caller-avatar { background: #10b981; opacity: 0.2; border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; position: relative;}
    .caller-avatar::after { content: '📞'; position: absolute; font-size: 1.2rem; opacity: 1; }
    .live-badge { background: #10b981; color: #0b101b; font-size: 0.6rem; font-weight: 800; padding: 0.1rem 0.4rem; border-radius: 4px; position: absolute; top: -5px; right: -10px;}
    
    .transcript-box { background-color: #0b101b; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem; font-family: monospace; font-size: 0.85rem; line-height: 1.6; height: 250px; overflow-y: auto; margin-top: 1rem;}
    .t-agent { color: #f97316; font-weight: 600; }
    .t-citizen { color: #10b981; font-weight: 600; }
    .t-text { color: #94a3b8; }
    
    /* Badges */
    .badge-gray { background-color: #1e293b; color: #94a3b8; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.65rem; margin-right: 0.3rem;}
    .badge-orange { background-color: rgba(249, 115, 22, 0.1); color: #f97316; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.65rem; margin-right: 0.3rem; border: 1px solid rgba(249, 115, 22, 0.2);}
    
    /* Streamlit overrides */
    div.row-widget.stRadio > div { flex-direction: column; gap: 0.5rem; }
    div[data-testid="stRadio"] label { cursor: pointer; padding: 0.5rem 0.8rem; border-radius: 6px; transition: all 0.2s;}
    div[data-testid="stRadio"] label:hover { background-color: #1e293b; }
    
    /* Hide radio button circles */
    div[data-baseweb="radio"] > div { display: none; }
    
    /* StSlider overrides */
    div[data-baseweb="slider"] { margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter, sans-serif", size=11),
    margin=dict(l=20, r=20, t=30, b=20),
    colorway=["#f97316", "#3b82f6", "#10b981", "#f59e0b", "#64748b", "#8b5cf6"]
)


# ---------- Data Loading ----------

@st.cache_data(ttl=30)
def load_stats():
    try:
        return database.get_stats()
    except Exception as e:
        logger.error(f"Failed to load stats: {e}")
        return {"total": 0, "by_status": {}, "by_category": {}, "by_language": {}, "by_ward": {}, "today_count": 0, "avg_call_duration": 0}

@st.cache_data(ttl=30)
def load_grievances(limit=50):
    try:
        return database.get_all_grievances(limit=limit)
    except Exception as e:
        logger.error(f"Failed to load grievances: {e}")
        return []

def get_status_pill(status):
    status_lower = status.lower()
    if status_lower in ["open", "new"]: return f'<span class="pill pill-open">Open</span>'
    elif status_lower in ["in_progress", "in progress"]: return f'<span class="pill pill-progress">In Progress</span>'
    elif status_lower == "resolved": return f'<span class="pill pill-resolved">Resolved</span>'
    elif status_lower == "escalated": return f'<span class="pill pill-escalated">Escalated</span>'
    else: return f'<span class="pill pill-other">{status.title()}</span>'

def get_cat_icon(cat):
    cat = cat.lower()
    if "road" in cat: return "🛣️ Roads"
    if "water" in cat: return "💧 Water"
    if "electric" in cat: return "⚡ Electricity"
    if "sanitation" in cat or "garbage" in cat: return "🗑️ Sanitation"
    if "health" in cat: return "🏥 Health"
    return "📋 Other"

def format_time_ago(dt):
    if not hasattr(dt, 'timestamp'): return "just now"
    now = datetime.now(timezone.utc)
    diff = now - dt
    if diff.total_seconds() < 60: return "just now"
    elif diff.total_seconds() < 3600: return f"{int(diff.total_seconds() // 60)}m ago"
    elif diff.total_seconds() < 86400: return f"{int(diff.total_seconds() // 3600)}h ago"
    else: return f"{int(diff.total_seconds() // 86400)}d ago"


# ---------- Sidebar ----------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">📞</div>
        <div>
            <div class="sidebar-title">NagrikSeva</div>
            <div class="sidebar-subtitle">AI Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "",
        ["Overview", "Live Calls", "Grievances", "Analytics", "Campaign"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("""
    <div style="margin-top: 50vh;"></div>
    <div class="status-online">
        <span class="dot-green"></span> System Online
    </div>
    """, unsafe_allow_html=True)


# ========== PAGE 1: OVERVIEW ==========

if page == "Overview":
    st.markdown('<div class="page-title">Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time civic grievance monitoring</div>', unsafe_allow_html=True)
    
    stats = load_stats()
    
    # Metrics manually layout using columns to mimic flexbox
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #f97316;">
            <div class="m-title">Total Grievances</div>
            <div class="m-value m-val-orange">{stats.get('total', 0):,}</div>
            <div class="m-sub">+{stats.get('today_count', 0)} today</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        open_count = stats.get('by_status', {}).get('open', 0)
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #f59e0b;">
            <div class="m-title">Open Tickets</div>
            <div class="m-value m-val-yellow">{open_count:,}</div>
            <div class="m-sub">Needs attention</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        resolved = stats.get('by_status', {}).get('resolved', 0)
        total = stats.get('total', 1) or 1
        pct = round((resolved / total) * 100)
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #10b981;">
            <div class="m-title">Resolved Today</div>
            <div class="m-value m-val-green">{resolved:,}</div>
            <div class="m-sub">{pct}% resolution rate</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        avg_s = int(stats.get('avg_call_duration', 0))
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #3b82f6;">
            <div class="m-title">Avg Call Duration</div>
            <div class="m-value">{avg_s}s</div>
            <div class="m-sub">Down 12s from yesterday</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    chart_col1, chart_col2 = st.columns([1, 1.2])
    
    with chart_col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Grievances by Category</div>', unsafe_allow_html=True)
        cat_data = stats.get("by_category", {})
        filtered = {k: v for k, v in cat_data.items() if v > 0}
        if filtered:
            fig = px.pie(names=list(filtered.keys()), values=list(filtered.values()), hole=0.6)
            fig.update_traces(textinfo='none', marker=dict(colors=["#f97316", "#3b82f6", "#f59e0b", "#10b981", "#64748b"]))
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig, use_container_width=True, height=280)
        else:
            st.info("No data yet.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with chart_col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Last 7 Days Volume</div>', unsafe_allow_html=True)
        # Mock 7 days data for visual
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        vals = [42, 58, 35, 68, 49, 31, 23]
        fig = go.Figure(data=[go.Bar(x=days, y=vals, marker_color="#f97316", marker_line_width=0)])
        fig.update_layout(**PLOTLY_LAYOUT, yaxis=dict(showgrid=True, gridcolor="#1e293b"))
        st.plotly_chart(fig, use_container_width=True, height=280)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Live Feed Table
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title"><span class="dot-red"></span> Live Feed</div>', unsafe_allow_html=True)
    
    grievances = load_grievances(5)
    if grievances:
        table_html = "<table class='custom-table'><tr><th>Ticket ID</th><th>Name</th><th>Ward</th><th>Category</th><th>Status</th><th>Time</th></tr>"
        for g in grievances:
            tid = g.get('ticket_id', 'N/A')
            name = g.get('citizen_name', 'Unknown')
            ward = g.get('ward', 'N/A')
            cat = get_cat_icon(g.get('category', 'other'))
            status = get_status_pill(g.get('status', 'open'))
            time_ago = format_time_ago(g.get('created_at', None))
            
            table_html += f"<tr><td class='td-ticket'>{tid}</td><td>{name}</td><td class='td-dim'>{ward}</td><td><span class='td-icon'></span>{cat}</td><td>{status}</td><td class='td-dim'>{time_ago}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No live feed data.")
    st.markdown('</div>', unsafe_allow_html=True)


# ========== PAGE 2: LIVE CALLS ==========

elif page == "Live Calls":
    st.markdown('<div class="page-title">Live Calls</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Active call monitoring & transcription</div>', unsafe_allow_html=True)
    
    # Get the most recent grievance
    recent_grievances = load_grievances(1)
    
    if recent_grievances:
        active_call = recent_grievances[0]
        phone = active_call.get('phone', 'Unknown Number')
        name = active_call.get('citizen_name', 'Unknown Caller')
        if not name: name = "Unknown Caller"
        ward = active_call.get('ward', 'Unknown Location')
        district = active_call.get('district', '')
        loc = f"{ward}, {district}" if district else ward
        lang = active_call.get('language', 'Hinglish').title()
        lang_icon = "🇮🇳" if "Hi" in lang else "🇬🇧"
        status = active_call.get('status', 'open')
        
        # Calculate duration
        created_at = active_call.get('created_at')
        duration_str = "00:00"
        if created_at and hasattr(created_at, 'timestamp'):
            now = datetime.now(timezone.utc)
            diff_seconds = int((now - created_at).total_seconds())
            if status in ['open', 'in_progress'] and diff_seconds < 300: # Assume active if < 5 mins
                mins, secs = divmod(diff_seconds, 60)
                duration_str = f"{mins:02d}:{secs:02d}"
            else:
                dur = active_call.get('call_duration_s', 0)
                mins, secs = divmod(dur, 60)
                duration_str = f"{mins:02d}:{secs:02d}"

        badge_txt = "LIVE" if status in ['open', 'in_progress'] else "ENDED"
        badge_bg = "#10b981" if badge_txt == "LIVE" else "#64748b"

        # Stages logic (simplified mock logic based on data presence)
        stages = [
            ("Greeting", True),
            ("Identity", bool(name and name != "Unknown Caller")),
            ("Location", bool(ward and ward != "Unknown Location")),
            ("Grievance", active_call.get('category') != 'other'),
            ("Confirmation", status in ['resolved', 'escalated'])
        ]
        
        stages_html = ""
        for stage_name, is_complete in stages:
            cls = "badge-orange" if is_complete else "badge-gray"
            stages_html += f'<span class="{cls}">{stage_name}</span>\n'

        # Chat History
        chat_history = active_call.get("chat_history", [])
        transcript_html = ""
        if not chat_history:
            transcript_html = '<span class="t-text">Waiting for speech...</span><br><br>'
        else:
            for msg in chat_history:
                role = msg.get("role", "")
                text = msg.get("content", "")
                if role in ["assistant", "agent"]:
                    transcript_html += f'<span class="t-agent">AGENT:</span> <span class="t-text">{text}</span><br><br>\n'
                elif role in ["user", "citizen"]:
                    transcript_html += f'<span class="t-citizen">CITIZEN:</span> <span class="t-text">{text}</span><br><br>\n'
        
        # Add blinking cursor if live
        if badge_txt == "LIVE":
            transcript_html += '<span style="color: #f97316; animation: blink 1s infinite;">█</span>'

        st.markdown(f"""
        <div class="panel">
            <div class="live-call-header">
                <div class="caller-avatar" style="background: {badge_bg};"><div class="live-badge" style="background: {badge_bg};">{badge_txt}</div></div>
                <div>
                    <div style="font-weight: 600; font-size: 1.1rem; color: #f8fafc;">{phone} — {name}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">{loc}</div>
                    <div style="margin-top: 0.4rem;">
                        <span style="font-size: 0.75rem; color: #64748b;">🌐 {lang_icon} {lang}</span>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 1rem; flex-wrap: wrap;">
                <span style="font-family: monospace; font-size: 0.9rem; font-weight: bold; color: #f8fafc; margin-right: 1rem;">{duration_str} ⏱</span>
                {stages_html}
            </div>
            
            <div class="transcript-box">
                {transcript_html}
            </div>
        </div>
        <style>@keyframes blink {{ 50% {{ opacity: 0; }} }}</style>
        """, unsafe_allow_html=True)
    else:
        st.info("No calls recorded yet.")
    
    # 3 Metrics below
    stats = load_stats()
    today_count = stats.get('today_count', 0)
    avg_s = int(stats.get('avg_call_duration', 0))
    resolved = stats.get('by_status', {}).get('resolved', 0)
    total = stats.get('total', 1) or 1
    pct = round((resolved / total) * 100)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #f97316;">
            <div class="m-title">Calls Today</div>
            <div class="m-value m-val-orange">{today_count}</div>
            <div class="m-sub">Total inbound & outbound</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #f59e0b;">
            <div class="m-title">Avg Duration</div>
            <div class="m-value m-val-yellow">{avg_s}s</div>
            <div class="m-sub">Target: < 120s</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="m-card" style="border-top: 2px solid #10b981;">
            <div class="m-title">Resolution Rate</div>
            <div class="m-value m-val-green">{pct}%</div>
            <div class="m-sub">Overall completion</div>
        </div>
        """, unsafe_allow_html=True)


# ========== PAGE 3: GRIEVANCES ==========

elif page == "Grievances":
    st.markdown('<div class="page-title">Grievances</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage and track citizen grievances</div>', unsafe_allow_html=True)
    
    # Search / Filter mock UI
    cols = st.columns([3, 1, 1, 1, 1])
    with cols[0]:
        st.text_input("", placeholder="🔍 Search by name, ticket ID, ward...", label_visibility="collapsed")
    with cols[1]:
        st.selectbox("", ["All Status"], label_visibility="collapsed")
    with cols[2]:
        st.selectbox("", ["All Categories"], label_visibility="collapsed")
    with cols[3]:
        st.selectbox("", ["All Wards"], label_visibility="collapsed")
    with cols[4]:
        st.button("📥 Export", use_container_width=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    grievances = load_grievances(20)
    if grievances:
        table_html = "<div class='panel' style='padding:0;'><table class='custom-table' style='margin:0;'><tr><th>Ticket ID</th><th>Citizen Name</th><th>Ward & District</th><th>Category</th><th>Language</th><th>Status</th><th>Created</th><th>Actions</th></tr>"
        for g in grievances:
            tid = g.get('ticket_id', 'N/A')
            name = g.get('citizen_name', 'Unknown')
            ward = g.get('ward', 'N/A')
            district = g.get('district', '')
            loc = f"{ward}, {district}" if district else ward
            cat = get_cat_icon(g.get('category', 'other'))
            lang = g.get('language', 'Hinglish').title()
            lang_icon = "🇮🇳" if "Hi" in lang else "🇬🇧"
            status = get_status_pill(g.get('status', 'open'))
            time_ago = format_time_ago(g.get('created_at', None))
            
            table_html += f"<tr><td class='td-ticket'>{tid}</td><td>{name}</td><td class='td-dim'>{loc}</td><td>{cat}</td><td class='td-dim'>{lang_icon} {lang}</td><td>{status}</td><td class='td-dim'>{time_ago}</td><td class='td-dim' style='cursor:pointer;'>👁️</td></tr>"
        table_html += "</table></div>"
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No grievances found.")


# ========== PAGE 4: ANALYTICS ==========

elif page == "Analytics":
    st.markdown('<div class="page-title">Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Deep-dive into grievance data</div>', unsafe_allow_html=True)
    
    r1c1, r1c2 = st.columns(2)
    stats = load_stats()
    
    with r1c1:
        st.markdown('<div class="panel"><div class="panel-title">Grievances by Ward</div>', unsafe_allow_html=True)
        ward_data = stats.get("by_ward", {})
        if ward_data:
            # Mock stacked bar visualization
            top_wards = dict(sorted(ward_data.items(), key=lambda x: x[1], reverse=True)[:7])
            fig = px.bar(
                x=list(top_wards.keys()), y=list(top_wards.values()),
                color_discrete_sequence=["#f97316"]
            )
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, height=250)
        else:
            st.info("No data")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with r1c2:
        st.markdown('<div class="panel"><div class="panel-title">Resolution Time Trend (30 days)</div>', unsafe_allow_html=True)
        # Mock Line Chart
        x_d = list(range(1, 31))
        y_d = [random.randint(30, 70) for _ in x_d]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_d, y=y_d, mode='lines', line=dict(color="#f97316", width=2)))
        fig.add_hline(y=48, line_dash="dash", line_color="#ef4444")
        fig.update_layout(**PLOTLY_LAYOUT, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1e293b"))
        st.plotly_chart(fig, use_container_width=True, height=250)
        st.markdown('</div>', unsafe_allow_html=True)
        
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="panel"><div class="panel-title">Language Distribution</div>', unsafe_allow_html=True)
        lang_data = stats.get("by_language", {})
        if lang_data:
            fig = px.pie(names=list(lang_data.keys()), values=list(lang_data.values()), hole=0.5)
            fig.update_traces(textinfo='none', marker=dict(colors=["#f97316", "#f59e0b", "#003366"]))
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True, height=250)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with r2c2:
        st.markdown('<div class="panel"><div class="panel-title">Call Volume Heatmap</div>', unsafe_allow_html=True)
        # Mock Heatmap 
        z = [[random.randint(0, 100) for _ in range(24)] for _ in range(7)]
        fig = px.imshow(z, color_continuous_scale="Oranges", labels=dict(y="Day", x="Hour"))
        fig.update_yaxes(ticktext=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], tickvals=list(range(7)))
        fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, height=250)
        st.markdown('</div>', unsafe_allow_html=True)


# ========== PAGE 5: CAMPAIGN ==========

elif page == "Campaign":
    st.markdown('<div class="page-title">Campaign</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Launch outbound follow-up campaigns</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Campaign Configuration</div>', unsafe_allow_html=True)
    
    hours = st.slider("Call grievances older than", min_value=12, max_value=168, value=48, format="%dh")
    
    st.markdown('<div style="margin-top:1rem; margin-bottom:0.5rem; font-size:0.85rem; color:#f8fafc;">Categories</div>', unsafe_allow_html=True)
    st.markdown("""
        <span class="badge-orange">Roads</span>
        <span class="badge-orange">Water</span>
        <span class="badge-orange">Electricity</span>
        <span class="badge-orange">Sanitation</span>
        <span class="badge-orange">Health</span>
        <span class="badge-orange">Other</span>
    """, unsafe_allow_html=True)
    
    try:
        eligible = database.get_open_old_grievances(hours=hours)
        count = len(eligible)
    except:
        count = 0
        eligible = []
        
    st.markdown(f"""
    <div style="background-color:#0b101b; border:1px solid #1e293b; padding:1rem; border-radius:8px; margin-top:2rem; margin-bottom:1rem;">
        <span style="color:#94a3b8;">This will trigger calls to</span> <span style="color:#f97316; font-weight:700;">{count}</span> <span style="color:#94a3b8;">citizens</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Launch Campaign", type="primary", use_container_width=True, disabled=(count==0)):
        with st.spinner("Launching outbound calls..."):
            try:
                base_url = os.getenv("BASE_URL", "http://localhost:8000")
                resp = requests.post(f"{base_url}/outbound/trigger", params={"hours": hours}, timeout=120)
                st.success(f"✅ Campaign launched! (Processed {resp.json().get('triggered', 0)} calls)")
            except Exception as e:
                st.error(f"Failed to launch campaign: {e}")
                
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Campaign History 
    st.markdown('<div class="panel" style="padding:0;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title" style="padding: 1.2rem;">Campaign History</div>', unsafe_allow_html=True)
    
    # Mock data for campaign history
    history_html = """
    <table class='custom-table' style='margin:0;'>
        <tr><th>Campaign ID</th><th>Launched</th><th>Citizens Called</th><th>Completed</th><th>Success Rate</th></tr>
        <tr><td class='td-ticket'>CMP-001</td><td class='td-dim'>2h ago</td><td>89</td><td>84</td><td class='t-citizen'>94%</td></tr>
        <tr><td class='td-ticket'>CMP-002</td><td class='td-dim'>Yesterday</td><td>203</td><td>189</td><td class='t-citizen'>93%</td></tr>
        <tr><td class='td-ticket'>CMP-003</td><td class='td-dim'>2 days ago</td><td>156</td><td>141</td><td class='t-citizen'>90%</td></tr>
        <tr><td class='td-ticket'>CMP-004</td><td class='td-dim'>3 days ago</td><td>312</td><td>287</td><td class='t-citizen'>92%</td></tr>
    </table>
    """
    st.markdown(history_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

