import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime
import pytz  # Handles UAE Timezone
import time

# --- 1. SETTINGS & UAE TIME LOGIC ---
st.set_page_config(page_title="AuraFlow | UAE Smart Scheduler", page_icon="🇦🇪", layout="wide")

def get_uae_time():
    """Returns the current time in UAE (Asia/Dubai)"""
    uae_tz = pytz.timezone('Asia/Dubai')
    return datetime.now(uae_tz)

# --- 2. MODERN MIND-FLOW STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .metric-card {
        background: white; padding: 20px; border-radius: 18px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02); border: 1px solid #F0F2F6;
        text-align: center;
    }
    .task-box {
        background: white; padding: 15px; border-radius: 12px;
        border-left: 5px solid #0073e6; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .uae-flag { font-size: 20px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_time()

# --- 4. TOP BAR: UAE CLOCK ---
now_uae = get_uae_time()
curr_time_str = now_uae.strftime("%H:%M")

c1, c2 = st.columns([4, 1])
with c1:
    st.title(f"Good afternoon! 👋")
    st.markdown(f"**UAE Standard Time:** {now_uae.strftime('%A, %d %B')} <span class='uae-flag'>🇦🇪</span>", unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><h2 style="margin:0;">{curr_time_str}</h2><small>GST (UTC+4)</small></div>', unsafe_allow_html=True)

# --- 5. SMART NOTIFICATION ENGINE ---
# Check for Water Reminder (Every 30 Mins)
time_since_water = (now_uae - st.session_state.last_water_check).total_seconds() / 60
if time_since_water >= 30:
    st.toast("💧 UAE Health Alert: Time to hydrate! (30m Interval Reached)", icon="🥛")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now_uae

# Check for Scheduled Task Notifications
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_time_str:
        # We use a unique key to ensure notification only fires once per minute
        notif_key = f"notif_{t['name']}_{curr_time_str}"
        if notif_key not in st.session_state:
            st.toast(f"🔔 UAE SCHEDULER: Starting '{t['name']}' now!", icon="⏰")
            st.session_state[notif_key] = True

# --- 6. METRICS & DASHBOARD ---
m1, m2, m3, m4 = st.columns(4)
done_count = len([t for t in st.session_state.tasks if t['status'] == 'Done'])

with m1: st.markdown(f'<div class="metric-card"><span>Tasks</span><h3>{done_count}</h3></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><span>Water</span><h3>{st.session_state.water_ml}ml</h3></div>', unsafe_allow_html=True)
with m3: st.markdown('<div class="metric-card"><span>Focus</span><h3>0.8h</h3></div>', unsafe_allow_html=True)
with m4: st.markdown('<div class="metric-card"><span>Streak</span><h3>12</h3></div>', unsafe_allow_html=True)

# --- 7. SMART SUGGESTIONS ---
st.markdown("### ✨ AI Smart Suggestions")
suggestions = [
    {"title": "20/20/20 Rule", "desc": "Look 20 feet away to rest your eyes", "cat": "Health"},
    {"title": "Afternoon Walk", "desc": "Perfect UAE weather for a 5m stretch", "cat": "Personal"}
]
for s in suggestions:
    sc1, sc2 = st.columns([5, 1])
    sc1.info(f"**{s['title']}** - {s['desc']}")
    if sc2.button("Add", key=s['title']):
        st.session_state.tasks.append({"name": s['title'], "cat": s['cat'], "time": curr_time_str, "status": "Pending"})
        st.rerun()

# --- 8. TASK QUEUE & SCHEDULING ---
st.markdown("### 📋 UAE Smart Schedule")

# Form to add new timed reminders
with st.expander("➕ Schedule New Event (UAE Time)"):
    tc1, tc2, tc3 = st.columns(3)
    name = tc1.text_input("Meeting/Task Name")
    tm = tc2.text_input("Time (e.g. 10:00 or 15:45)", value=curr_time_str)
    cat = tc3.selectbox("Category", ["Work", "Study", "Health", "Personal"])
    if st.button("Set UAE Reminder"):
        st.session_state.tasks.append({"name": name, "cat": cat, "time": tm, "status": "Pending"})
        st.rerun()

# Display List (Sorted by AI Importance)
importance = {"Work": 1, "Study": 2, "Health": 3, "Personal": 4}
sorted_tasks = sorted(st.session_state.tasks, key=lambda x: importance.get(x['cat'], 99))

for i, t in enumerate(sorted_tasks):
    if t['status'] == "Pending":
        st.markdown(f"""
            <div class="task-box">
                <div><b>{t['time']}</b> | {t['name']} <small style="color:gray;">({t['cat']})</small></div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Mark Complete", key=f"d_{i}"):
            t['status'] = "Done"
            st.rerun()

# --- 9. AUTO-REFRESH (Keep Clock Ticking) ---
# This causes the page to rerun frequently to check the time
time.sleep(1)
st.rerun()
