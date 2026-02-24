import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import time
import math
from datetime import datetime
import pytz

# =========================
# 1. CONFIG & SYNC
# =========================
st.set_page_config(page_title="MindFlow | AI Optimizer", page_icon="✨", layout="wide")

def get_uae_now():
    """Returns a timezone-aware datetime object for UAE."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# Gemini Configuration
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-turbo")
else:
    st.error("API Key missing! Please add GEMINI_API_KEY to your Streamlit secrets.")

# =========================
# 2. STATE INITIALIZATION
# =========================
# Use aware datetimes from the start to avoid TypeError
if "tasks" not in st.session_state: st.session_state.tasks = []
if "water" not in st.session_state: st.session_state.water = 0
if "study_plan" not in st.session_state: st.session_state.study_plan = {}
if "last_water_check" not in st.session_state: st.session_state.last_water_check = get_uae_now()

# =========================
# 3. CORE LOGIC ENGINES
# =========================

def generate_study_plan(module, exam_date, topics, daily_hours):
    today = get_uae_now().date()
    days_left = (exam_date - today).days
    if days_left <= 0:
        raise ValueError("Exam date must be in the future!")
    
    topics_per_day = math.ceil(len(topics) / days_left)
    schedule = {f"Day {i+1}": topics[i*topics_per_day : (i+1)*topics_per_day] 
                for i in range(days_left) if i*topics_per_day < len(topics)}
    
    return {"module": module, "schedule": schedule, "daily_hours": daily_hours}

# =========================
# 4. NAVIGATION
# =========================
now = get_uae_now()
st.sidebar.title("✨ MindFlow")
section = st.sidebar.radio("Navigate", ["Home", "Study", "Work", "Health", "Dashboard"])

# =========================
# 5. HOME SECTION
# =========================
if section == "Home":
    st.title("Command Center 🏠")
    st.caption(f"UAE Time: {now.strftime('%I:%M %p')} | System Status: Active")

    # High-Level Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hydration Status", f"{st.session_state.water} ml", "Target: 2000ml")
    with col2:
        pending = len([t for t in st.session_state.tasks if t.get('status') != 'Done'])
        st.metric("Workload", f"{pending} Tasks", "Pending")
    with col3:
        study_mod = st.session_state.study_plan.get('module', 'None Active')
        st.metric("Study Module", study_mod)

    st.divider()
    
    # AI Morning Briefing
    st.subheader("✨ Daily AI Briefing")
    if st.button("Generate Strategy"):
        with st.spinner("Analyzing your flow..."):
            context = f"Tasks: {pending}, Water: {st.session_state.water}ml, Study: {study_mod}"
            response = model.generate_content(f"Give me a 3-sentence high-performance strategy for today: {context}")
            st.info(response.text)

# =========================
# 6. STUDY SECTION
# =========================
elif section == "Study":
    st.header("📚 AI Study Planner")
    with st.form("study_input"):
        module = st.text_input("Module Name")
        exam_date = st.date_input("Exam Date", min_value=now.date())
        topics = st.text_area("Topics (comma separated)")
        if st.form_submit_button("Build Plan"):
            topic_list = [t.strip() for t in topics.split(",") if t.strip()]
            st.session_state.study_plan = generate_study_plan(module, exam_date, topic_list, 4)
            st.success("Plan generated! Check the JSON or Dashboard.")

    if st.session_state.study_plan:
        st.write(st.session_state.study_plan)

# =========================
# 7. WORK SECTION
# =========================
elif section == "Work":
    st.header("💼 Work Focus Planner")
    with st.form("add_task"):
        name = st.text_input("Task Description")
        t_time = st.text_input("Target Time (HH:MM)", value=now.strftime("%H:%M"))
        if st.form_submit_button("Add Focus Block"):
            st.session_state.tasks.append({"name": name, "time": t_time, "status": "Pending"})
            st.rerun()

    for i, task in enumerate(st.session_state.tasks):
        if task['status'] == "Pending":
            c1, c2 = st.columns([4, 1])
            c1.warning(f"**{task['time']}** — {task['name']}")
            if c2.button("Done", key=f"tk_{i}"):
                task['status'] = "Done"
                st.rerun()

# =========================
# 8. HEALTH SECTION
# =========================
elif section == "Health":
    st.header("🏥 Health Optimizer")
    st.info("Ensure you are maintaining the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    

    water_goal = st.progress(min(st.session_state.water / 2000, 1.0))
    st.write(f"Current Hydration: {st.session_state.water} / 2000 ml")

# =========================
# 9. DASHBOARD
# =========================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names='status', title='Task Completion Rate', 
                     color_discrete_map={'Done':'#10b981', 'Pending':'#f59e0b'})
        # FIX: width="stretch" replaces use_container_width
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No data yet. Start by adding tasks in the Work section!")

# =========================
# 10. REAL-TIME HYDRATION ENGINE
# =========================
st.sidebar.divider()
st.sidebar.subheader("💧 Quick Log")
if st.sidebar.button("Add 250ml Water"):
    st.session_state.water += 250
    st.rerun()

# Timezone-aware subtraction to prevent the TypeError in your logs
time_since_last_sip = (now - st.session_state.last_water_check).total_seconds() / 60

if time_since_last_sip >= 30:
    st.toast("💧 Time to hydrate! Your brain needs water for focus.", icon="🥤")
    st.session_state.last_water_check = now

# Auto-refresh loop
time.sleep(2)
st.rerun()
