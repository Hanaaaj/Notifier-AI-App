import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import time

# --- 1. GLOBAL SYNC & CONFIG ---
st.set_page_config(page_title="AuraFlow | Unified Assistant", page_icon="🚀", layout="wide")

def get_uae_now():
    """Universal UAE time sync to prevent TypeError."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# --- 2. DATA INITIALIZATION ---
if 'data' not in st.session_state: st.session_state.data = []
if 'water_ml' not in st.session_state: st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state: st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state: st.session_state.notified_cache = set()

# --- 3. THEME & STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); text-align: center;
        border: 1px solid #F0F2F6;
    }
    .study-box { border-left: 5px solid #6366F1; background: #EEF2FF; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .work-box { border-left: 5px solid #10B981; background: #ECFDF5; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .health-box { border-left: 5px solid #F59E0B; background: #FFFBEB; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ENGINE LOGIC ---
now = get_uae_now()
curr_time_hm = now.strftime("%H:%M")

# --- 5. SIDEBAR: MODULE & AI TIMETABLE BUILDER ---
with st.sidebar:
    st.header("🤖 AI Timetable Generator")
    mode = st.radio("Choose Mode", ["Study (Modules)", "Work (Projects)"])
    
    name = st.text_input("Module/Project Name")
    topics = st.text_area("List Topics/Tasks (one per line)")
    
    if st.button("Generate AI Schedule"):
        if name and topics:
            items = [i.strip() for i in topics.split('\n') if i.strip()]
            start_time = datetime.combine(now.date(), datetime.strptime("09:00", "%H:%M").time())
            
            for i, item in enumerate(items):
                # Work/Study Session (60 mins)
                t_start = (start_time + timedelta(minutes=i*90)).strftime("%H:%M")
                st.session_state.data.append({
                    "name": f"{mode}: {item}", "track": mode, "type": "Deep Work", 
                    "time": t_start, "status": "Pending"
                })
                # Break Session (30 mins)
                b_start = (start_time + timedelta(minutes=i*90 + 60)).strftime("%H:%M")
                st.session_state.data.append({
                    "name": f"Break & Stretch ({name})", "track": "Health", "type": "Break", 
                    "time": b_start, "status": "Pending"
                })
            st.success("Timetable Generated!")
            st.rerun()
    
    st.divider()
    if st.button("Reset All Data"):
        st.session_state.data = []
        st.session_state.water_ml = 0
        st.rerun()

# --- 6. MAIN DASHBOARD ---
st.title("AuraFlow Unified Assistant 🇦🇪")
st.caption(f"Real-time: {now.strftime('%H:%M:%S')} GST")

# Metrics
m1, m2, m3, m4 = st.columns(4)
study_p = [t for t in st.session_state.data if t['track'] == "Study (Modules)"]
work_p = [t for t in st.session_state.data if t['track'] == "Work (Projects)"]

with m1:
    s_done = len([t for t in study_p if t['status'] == 'Done'])
    st.markdown(f'<div class="metric-card"><span>📚 Study Progress</span><h3>{s_done}/{len(study_p)}</h3></div>', unsafe_allow_html=True)
with m2:
    w_done = len([t for t in work_p if t['status'] == 'Done'])
    st.markdown(f'<div class="metric-card"><span>💼 Work Progress</span><h3>{w_done}/{len(work_p)}</h3></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><span>💧 Water Intake</span><h3>{st.session_state.water_ml}ml</h3></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><span>⏱️ Current Time</span><h3>{curr_time_hm}</h3></div>', unsafe_allow_html=True)

# --- 7. TASK TRACKING & ANALYTICS ---
tab_tasks, tab_analytics = st.tabs(["📋 Task Manager", "📈 Progress Reports"])

with tab_tasks:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Current Focus")
        for i, t in enumerate(st.session_state.data):
            if t['status'] == "Pending":
                style = "study-box" if "Study" in t['track'] else "work-box" if "Work" in t['track'] else "health-box"
                c1, c2 = st.columns([4, 1])
                c1.markdown(f'<div class="{style}"><strong>{t["time"]}</strong> — {t["name"]}</div>', unsafe_allow_html=True)
                if c2.button("Done", key=f"d_{i}"):
                    t['status'] = "Done"
                    st.rerun()
                    
    with col_b:
        st.subheader("Manual Quick Entry")
        q_name = st.text_input("Quick Task Name")
        q_time = st.text_input("Time (HH:MM)", value=curr_time_hm)
        q_track = st.selectbox("Category", ["Study (Modules)", "Work (Projects)", "Health"])
        if st.button("Add Task"):
            st.session_state.data.append({"name": q_name, "time": q_time, "track": q_track, "status": "Pending"})
            st.rerun()

with tab_analytics:
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.subheader("Completion Analysis")
        fig = px.bar(df, x="track", color="status", barmode="group", color_discrete_map={"Done": "#10B981", "Pending": "#E2E8F0"})
        st.plotly_chart(fig, width="stretch")
        
        st.subheader("Focus Distribution")
        fig2 = px.pie(df, names="track", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig2, width="stretch")

# --- 8. THE NOTIFICATION ENGINE ---

# 💧 10-Minute Hydration & Eye-Rest Check
time_since_last = (now - st.session_state.last_water_check).total_seconds() / 60
if time_since_last >= 10:
    st.toast("💧 HYDRATION: Drink water now to keep your brain sharp!", icon="🥤")
    st.toast("👁️ EYE REST: Look 20 feet away for 20 seconds.", icon="🧘")
    st.session_state.water_ml += 150
    st.session_state.last_water_check = now

# 🔔 Scheduled Task Alerts
for t in st.session_state.data:
    if t['status'] == "Pending" and t['time'] == curr_time_hm:
        nid = f"{t['name']}_{curr_time_hm}"
        if nid not in st.session_state.notified_cache:
            st.toast(f"⏰ STARTING NOW: {t['name']}", icon="🔔")
            st.session_state.notified_cache.add(nid)

# Heartbeat: Refresh every second for real-time notifications
time.sleep(1)
st.rerun()
