import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime
import pytz
import time

# --- 1. SETUP UAE TIMEZONE ---
uae_tz = pytz.timezone('Asia/Dubai')

def get_uae_now():
    return datetime.now(uae_tz)

st.set_page_config(page_title="AuraFlow Live Planner", page_icon="⏰", layout="wide")

# --- 2. THE AESTHETIC (MindFlow CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .clock-container {
        background: #1A202C; color: #00F2FE; padding: 20px; 
        border-radius: 15px; text-align: center; border: 2px solid #00F2FE;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
    }
    .planner-card {
        background: white; padding: 18px; border-radius: 14px;
        margin-bottom: 12px; border: 1px solid #E2E8F0;
        display: flex; align-items: center; justify-content: space-between;
    }
    .status-now { border-left: 5px solid #00F2FE; background: #E6FFFA; }
    .status-done { border-left: 5px solid #38A169; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE (The Brain) ---
if 'schedule' not in st.session_state:
    st.session_state.schedule = []
if 'notified_tasks' not in st.session_state:
    st.session_state.notified_tasks = set() # Prevents duplicate popups in the same minute
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0

# --- 4. HEADER: REAL-TIME CLOCK ---
now = get_uae_now()
current_hm = now.strftime("%H:%M") # The "Real Clock" string

c1, c2 = st.columns([3, 1])
with c1:
    st.title("My UAE Day Planner 🇦🇪")
    st.markdown(f"**Date:** {now.strftime('%A, %B %d, %Y')}")

with c2:
    # This visualizes the Real Clock
    st.markdown(f"""
        <div class="clock-container">
            <h1 style="margin:0; font-family: monospace;">{now.strftime('%H:%M:%S')}</h1>
            <small>UAE STANDARD TIME</small>
        </div>
    """, unsafe_allow_html=True)

# --- 5. NOTIFICATION ENGINE (The "Pop-Up" Logic) ---
# 1. Task Reminders
for task in st.session_state.schedule:
    # If task is Pending AND time matches HH:MM AND we haven't popped up yet
    if task['status'] == "Pending" and task['time'] == current_hm:
        notif_id = f"{task['name']}_{current_hm}"
        if notif_id not in st.session_state.notified_tasks:
            st.toast(f"🔔 REMINDER: {task['name']} is starting now!", icon="⏰")
            # We add logic here to trigger a sound via JS if needed
            st.session_state.notified_tasks.add(notif_id)

# 2. Automated Water Logic (30-min interval)
if now.minute % 30 == 0 and now.second == 0:
    st.toast("💧 HYDRATION: Time for 250ml of water!", icon="🥤")
    st.session_state.water_ml += 250

# --- 6. ADDING TO THE PLANNER ---
st.divider()
with st.expander("➕ Schedule a New Reminder"):
    col_in1, col_in2, col_in3 = st.columns(3)
    name = col_in1.text_input("Task/Meeting Name")
    tm = col_in2.text_input("Time (Use 24h format, e.g., 15:30)", value=current_hm)
    cat = col_in3.selectbox("Type", ["Work", "Study", "Health", "Personal"])
    
    if st.button("Add to My Day"):
        st.session_state.schedule.append({
            "name": name, "time": tm, "cat": cat, "status": "Pending"
        })
        st.success(f"Task '{name}' set for {tm}")
        st.rerun()

# --- 7. THE TIMELINE VIEW ---
st.subheader("Today's Timeline")

# We sort by time so the user sees a chronological day
sorted_schedule = sorted(st.session_state.schedule, key=lambda x: x['time'])

if not sorted_schedule:
    st.info("No tasks scheduled yet.")
else:
    for i, t in enumerate(sorted_schedule):
        # Determine styling based on current time
        is_active = t['time'] == current_hm
        card_class = "status-now" if is_active else ("status-done" if t['status'] == "Done" else "")
        
        st.markdown(f"""
            <div class="planner-card {card_class}">
                <div>
                    <span style="font-weight:bold; color:#2D3748;">{t['time']}</span>
                    <span style="margin-left:15px; font-size:1.1rem;">{t['name']}</span>
                </div>
                <div>
                    <span style="background:#EDF2F7; padding:4px 10px; border-radius:8px; font-size:0.8rem;">{t['cat']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if t['status'] == "Pending":
            if st.button("Mark Completed", key=f"done_{i}"):
                t['status'] = "Done"
                st.rerun()

# --- 8. DASHBOARD & ANALYSIS ---
st.divider()
st.subheader("📈 Productivity Analysis")
d1, d2 = st.columns(2)

with d1:
    # Progress Pie Chart
    if sorted_schedule:
        df = pd.DataFrame(sorted_schedule)
        fig = px.pie(df, names='status', title="Daily Task Completion", 
                     color_discrete_map={'Done':'#38A169', 'Pending':'#E2E8F0'},
                     hole=0.5)
        fig.update_layout(showlegend=False, height=250)
        st.plotly_chart(fig, use_container_width=True)

with d2:
    st.metric("Total Water Intake", f"{st.session_state.water_ml} ml")
    st.info("**AI Insight:** You are most active in the afternoon. Ensure your hardest 'Work' tasks are set between 14:00 and 16:00.")

# --- 9. THE "HEARTBEAT" (Auto-Refresh) ---
# This is the most important part. It keeps the clock ticking every second.
time.sleep(1) 
st.rerun()
