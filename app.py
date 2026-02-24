import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import time

# --- 1. SETUP & UAE TIMEZONE ---
st.set_page_config(page_title="AuraFlow Study", page_icon="🎓", layout="wide")

def get_uae_now():
    """Returns a timezone-aware UAE datetime object to prevent TypeErrors."""
    uae_tz = pytz.timezone('Asia/Dubai')
    return datetime.now(uae_tz)

# --- 2. CUSTOM STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); text-align: center;
        border: 1px solid #F0F2F6;
    }
    .suggestion-box {
        background-color: #F0F9FF; border-left: 5px solid #0EA5E9;
        padding: 15px; border-radius: 10px; margin-bottom: 12px;
    }
    .deadline-card {
        background: #FFFBEB; border-left: 5px solid #F59E0B;
        padding: 12px; border-radius: 8px; margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PERSISTENT STATE ---
if 'deadlines' not in st.session_state:
    st.session_state.deadlines = []
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state:
    st.session_state.notified_cache = set()

# --- 4. ENGINE LOGIC ---
now = get_uae_now()
curr_time_hm = now.strftime("%H:%M")

def get_study_suggestions():
    suggestions = []
    # Deadline Proximity Logic
    for dl in st.session_state.deadlines:
        days_left = (dl['date'] - now.date()).days
        if 0 < days_left <= 7:
            suggestions.append({"title": f"Review {dl['subject']}", "desc": f"Only {days_left} days left! Start a 45m block.", "cat": "Study"})
    
    # Standard Wellness AI
    suggestions.append({"title": "Posture Check", "desc": "Stretch your back and neck for 2 mins.", "cat": "Exercise"})
    suggestions.append({"title": "Brain Fuel", "desc": "Hydrate now to improve focus.", "cat": "Health"})
    return suggestions

# --- 5. TOP HEADER ---
c_title, c_clock = st.columns([4, 1])
with c_title:
    st.title("🎓 Study Dashboard")
    st.caption(f"UAE Standard Time | {now.strftime('%A, %b %d, %Y')}")
with c_clock:
    st.markdown(f'<div class="metric-card"><b>{now.strftime("%H:%M:%S")}</b></div>', unsafe_allow_html=True)

# --- 6. DASHBOARD STATS ---
m1, m2, m3 = st.columns(3)
with m1: st.markdown(f'<div class="metric-card"><span>Deadlines</span><h3>{len(st.session_state.deadlines)}</h3></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><span>Next Break</span><h3>25m</h3></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="metric-card"><span>Study Streak</span><h3>4 Days</h3></div>', unsafe_allow_html=True)

# --- 7. INPUT SECTION (SIDEBAR) ---
with st.sidebar:
    st.header("📌 Project/Exam Input")
    sub = st.text_input("Subject/Module Name")
    d_type = st.selectbox("Type", ["Exam", "Project", "Quiz", "Assignment"])
    d_date = st.date_input("Deadline Date", min_value=now.date())
    if st.button("Add to Tracker"):
        st.session_state.deadlines.append({"subject": sub, "type": d_type, "date": d_date})
        st.rerun()

    st.header("⏰ Manual Reminder")
    r_name = st.text_input("Task Title")
    r_time = st.text_input("Time (HH:MM)", value=curr_time_hm)
    if st.button("Set Reminder"):
        st.session_state.tasks.append({"name": r_name, "time": r_time, "status": "Pending", "cat": "Study"})
        st.rerun()

# --- 8. AI STUDY STRATEGY ---
st.subheader("✨ AI Suggestions & Breaks")
for s in get_study_suggestions():
    col_s1, col_s2 = st.columns([5, 1])
    col_s1.markdown(f'<div class="suggestion-box"><strong>[{s["cat"]}] {s["title"]}</strong><br><small>{s["desc"]}</small></div>', unsafe_allow_html=True)
    if col_s2.button("Accept", key=s['title']):
        st.session_state.tasks.append({"name": s['title'], "cat": s['cat'], "time": curr_time_hm, "status": "Pending"})
        st.rerun()

# --- 9. DEADLINES & ANALYTICS ---
st.divider()
c_left, c_right = st.columns(2)

with c_left:
    st.subheader("📅 Upcoming Deadlines")
    for dl in sorted(st.session_state.deadlines, key=lambda x: x['date']):
        st.markdown(f'<div class="deadline-card"><strong>{dl["date"].strftime("%b %d")}</strong> — {dl["subject"]} ({dl["type"]})</div>', unsafe_allow_html=True)

with c_right:
    st.subheader("📊 Workload density")
    if st.session_state.deadlines:
        df = pd.DataFrame(st.session_state.deadlines)
        fig = px.histogram(df, x="date", color_discrete_sequence=['#F59E0B'])
        # FIXED: Using width='stretch' for Streamlit 2026 compatibility
        st.plotly_chart(fig, width='stretch')

# --- 10. LIVE NOTIFICATION SYSTEM ---

# Corrected Time Math (preventing offset-naive vs aware error)
time_diff = now - st.session_state.last_water_check
if time_diff.total_seconds() / 60 >= 30:
    st.toast("💧 UAE Wellness: Drink water and stretch!", icon="🧘")
    st.session_state.last_water_check = now

# Alert logic
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_time_hm:
        notif_id = f"{t['name']}_{curr_time_hm}"
        if notif_id not in st.session_state.notified_cache:
            st.toast(f"🔔 STUDY ALERT: {t['name']}", icon="📖")
            st.session_state.notified_cache.add(notif_id)

# Heartbeat
time.sleep(1)
st.rerun()
