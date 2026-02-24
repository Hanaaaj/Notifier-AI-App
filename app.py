import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime
import pytz
import time

# --- 1. UAE TIME & PLANNER SETTINGS ---
uae_tz = pytz.timezone('Asia/Dubai')
def get_uae_now():
    return datetime.now(uae_tz)

st.set_page_config(page_title="AuraFlow Planner", page_icon="🗓️", layout="wide")

# --- 2. CUSTOM DAY-PLANNER STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F9FAFB; }
    /* Planner Card Style */
    .planner-card {
        background: white; padding: 20px; border-radius: 15px;
        border: 1px solid #E5E7EB; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .time-slot { color: #6B7280; font-weight: 600; font-size: 0.9rem; min-width: 60px; }
    .task-title { color: #111827; font-weight: 500; margin-left: 15px; }
    .ai-suggestion { background: #EEF2FF; border-left: 4px solid #6366F1; padding: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'daily_tasks' not in st.session_state:
    st.session_state.daily_tasks = []
if 'water_logs' not in st.session_state:
    st.session_state.water_logs = 0
if 'last_check' not in st.session_state:
    st.session_state.last_check = get_uae_now()

# --- 4. HEADER & REAL-TIME CLOCK ---
now = get_uae_now()
col_a, col_b = st.columns([3, 1])

with col_a:
    st.title(f"Plan for {now.strftime('%A, %d %B')}")
    st.markdown(f"**Location:** Ras Al Khaimah, UAE 🇦🇪")

with col_b:
    st.markdown(f"""
        <div style="background:#111827; color:white; padding:15px; border-radius:12px; text-align:center;">
            <h2 style="margin:0;">{now.strftime('%H:%M')}</h2>
            <small>GST Time</small>
        </div>
    """, unsafe_allow_html=True)

# --- 5. SMART PLANNER LOGIC ---
st.divider()

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Your Timeline")
    
    # Sort tasks by time for the planner view
    if not st.session_state.daily_tasks:
        st.info("Your day is empty. Add a task to start planning!")
    else:
        sorted_tasks = sorted(st.session_state.daily_tasks, key=lambda x: x['time'])
        for i, task in enumerate(sorted_tasks):
            # Check if task is happening NOW
            is_now = now.strftime('%H:%M') == task['time']
            border_color = "#10B981" if task['status'] == "Done" else ("#6366F1" if is_now else "#E5E7EB")
            
            st.markdown(f"""
                <div class="planner-card" style="border-left: 6px solid {border_color};">
                    <div style="display: flex; align-items: center;">
                        <span class="time-slot">{task['time']}</span>
                        <span class="task-title">{task['name']}</span>
                        <span style="margin-left: auto; font-size: 0.8rem; color: #9CA3AF;">{task['cat']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if task['status'] == "Pending":
                if st.button(f"Mark Finished", key=f"finish_{i}"):
                    task['status'] = "Done"
                    st.rerun()

with c2:
    st.subheader("✨ Quick Add")
    with st.form("add_planner_task", clear_on_submit=True):
        new_name = st.text_input("What's happening?")
        new_time = st.text_input("At what time? (HH:MM)", value=now.strftime('%H:%M'))
        new_cat = st.selectbox("Category", ["Work", "Study", "Health", "Personal", "Prayer"])
        if st.form_submit_button("Add to Day"):
            st.session_state.daily_tasks.append({
                "name": new_name, "time": new_time, "cat": new_cat, "status": "Pending"
            })
            st.rerun()

    st.markdown("---")
    st.subheader("💡 AI Suggestions")
    # Rule: Suggest Eye Rest if it's afternoon in UAE
    if 13 <= now.hour <= 16:
        st.markdown('<div class="ai-suggestion"><b>✨ AI Suggestion:</b> Afternoon fatigue peak. Schedule a 10m walk or hydration break.</div>', unsafe_allow_html=True)
        if st.button("Add Break"):
            st.session_state.daily_tasks.append({"name": "AI Rest Break", "time": now.strftime('%H:%M'), "cat": "Health", "status": "Pending"})
            st.rerun()

# --- 6. DASHBOARD & ANALYSIS ---
st.divider()
st.subheader("📊 Performance & Progress")
d1, d2, d3 = st.columns(3)

# Progress calculation
total_tasks = len(st.session_state.daily_tasks)
done_tasks = len([t for t in st.session_state.daily_tasks if t['status'] == "Done"])
progress = (done_tasks / total_tasks) if total_tasks > 0 else 0

with d1:
    st.metric("Completion Rate", f"{int(progress*100)}%")
with d2:
    st.metric("Hydration Log", f"{st.session_state.water_logs}ml")
with d3:
    st.metric("Planner Status", "On Track" if progress > 0.5 or total_tasks == 0 else "Behind")

# Progress Chart
if total_tasks > 0:
    df = pd.DataFrame([{"Status": t['status'], "Count": 1} for t in st.session_state.daily_tasks])
    fig = px.pie(df, names='Status', hole=0.6, color_discrete_map={'Done':'#10B981', 'Pending':'#E5E7EB'})
    fig.update_layout(showlegend=False, height=200, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

# --- 7. NOTIFICATION & REFRESH ---
# Water reminder logic
if (now - st.session_state.last_check).total_seconds() / 60 >= 30:
    st.toast("💧 UAE Hydration Goal: Please drink 250ml of water.", icon="🥤")
    st.session_state.water_logs += 250
    st.session_state.last_check = now

# Auto-Notification for Tasks
for t in st.session_state.daily_tasks:
    if t['status'] == "Pending" and t['time'] == now.strftime('%H:%M'):
        st.toast(f"🔔 UAE PLANNER: {t['name']} is starting!", icon="⏰")

time.sleep(1)
if now.second == 0:
    st.rerun()
