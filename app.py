import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="AuraFlow | Smart Scheduler", page_icon="🕒", layout="wide")

# Helper to ensure EVERY time object is UAE-aware (fixes the TypeError)
def get_uae_now():
    uae_tz = pytz.timezone('Asia/Dubai')
    return datetime.now(uae_tz)

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .metric-card {
        background: white; padding: 24px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #F0F2F6;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSISTENT STATE ---
# Crucial: Initialize these with get_uae_now() to avoid the mismatch
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state:
    st.session_state.notified_cache = set()

# --- 3. LOGIC ---
now = get_uae_now()
curr_time_hm = now.strftime("%H:%M")

# --- 4. UI LAYOUT ---
c_title, c_clock = st.columns([4, 1])
with c_title:
    st.title("Good afternoon! 👋")
    st.caption(f"UAE Time: {now.strftime('%A, %b %d')}")
with c_clock:
    st.markdown(f'<div class="metric-card"><b>{now.strftime("%H:%M:%S")}</b></div>', unsafe_allow_html=True)

# Metrics
m1, m2, m3, m4 = st.columns(4)
done_tasks = len([t for t in st.session_state.tasks if t.get('status') == 'Done'])
with m1: st.markdown(f'<div class="metric-card"><span>Tasks Done</span><h3>{done_tasks}</h3></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><span>Water Log</span><h3>{st.session_state.water_ml}ml</h3></div>', unsafe_allow_html=True)
with m3: st.markdown('<div class="metric-card"><span>Focus Time</span><h3>2.2h</h3></div>', unsafe_allow_html=True)
with m4: st.markdown('<div class="metric-card"><span>Streak</span><h3>12</h3></div>', unsafe_allow_html=True)

# --- 5. TASK QUEUE ---
st.write("### 📋 Scheduled Reminders")
for i, t in enumerate(st.session_state.tasks):
    if t['status'] == 'Pending':
        col_a, col_b = st.columns([5, 1])
        col_a.info(f"**{t['time']}** — {t['name']}")
        if col_b.button("Done", key=f"d_{i}"):
            t['status'] = 'Done'
            st.rerun()

# --- 6. ADD NEW ---
with st.expander("➕ Set New Reminder"):
    c1, c2 = st.columns(2)
    name = c1.text_input("What's the task?")
    tm = c2.text_input("Time (HH:MM)", value=curr_time_hm)
    if st.button("Add to Schedule"):
        st.session_state.tasks.append({"name": name, "time": tm, "status": "Pending"})
        st.rerun()

# --- 7. ANALYSIS (Fix for Streamlit 2026 Warning) ---
st.write("### 📈 Analytics")
df_week = pd.DataFrame({'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 'Tasks': [5, 4, 7, 2, 5, 8, 3]})
fig = px.bar(df_week, x='Day', y='Tasks', color_discrete_sequence=['#A7F3D0'])

# UPDATED: Use width='stretch' instead of use_container_width=True
st.plotly_chart(fig, width='stretch')

# --- 8. NOTIFICATION & TIME CHECK (The Crash Fix) ---

# This line was crashing because 'now' and 'last_water_check' must both be UAE-aware
time_diff = now - st.session_state.last_water_check
if time_diff.total_seconds() / 60 >= 30:
    st.toast("💧 UAE Hydration: Time to drink water!", icon="🥛")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now

# Exact Time Notifications
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_time_hm:
        notif_id = f"{t['name']}_{curr_time_hm}"
        if notif_id not in st.session_state.notified_cache:
            st.toast(f"⏰ ALERT: {t['name']} starting now!", icon="🔔")
            st.session_state.notified_cache.add(notif_id)

# Heartbeat: Refresh every second to keep clock and notifications live
time.sleep(1)
st.rerun()
