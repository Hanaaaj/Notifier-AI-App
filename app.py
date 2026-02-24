import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time

# --- 1. GLOBAL SYNC & CONFIG ---
st.set_page_config(page_title="AuraFlow | Progress Tracker", page_icon="📈", layout="wide")

def get_uae_now():
    return datetime.now(pytz.timezone('Asia/Dubai'))

# --- 2. DATA INITIALIZATION ---
if 'data' not in st.session_state:
    st.session_state.data = [] # Single source of truth for all tasks/deadlines
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state:
    st.session_state.notified_cache = set()

# --- 3. UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .status-done { text-decoration: line-through; color: #94A3B8; }
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); text-align: center;
        border: 1px solid #F0F2F6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE LOGIC ---
now = get_uae_now()
curr_time_hm = now.strftime("%H:%M")

# --- 5. TOP HEADER & MAIN METRICS ---
st.title("AuraFlow: Multi-Track Dashboard 🇦🇪")
st.caption(f"Real-time tracking: {now.strftime('%H:%M:%S')}")

m1, m2, m3, m4 = st.columns(4)
study_tasks = [t for t in st.session_state.data if t['track'] == "Study"]
work_tasks = [t for t in st.session_state.data if t['track'] == "Work"]

with m1:
    prog = len([t for t in study_tasks if t['status'] == "Done"]) / len(study_tasks) * 100 if study_tasks else 0
    st.markdown(f'<div class="metric-card"><span>📚 Study Progress</span><h3>{prog:.0f}%</h3></div>', unsafe_allow_html=True)
with m2:
    prog_w = len([t for t in work_tasks if t['status'] == "Done"]) / len(work_tasks) * 100 if work_tasks else 0
    st.markdown(f'<div class="metric-card"><span>💼 Work Progress</span><h3>{prog_w:.0f}%</h3></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><span>💧 Water Intake</span><h3>{st.session_state.water_ml}ml</h3></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><span>🔥 Health Score</span><h3>85/100</h3></div>', unsafe_allow_html=True)

# --- 6. DATA INPUT ---
with st.expander("➕ Add New Task / Deadline / Meeting"):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    name = c1.text_input("Title")
    track = c2.selectbox("Track", ["Study", "Work", "Health"])
    t_type = c3.selectbox("Type", ["Exam", "Project", "Meeting", "Exercise"])
    t_time = c4.text_input("Time (HH:MM)", value=curr_time_hm)
    
    if st.button("Log into AuraFlow"):
        st.session_state.data.append({
            "name": name, "track": track, "type": t_type, 
            "time": t_time, "status": "Pending", "created": now.date()
        })
        st.rerun()

# --- 7. TRACKING DASHBOARDS ---
tab1, tab2, tab3 = st.tabs(["📋 Task Manager", "📈 Progress Analytics", "✨ AI Health Suggestions"])

with tab1:
    col_study, col_work = st.columns(2)
    
    with col_study:
        st.subheader("📚 Study Track")
        for i, t in enumerate(st.session_state.data):
            if t['track'] == "Study" and t['status'] == "Pending":
                c_a, c_b = st.columns([4, 1])
                c_a.info(f"**{t['time']}** — {t['name']} ({t['type']})")
                if c_b.button("Done", key=f"s_{i}"):
                    t['status'] = "Done"
                    st.rerun()

    with col_work:
        st.subheader("💼 Work Track")
        for i, t in enumerate(st.session_state.data):
            if t['track'] == "Work" and t['status'] == "Pending":
                c_a, c_b = st.columns([4, 1])
                c_a.success(f"**{t['time']}** — {t['name']} ({t['type']})")
                if c_b.button("Done", key=f"w_{i}"):
                    t['status'] = "Done"
                    st.rerun()

with tab2:
    st.subheader("Analytics Overview")
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        
        # Performance Chart
        fig = px.bar(df, x="track", color="status", 
                     title="Completion Rates by Category",
                     color_discrete_map={"Done": "#10B981", "Pending": "#E2E8F0"},
                     barmode="group")
        st.plotly_chart(fig, width="stretch")
        
        # Activity History
        fig2 = px.pie(df, names="type", title="Focus Distribution", hole=0.4)
        st.plotly_chart(fig2, width="stretch")

with tab3:
    st.subheader("AI Wellness Insights")
    if len(work_tasks) > 3:
        st.warning("⚠️ **High Workload Detected:** AI suggests a 10-minute 'Screen-Off' break after your next meeting.")
    if st.session_state.water_ml < 1000:
        st.error("⚠️ **Hydration Low:** Your focus may drop. Drink 500ml of water immediately.")
    st.info("💡 **Study Tip:** You have an exam prep session coming up. Review your hardest module first while energy is high.")

# --- 8. LIVE NOTIFICATIONS & WATER ---
# 30-min Health Cycle
if (now - st.session_state.last_water_check).total_seconds() / 60 >= 30:
    st.toast("💧 Hydration & Movement Check!", icon="🧘")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now

# Scheduled Alerts
for t in st.session_state.data:
    if t['status'] == "Pending" and t['time'] == curr_time_hm:
        nid = f"{t['name']}_{curr_time_hm}"
        if nid not in st.session_state.notified_cache:
            st.toast(f"🔔 STARTING NOW: {t['name']}", icon="⏰")
            st.session_state.notified_cache.add(nid)

# Heartbeat
time.sleep(1)
st.rerun()
