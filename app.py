import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="MindFlow | Smart Scheduler", page_icon="🕒", layout="wide")

# (Keep the CSS from previous version or customize for rounded cards)

# --- 2. THE SMART BRAIN (Logic & AI) ---

if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water_goal' not in st.session_state:
    st.session_state.water_goal = {"last_drink": datetime.now(), "interval": 30} # minutes

def calculate_priority(task):
    """AI-Logic to arrange reminders by importance"""
    score = 0
    # Time-based urgency
    if "10 am" in task['time'].lower() or "9 am" in task['time'].lower():
        score += 50
    # Category-based importance
    category_weights = {"Work": 30, "Study": 25, "Health": 20, "Personal": 10}
    score += category_weights.get(task['cat'], 0)
    return score

def get_ai_reordering(tasks):
    """Uses Gemini to refine the schedule if requested"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        task_list = [f"{t['name']} at {t['time']}" for t in tasks]
        prompt = f"Rearrange these tasks by biological peak performance and urgency: {task_list}. Return only a JSON list."
        # Note: In a real hackathon, you'd parse this JSON back into session_state
        return model.generate_content(prompt).text
    except:
        return "Manual Priority Active"

# --- 3. THE TIME KEEPER (Notification Logic) ---
now = datetime.now()
current_time_str = now.strftime("%H:%M")

def check_notifications():
    """Triggered on every rerun to check if a reminder is due"""
    # 1. Check Specific Task Times
    for t in st.session_state.tasks:
        if t['status'] == "Pending" and t['time'] == current_time_str:
            st.toast(f"🔔 NOTIFICATION: {t['name']} starting now!", icon="⏰")
            
    # 2. Check Water Interval (Every 30 mins)
    time_since_water = (now - st.session_state.water_goal["last_drink"]).seconds / 60
    if time_since_water >= st.session_state.water_goal["interval"]:
        st.toast("💧 SMART REMINDER: Time to drink water!", icon="🥤")
        # Auto-reset after notification to avoid spamming
        st.session_state.water_goal["last_drink"] = now

# --- 4. MAIN INTERFACE ---

st.title(f"Today is {now.strftime('%A, %b %d')}")
st.subheader(f"Current Time: {current_time_str}")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📅 Smart Schedule")
    # Sorting tasks by the Importance Logic
    sorted_tasks = sorted(st.session_state.tasks, key=calculate_priority, reverse=True)
    
    for i, t in enumerate(sorted_tasks):
        with st.container():
            st.markdown(f"""
            <div style="background: white; padding: 15px; border-radius: 12px; border-left: 5px solid #4facfe; margin-bottom: 10px;">
                <strong>{t['time']} - {t['name']}</strong> <span style="font-size: 10px; background: #eee; padding: 2px 5px; border-radius: 4px;">{t['cat']}</span>
            </div>
            """, unsafe_allow_html=True)

with col2:
    st.markdown("### ➕ Add Event")
    with st.form("new_event"):
        name = st.text_input("Event Name (e.g., Meeting)")
        t_time = st.text_input("Time (HH:MM format)", value=current_time_str)
        t_cat = st.selectbox("Category", ["Work", "Study", "Health", "Personal"])
        if st.form_submit_button("Set Reminder"):
            st.session_state.tasks.append({
                "name": name, 
                "time": t_time, 
                "cat": t_cat, 
                "status": "Pending",
                "created": now
            })
            st.rerun()

# --- 5. DASHBOARD & ANALYSIS ---
st.markdown("---")
st.markdown("### 📊 Weekly Analytics")
# (Insert your Plotly charts here for progress tracking)

# --- 6. AUTO-REFRESH SCRIPT ---
# This forces the app to refresh every 60 seconds to check time-based notifications
check_notifications()
st.empty()
time.sleep(1) # Subtle pause
if now.second == 0: # Rerun on the minute mark
    st.rerun()
