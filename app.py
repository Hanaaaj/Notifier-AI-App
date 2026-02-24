import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# --- 1. CONFIG & MIND-FLOW STYLING ---
st.set_page_config(page_title="AuraFlow | Smart Dashboard", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    
    /* Modern Dashboard Cards */
    .metric-card {
        background-color: white;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        border: 1px solid #F0F2F6;
        margin-bottom: 20px;
    }
    .metric-title { color: #5F6368; font-size: 14px; font-weight: 500; }
    .metric-value { color: #1A1C1E; font-size: 32px; font-weight: 700; margin-top: 8px; }
    
    /* Smart Suggestion Container */
    .suggestion-box {
        background-color: #FDF4FF;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #FAE8FF;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Task Item Styling */
    .task-item {
        background: white; 
        padding: 15px; 
        border-radius: 12px; 
        border-left: 5px solid #4facfe; 
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge-ai { background: #F3E8FF; color: #7E22CE; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE (The Memory) ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0
if 'last_water_time' not in st.session_state:
    st.session_state.last_water_time = datetime.now()
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()

# --- 3. THE ENGINES (Logic Layer) ---

def calculate_priority(task):
    """Rule-based reordering logic"""
    score = 0
    weights = {"Work": 40, "Study": 30, "Health": 20, "Personal": 10}
    score += weights.get(task['cat'], 0)
    # Check if task is within the next hour
    try:
        t_hour = int(task['time'].split(":")[0])
        if t_hour == datetime.now().hour: score += 50
    except: pass
    return score

def get_proactive_suggestions():
    """Generates AI suggestions based on session data"""
    suggs = []
    # Suggest Eye Rest every 20 mins of session time
    session_mins = (datetime.now() - st.session_state.start_time).seconds / 60
    if session_mins > 20:
        suggs.append({"title": "Eye Rest (20/20/20)", "desc": "Look away for 20s", "cat": "Health"})
    
    # Suggest hydration if goal is low
    if st.session_state.water_ml < 1000:
        suggs.append({"title": "Hydration Hit", "desc": "Drink 250ml now", "cat": "Health"})
    return suggs

# --- 4. TOP HEADER & CLOCK ---
now = datetime.now()
curr_str = now.strftime("%H:%M")

c_title, c_clock = st.columns([4, 1])
with c_title:
    st.title(f"Good afternoon! 👋")
    st.caption(f"Today is {now.strftime('%A, %B %d')}")
with c_clock:
    st.markdown(f'<div class="metric-card" style="padding:10px; text-align:center;"><b>{curr_str}</b></div>', unsafe_allow_html=True)

# --- 5. MAIN METRICS ---
m1, m2, m3, m4 = st.columns(4)
done_count = len([t for t in st.session_state.tasks if t['status'] == 'Done'])

with m1:
    st.markdown(f'<div class="metric-card"><span class="metric-title">✅ Tasks Done</span><div class="metric-value">{done_count}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><span class="metric-title">💧 Water Intake</span><div class="metric-value">{st.session_state.water_ml}ml</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><span class="metric-title">⏱️ Session Focus</span><div class="metric-value">42m</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><span class="metric-title">🔥 Streak</span><div class="metric-value">5 Days</div></div>', unsafe_allow_html=True)

# --- 6. SMART SUGGESTIONS ---
st.markdown("### ✨ Smart Suggestions")
for s in get_proactive_suggestions():
    with st.container():
        sc1, sc2 = st.columns([5, 1])
        sc1.markdown(f"""
            <div class="suggestion-box">
                <div><strong>{s['title']}</strong> <span class="badge-ai">AI</span><br><small>{s['desc']}</small></div>
            </div>
        """, unsafe_allow_html=True)
        if sc2.button("Add", key=s['title']):
            st.session_state.tasks.append({"name": s['title'], "cat": s['cat'], "status": "Pending", "time": curr_str})
            st.rerun()

# --- 7. TASK QUEUE (AI ORDERED) ---
st.markdown("### 📋 Scheduled Reminders")
sorted_tasks = sorted(st.session_state.tasks, key=calculate_priority, reverse=True)

if not sorted_tasks:
    st.info("No reminders yet. Add one below!")
else:
    for i, t in enumerate(sorted_tasks):
        if t['status'] == "Pending":
            with st.container():
                tc1, tc2 = st.columns([5, 1])
                tc1.markdown(f"""
                    <div class="task-item">
                        <div><b>{t['time']}</b> - {t['name']} <small>({t['cat']})</small></div>
                    </div>
                """, unsafe_allow_html=True)
                if tc2.button("Done", key=f"done_{i}"):
                    # Find original task in list and mark done
                    for task in st.session_state.tasks:
                        if task['name'] == t['name']: task['status'] = "Done"
                    st.rerun()

# --- 8. ADD NEW & HYDRATION ---
st.markdown("---")
with st.expander("➕ Set New Timed Reminder"):
    c_a, c_b, c_c = st.columns(3)
    new_name = c_a.text_input("What's the event?")
    new_time = c_b.text_input("Time (HH:MM)", value=curr_str)
    new_cat = c_c.selectbox("Category", ["Work", "Study", "Health", "Personal"])
    if st.button("Schedule Now"):
        st.session_state.tasks.append({"name": new_name, "cat": new_cat, "status": "Pending", "time": new_time})
        st.rerun()

# --- 9. AUTOMATIC NOTIFICATION CHECKER ---
# Check if 30 mins passed for water
time_passed = (now - st.session_state.last_water_time).seconds / 60
if time_passed >= 30:
    st.toast("💧 Time to hydrate! Logging 250ml...", icon="🥛")
    st.session_state.water_ml += 250
    st.session_state.last_water_time = now

# Check for timed tasks
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_str:
        st.toast(f"⏰ REMINDER: {t['name']} is starting!", icon="🔔")

# --- 10. AUTO-REFRESH SCRIPT ---
time.sleep(1)
if now.second == 0:
    st.rerun()
