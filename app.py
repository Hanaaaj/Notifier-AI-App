import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import pytz
import time

# --- 1. GLOBAL SYNC & CONFIG ---
st.set_page_config(page_title="AuraFlow | Unified Assistant", page_icon="🚀", layout="wide")

def get_uae_now():
    """Universal UAE time sync to prevent TypeErrors."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# --- 2. DATA INITIALIZATION ---
# Standardizing keys: We use 'name', 'date', 'type', and 'time' across all modules
if 'deadlines' not in st.session_state: st.session_state.deadlines = []
if 'meetings' not in st.session_state: st.session_state.meetings = []
if 'tasks' not in st.session_state: st.session_state.tasks = []
if 'water_ml' not in st.session_state: st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state: st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state: st.session_state.notified_cache = set()

# --- 3. THE AI BRAIN ---
def get_ai_suggestions():
    now = get_uae_now()
    suggs = []
    
    # Study Logic
    for dl in st.session_state.deadlines:
        days_to = (dl['date'] - now.date()).days
        if 0 < days_to <= 7:
            suggs.append({"title": f"Prep: {dl['name']}", "desc": f"Deadline in {days_to} days. Start reviewing now.", "cat": "Study"})

    # Work & Health Logic
    if len(st.session_state.meetings) > 2:
        suggs.append({"title": "Back-to-Back Meetings", "desc": "Schedule a 5-min eye rest after your next call.", "cat": "Work"})
    
    suggs.append({"title": "Hydration Target", "desc": "You're at 60% of your daily water goal.", "cat": "Health"})
    return suggs

# --- 4. SIDEBAR & UTILITIES ---
with st.sidebar:
    st.title("Settings")
    if st.button("Reset All Data"):
        st.session_state.deadlines = []
        st.session_state.meetings = []
        st.session_state.tasks = []
        st.session_state.water_ml = 0
        st.session_state.notified_cache = set()
        st.rerun()
    st.divider()
    st.write("Logged in as: Student/Professional")

# --- 5. MAIN UI ---
now = get_uae_now()
curr_time = now.strftime("%H:%M")

st.title("AuraFlow: Study, Work & Health 🇦🇪")
st.caption(f"UAE Time: {now.strftime('%H:%M:%S')} | Dashboard Active")

tabs = st.tabs(["🎓 Study", "💼 Work", "🏥 Health", "✨ AI Insights"])

# --- STUDY TAB ---
with tabs[0]:
    st.subheader("Exam & Project Tracker")
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("study_input", clear_on_submit=True):
            # FIXED: Ensuring key name matches 'name'
            d_name = st.text_input("Subject/Module Name")
            d_type = st.selectbox("Type", ["Exam", "Project", "Assignment"])
            d_date = st.date_input("Deadline Date", min_value=now.date())
            if st.form_submit_button("Log Deadline"):
                st.session_state.deadlines.append({"name": d_name, "type": d_type, "date": d_date})
                st.rerun()
    with col2:
        if not st.session_state.deadlines: st.info("No deadlines logged.")
        for dl in sorted(st.session_state.deadlines, key=lambda x: x['date']):
            st.warning(f"⏳ **{dl['date']}** | {dl['name']} ({dl['type']})")

# --- WORK TAB ---
with tabs[1]:
    st.subheader("Meeting & Task Manager")
    w1, w2 = st.columns([1, 2])
    with w1:
        with st.form("work_input"):
            m_name = st.text_input("Meeting/Task Title")
            m_time = st.text_input("Time (HH:MM)", value=curr_time)
            if st.form_submit_button("Add to Schedule"):
                st.session_state.meetings.append({"name": m_name, "time": m_time})
                st.rerun()
    with w2:
        if st.session_state.meetings:
            st.table(pd.DataFrame(st.session_state.meetings))

# --- HEALTH TAB ---
with tabs[2]:
    st.subheader("Wellness Dashboard")
    h1, h2, h3 = st.columns(3)
    h1.metric("Hydration", f"{st.session_state.water_ml}ml")
    h2.metric("Screen Breaks", f"{len(st.session_state.tasks)} done")
    h3.metric("Status", "Balanced")
    
    # Future-proof Chart
    df_h = pd.DataFrame({'Goal': ['Water', 'Focus', 'Exercise'], 'Score': [st.session_state.water_ml/15, 75, 50]})
    fig = px.line_polar(df_h, r='Score', theta='Goal', line_close=True)
    st.plotly_chart(fig, width="stretch")

# --- AI TAB ---
with tabs[3]:
    st.subheader("AI Smart Suggestions")
    for s in get_ai_suggestions():
        st.info(f"**{s['cat']}**: {s['title']} \n\n {s['desc']}")

# --- 6. REAL-TIME NOTIFIER ---
# Water reminder logic
if (now - st.session_state.last_water_check).total_seconds() / 60 >= 30:
    st.toast("💧 Time to hydrate! Logging 250ml...", icon="🥛")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now

# Exact time alerts (Meetings/Tasks)
combined_alerts = st.session_state.meetings + st.session_state.tasks
for a in combined_alerts:
    if a.get('time') == curr_time:
        nid = f"{a['name']}_{curr_time}"
        if nid not in st.session_state.notified_cache:
            st.toast(f"🔔 ALERT: {a['name']} starting now!", icon="⏰")
            st.session_state.notified_cache.add(nid)

time.sleep(1)
st.rerun()
