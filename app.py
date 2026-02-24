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
# 1. CONFIG & SYNC
# =========================
st.set_page_config(page_title="MindFlow | Adaptive Intelligence", page_icon="✨", layout="wide")

def get_uae_now():
    """Universal UAE time sync to prevent offset-naive/aware TypeErrors."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# Gemini Configuration (Ensure GEMINI_API_KEY is in your Streamlit secrets)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-turbo")
else:
    st.warning("Gemini API Key missing. AI features will be disabled.")

# =========================
# 2. STATE INITIALIZATION
# =========================
if "tasks" not in st.session_state: st.session_state.tasks = []
if "water" not in st.session_state: st.session_state.water = 0
if "study_plan" not in st.session_state: st.session_state.study_plan = {}
# Critical Fix: Initialize last_water_check with a timezone-aware object
if "last_water_check" not in st.session_state: st.session_state.last_water_check = get_uae_now()
if "notified_cache" not in st.session_state: st.session_state.notified_cache = set()

# =========================
# 3. HELPER ENGINES
# =========================
def generate_study_plan(module, exam_date, topics, daily_hours):
    today = get_uae_now().date()
    days_remaining = (exam_date - today).days
    if days_remaining <= 0:
        raise ValueError("Exam date must be in the future.")

    topics_per_day = math.ceil(len(topics) / days_remaining)
    schedule = {}
    topic_index = 0
    for d in range(days_remaining):
        daily_topics = topics[topic_index: topic_index + topics_per_day]
        if not daily_topics: break
        schedule[f"Day {d+1}"] = {
            "topics": daily_topics,
            "break_rule": "20 min break after 60 min",
            "hydration": "Every 10 min"
        }
        topic_index += topics_per_day
    return {"module": module, "days_remaining": days_remaining, "schedule": schedule}

def calculate_wellness(water, exercise, sleep):
    score = (water/2000)*40 + (exercise/60)*30 + (sleep/8)*30
    return round(min(score, 100), 2)

# =========================
# 4. NAVIGATION
# =========================
now = get_uae_now()
st.sidebar.title("✨ MindFlow AI")
section = st.sidebar.radio("Navigate", ["Home", "Study", "Work", "Health", "Dashboard"])

# =========================
# 5. HOME SECTION
# =========================
if section == "Home":
    st.title("Welcome to MindFlow ✨")
    st.markdown(f"**Current UAE Time:** `{now.strftime('%H:%M:%S')}`")
    
    # Overview Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div style="background:#f8f9fa;padding:20px;border-radius:15px;border-left:5px solid #6366f1">
            <h4 style="margin:0">📚 Study</h4>
            <p style="font-size:22px;font-weight:bold;margin:0">{st.session_state.study_plan.get('module', 'No active module')}</p>
            </div>""", unsafe_allow_html=True)
    with c2:
        pending = len([t for t in st.session_state.tasks if t.get('status') != 'Done'])
        st.markdown(f"""<div style="background:#f8f9fa;padding:20px;border-radius:15px;border-left:5px solid #10b981">
            <h4 style="margin:0">💼 Work</h4>
            <p style="font-size:22px;font-weight:bold;margin:0">{pending} Tasks Pending</p>
            </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="background:#f8f9fa;padding:20px;border-radius:15px;border-left:5px solid #f59e0b">
            <h4 style="margin:0">💧 Hydration</h4>
            <p style="font-size:22px;font-weight:bold;margin:0">{st.session_state.water} / 2000 ml</p>
            </div>""", unsafe_allow_html=True)

    st.divider()
    
    st.subheader("🤖 Today's AI Briefing")
    if st.button("Generate Strategy"):
        with st.spinner("AI analyzing your metrics..."):
            context = f"Study: {st.session_state.study_plan.get('module')}. Water: {st.session_state.water}ml. Tasks: {pending}."
            resp = model.generate_content(f"Give a short 3-sentence high-performance strategy for today: {context}")
            st.info(resp.text)

# =========================
# 6. STUDY SECTION
# =========================
elif section == "Study":
    st.header("📚 AI Study Planner")
    with st.form("study_input"):
        mod = st.text_input("Module Name")
        ex_date = st.date_input("Exam Date", min_value=now.date())
        top = st.text_area("Topics (comma separated)")
        hrs = st.slider("Daily Study Hours", 1, 12, 4)
        if st.form_submit_button("Generate Plan"):
            plan = generate_study_plan(mod, ex_date, [t.strip() for t in top.split(',')], hrs)
            st.session_state.study_plan = plan
            st.success("Plan Created!")

    if st.session_state.study_plan:
        st.json(st.session_state.study_plan)

# =========================
# 7. WORK SECTION
# =========================
elif section == "Work":
    st.header("💼 Work Focus Planner")
    with st.form("task_add"):
        name = st.text_input("Task Name")
        t_time = st.text_input("Time (HH:MM)", value=now.strftime("%H:%M"))
        if st.form_submit_button("Add Task"):
            st.session_state.tasks.append({"name": name, "time": t_time, "status": "Pending"})
            st.rerun()

    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            col1, col2 = st.columns([4, 1])
            col1.info(f"**{t['time']}** — {t['name']}")
            if col2.button("Done", key=f"btn_{i}"):
                t['status'] = "Done"
                st.rerun()

# =========================
# 8. HEALTH SECTION
# =========================
elif section == "Health":
    st.header("🏥 Health Optimizer")
    ex = st.number_input("Exercise (mins)", 0, 180, 0)
    sl = st.number_input("Sleep (hrs)", 0, 15, 8)
    if st.button("Check Wellness"):
        score = calculate_wellness(st.session_state.water, ex, sl)
        st.metric("Wellness Score", f"{score}/100")
    
    

# =========================
# 9. DASHBOARD
# =========================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names="status", hole=0.4, title="Task Status",
                     color_discrete_map={"Done":"#10B981", "Pending":"#FACC15"})
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No task data available.")

# =========================
# 10. REAL-TIME HYDRATION & ALERTS
# =========================
st.sidebar.divider()
add_w = st.sidebar.selectbox("Log Water (ml)", [250, 500, 750])
if st.sidebar.button("Log Intake"):
    st.session_state.water += add_w
    st.rerun()

# 10-Minute Hydration Logic
time_diff = (now - st.session_state.last_water_check).total_seconds() / 60
if time_diff >= 10:
    st.toast("💧 Time to hydrate! Stay sharp.", icon="🥤")
    st.session_state.last_water_check = now

# Auto-refresh to keep notifications active
time.sleep(1)
st.rerun()
