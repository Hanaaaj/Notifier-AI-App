import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json
import time
import math
from datetime import datetime, timedelta
import pytz

# =========================
# CONFIG & SYNC
# =========================
st.set_page_config(page_title="MindFlow | Adaptive Intelligence", page_icon="✨", layout="wide")

def get_uae_now():
    """Universal UAE time sync to prevent offset-naive/aware TypeErrors."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# Gemini Configuration
# Ensure "GEMINI_API_KEY" is set in your Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-turbo")
else:
    st.error("Please set GEMINI_API_KEY in secrets.")

DATA_FILE = "mindflow_data.json"

# =========================
# STATE INITIALIZATION
# =========================
if "tasks" not in st.session_state: st.session_state.tasks = []
if "water" not in st.session_state: st.session_state.water = 0
if "study_plan" not in st.session_state: st.session_state.study_plan = {}
if "last_water_check" not in st.session_state: st.session_state.last_water_check = get_uae_now()
if "notified_cache" not in st.session_state: st.session_state.notified_cache = set()

# =========================
# ENGINES
# =========================

def generate_study_plan(module, exam_date, topics, daily_hours):
    today = get_uae_now().date()
    days_remaining = (exam_date - today).days
    if days_remaining <= 0:
        raise ValueError("Exam must be in the future.")

    topics_per_day = math.ceil(len(topics) / days_remaining)
    if topics_per_day > 4: topics_per_day = 4  # Overload protection

    schedule = {}
    topic_index = 0
    for d in range(days_remaining):
        daily_topics = topics[topic_index: topic_index + topics_per_day]
        if not daily_topics: break
        schedule[f"Day {d+1}"] = {
            "topics": daily_topics,
            "study_hours": daily_hours,
            "break_rule": "20 min break after 60 min",
            "hydration": "Every 10 min",
            "exercise": "After 3 hours"
        }
        topic_index += topics_per_day
    return {"module": module, "days_remaining": days_remaining, "schedule": schedule}

def calculate_wellness(water, exercise, sleep):
    # Score out of 100
    score = (water/2000)*40 + (exercise/60)*30 + (sleep/8)*30
    return round(min(score, 100), 2)

# =========================
# UI HEADER & NAVIGATION
# =========================
now = get_uae_now()
st.sidebar.title("✨ MindFlow AI")
section = st.sidebar.radio("Navigate", ["Home", "Study", "Work", "Health", "Dashboard"])

# =========================
# HOME SECTION
# =========================
if section == "Home":
    st.title("Command Center 🏠")
    st.caption(f"UAE Time: {now.strftime('%H:%M:%S')} | Optimize your flow.")
    
    # Quick Stats Row
    c1, c2, c3 = st.columns(3)
    with c1:
        topics_left = len(st.session_state.study_plan.get("schedule", {}))
        st.markdown(f"""<div style="background:#f0f2f6;padding:20px;border-radius:15px;border-left:5px solid #6366f1">
            <h4 style="margin:0">📚 Study</h4><p style="font-size:24px;font-weight:bold;margin:0">{topics_left if topics_left > 0 else 'No Plan'}</p>
            <small>Days Scheduled</small></div>""", unsafe_allow_html=True)
    with c2:
        pending_work = len([t for t in st.session_state.tasks if t.get('status') != 'Done'])
        st.markdown(f"""<div style="background:#f0f2f6;padding:20px;border-radius:15px;border-left:5px solid #10b981">
            <h4 style="margin:0">💼 Work</h4><p style="font-size:24px;font-weight:bold;margin:0">{pending_work}</p>
            <small>Pending Tasks</small></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="background:#f0f2f6;padding:20px;border-radius:15px;border-left:5px solid #f59e0b">
            <h4 style="margin:0">💧 Water</h4><p style="font-size:24px;font-weight:bold;margin:0">{st.session_state.water} ml</p>
            <small>Logged Today</small></div>""", unsafe_allow_html=True)

    st.divider()
    
    # AI Briefing
    st.subheader("✨ Daily AI Strategy")
    if st.button("Generate Today's Strategy"):
        with st.spinner("Analyzing your metrics..."):
            context = f"Study Plan: {st.session_state.study_plan.get('module')}. Water: {st.session_state.water}ml. Tasks: {pending_work}."
            response = model.generate_content(f"Give a short, 3-sentence high-performance strategy for today based on: {context}")
            st.info(response.text)

# =========================
# STUDY SECTION
# =========================
elif section == "Study":
    st.header("📚 AI Study Planner")
    with st.form("study_form"):
        module = st.text_input("Module Name")
        exam_date = st.date_input("Exam Date", min_value=now.date())
        topics = st.text_area("Topics (comma separated)")
        daily_hours = st.slider("Daily Study Hours", 1, 12, 4)
        if st.form_submit_button("Generate Timetable"):
            topic_list = [t.strip() for t in topics.split(",") if t.strip()]
            plan = generate_study_plan(module, exam_date, topic_list, daily_hours)
            st.session_state.study_plan = plan
            st.success("Timetable Generated!")

    if st.session_state.study_plan:
        st.json(st.session_state.study_plan)

# =========================
# WORK SECTION
# =========================
elif section == "Work":
    st.header("💼 Work Focus Planner")
    with st.form("work_form"):
        t_name = st.text_input("Task Name")
        t_time = st.text_input("Scheduled Time (HH:MM)", value=now.strftime("%H:%M"))
        if st.form_submit_button("Add Focus Block"):
            st.session_state.tasks.append({"name": t_name, "time": t_time, "status": "Pending", "track": "Work"})
            st.rerun()
    
    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            cols = st.columns([4, 1])
            cols[0].info(f"**{t['time']}** — {t['name']}")
            if cols[1].button("Complete", key=f"work_{i}"):
                t['status'] = "Done"
                st.rerun()

# =========================
# HEALTH SECTION
# =========================
elif section == "Health":
    st.header("🏥 Health Optimizer")
    ex = st.number_input("Exercise Minutes Today", 0, 180, 0)
    sl = st.number_input("Sleep Hours Last Night", 0, 15, 8)
    if st.button("Calculate Wellness Score"):
        score = calculate_wellness(st.session_state.water, ex, sl)
        st.metric("Overall Score", f"{score}/100")
        
    

# =========================
# DASHBOARD
# =========================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names="status", title="Task Completion", color_discrete_map={"Done":"#10B981", "Pending":"#FACC15"})
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No tasks logged yet.")

# =========================
# SIDEBAR LOGGING & HYDRATION
# =========================
st.sidebar.divider()
st.sidebar.subheader("💧 Quick Log")
add_water = st.sidebar.selectbox("Add Water (ml)", [250, 500, 750])
if st.sidebar.button("Log Intake"):
    st.session_state.water += add_water
    st.rerun()

# =========================
# REAL-TIME NOTIFICATION ENGINE
# =========================
# Correct Time Math: Aware - Aware
time_since_water = (now - st.session_state.last_water_check).total_seconds() / 60

if time_since_water >= 10:
    st.toast("💧 Hydration Alert: Drink water to maintain focus!", icon="🥤")
    # Note: We update the check time so the toast doesn't spam every second
    st.session_state.last_water_check = now

# Task Alerts
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == now.strftime("%H:%M"):
        nid = f"{t['name']}_{t['time']}"
        if nid not in st.session_state.notified_cache:
            st.toast(f"🔔 Task Starting: {t['name']}", icon="⏰")
            st.session_state.notified_cache.add(nid)

# Update screen
time.sleep(1)
st.rerun()
