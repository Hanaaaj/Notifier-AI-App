import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz  # Required for UAE Time
import time

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="AuraFlow | UAE Smart Scheduler", page_icon="🕒", layout="wide")

# Function to get UAE Time (Prevents the TypeError mismatch)
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
    .suggestion-box {
        background-color: #FDF4FF; padding: 16px; border-radius: 12px;
        border: 1px solid #FAE8FF; margin-bottom: 12px;
    }
    .badge-ai { background: #F3E8FF; color: #7E22CE; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSISTENT STATE ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state:
    st.session_state.notified_cache = set() # Prevents duplicate alerts in same minute

# --- 3. INTELLIGENCE FUNCTIONS ---

def get_ai_priority(task_list):
    weights = {"Work": 50, "Study": 40, "Health": 30, "Personal": 10}
    return sorted(task_list, key=lambda x: weights.get(x['cat'], 0), reverse=True)

def get_smart_suggestions():
    suggestions = []
    if st.session_state.water_ml < 1000:
        suggestions.append({"title": "Rehydrate", "desc": "Drink 250ml water now", "cat": "Health"})
    suggestions.append({"title": "20/20/20 Rule", "desc": "Rest your eyes from the screen", "cat": "Health"})
    return suggestions

# --- 4. MAIN UI LAYOUT ---
now = get_uae_now()
curr_time = now.strftime("%H:%M")

c_title, c_clock = st.columns([4, 1])
with c_title:
    st.title(f"Good afternoon! 👋")
    st.caption(f"UAE Standard Time: {now.strftime('%A, %B %d, %Y')}")
with c_clock:
    st.markdown(f'<div class="metric-card"><b>{now.strftime("%H:%M:%S")}</b></div>', unsafe_allow_html=True)

# Metric Grid
m1, m2, m3, m4 = st.columns(4)
done_tasks = [t for t in st.session_state.tasks if t.get('status') == 'Done']

with m1: st.markdown(f'<div class="metric-card"><span>✅ Tasks Done</span><h3>{len(done_tasks)}</h3></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><span>💧 Water</span><h3>{st.session_state.water_ml}ml</h3></div>', unsafe_allow_html=True)
with m3: st.markdown('<div class="metric-card"><span>⏱️ Focus</span><h3>2h 10m</h3></div>', unsafe_allow_html=True)
with m4: st.markdown('<div class="metric-card"><span>🔥 Streak</span><h3>12 Days</h3></div>', unsafe_allow_html=True)

# --- 5. SMART SUGGESTIONS & TASK QUEUE ---
st.markdown("### ✨ Smart Suggestions")
for s in get_smart_suggestions():
    cols = st.columns([5, 1])
    cols[0].markdown(f'<div class="suggestion-box"><strong>{s["title"]}</strong> <span class="badge-ai">AI Suggestion</span><br>{s["desc"]}</div>', unsafe_allow_html=True)
    if cols[1].button("Add", key=s['title']):
        st.session_state.tasks.append({"name": s['title'], "cat": s['cat'], "time": curr_time, "status": "Pending"})
        st.rerun()

st.markdown("---")
st.markdown("### 📋 Daily Schedule")
sorted_queue = get_ai_priority([t for t in st.session_state.tasks if t['status'] == 'Pending'])

for i, t in enumerate(sorted_queue):
    col_a, col_b = st.columns([5, 1])
    col_a.info(f"**{t['time']}** — {t['name']} ({t['cat']})")
    if col_b.button("Done", key=f"d_{i}"):
        for original in st.session_state.tasks:
            if original['name'] == t['name']: original['status'] = 'Done'
        st.rerun()

# --- 6. ADD NEW ---
with st.expander("➕ Create Custom Reminder"):
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Task Name")
    tm = c2.text_input("Time (HH:MM)", value=curr_time)
    cat = c3.selectbox("Category", ["Work", "Study", "Health", "Personal"])
    if st.button("Schedule Task"):
        st.session_state.tasks.append({"name": name, "cat": cat, "time": tm, "status": "Pending"})
        st.rerun()

# --- 7. NOTIFICATION LOOP (THE FIX) ---

# Check 30-min water timer using UAE-aware subtraction
time_delta = now - st.session_state.last_water_check
if time_delta.total_seconds() / 60 >= 30:
    st.toast("💧 Time to hydrate! Logging 250ml...", icon="🥛")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now

# Check for timed meetings/alerts
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_time:
        notif_id = f"{t['name']}_{curr_time}"
        if notif_id not in st.session_state.notified_cache:
            st.toast(f"⏰ REMINDER: {t['name']} is starting!", icon="🔔")
            st.session_state.notified_cache.add(notif_id)

# Real-time refresh (updates clock and checks alerts every second)
time.sleep(1)
st.rerun()
