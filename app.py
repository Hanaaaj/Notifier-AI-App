import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import time
import math
from datetime import datetime
import pytz

# ==========================================================
# 1. PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="MindFlow | Adaptive Intelligence", 
    page_icon="✨", 
    layout="wide"
)

def get_uae_now():
    return datetime.now(pytz.timezone('Asia/Dubai'))

# ==========================================================
# 2. AI CONFIGURATION (Safe Handling)
# ==========================================================
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Switched to 'gemini-1.5-flash' for better availability
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"AI Configuration Error: {e}")
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")

# ==========================================================
# 3. STATE INITIALIZATION
# ==========================================================
if "tasks" not in st.session_state: st.session_state.tasks = []
if "water" not in st.session_state: st.session_state.water = 0
if "study_plan" not in st.session_state: st.session_state.study_plan = {}
if "last_check" not in st.session_state: st.session_state.last_check = get_uae_now()

# ==========================================================
# 4. NAVIGATION
# ==========================================================
now = get_uae_now()
st.sidebar.title("✨ MindFlow")
section = st.sidebar.radio("Navigate", ["Home", "Study", "Work", "Health", "Dashboard"])

# ==========================================================
# 5. HOME SECTION
# ==========================================================
if section == "Home":
    st.title("Command Center 🏠")
    st.caption(f"UAE Time: {now.strftime('%I:%M %p')}")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Hydration", f"{st.session_state.water} ml", "Goal: 2000ml")
    with m2:
        pending = len([t for t in st.session_state.tasks if t.get('status') != 'Done'])
        st.metric("Tasks", f"{pending} Pending")
    with m3:
        mod = st.session_state.study_plan.get('module', 'None')
        st.metric("Study Plan", mod)

    st.divider()
    
    st.subheader("🤖 Daily AI Strategy")
    if st.button("Generate Strategy"):
        try:
            with st.spinner("AI is analyzing your current flow..."):
                ctx = f"Study: {mod}, Water: {st.session_state.water}ml, Pending Tasks: {pending}"
                # The prompt that was causing the NotFound error
                resp = model.generate_content(f"Give a short 3-sentence high-performance strategy for today: {ctx}")
                st.info(resp.text)
        except Exception as e:
            st.warning("The AI is currently unavailable or the model name was not found. Please check your API quota or model name.")
            st.error(f"Error Details: {e}")

# ==========================================================
# 6. STUDY SECTION
# ==========================================================
elif section == "Study":
    st.header("📚 AI Study Planner")
    with st.form("study_form"):
        name = st.text_input("Module Name")
        exam = st.date_input("Exam Date", min_value=now.date())
        topics = st.text_area("Topics (comma separated)")
        if st.form_submit_button("Generate Plan"):
            topic_list = [t.strip() for t in topics.split(",") if t.strip()]
            days = (exam - now.date()).days
            if days > 0:
                st.session_state.study_plan = {
                    "module": name,
                    "topics_per_day": math.ceil(len(topic_list)/days),
                    "days_left": days
                }
                st.success("Plan Created!")
            else:
                st.error("Exam date must be in the future.")

# ==========================================================
# 7. WORK SECTION
# ==========================================================
elif section == "Work":
    st.header("💼 Work Focus Planner")
    with st.form("task_form"):
        t_name = st.text_input("Task Title")
        t_time = st.text_input("Time (HH:MM)", value=now.strftime("%H:%M"))
        if st.form_submit_button("Add Task"):
            st.session_state.tasks.append({"name": t_name, "time": t_time, "status": "Pending"})
            st.rerun()

    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            c1, c2 = st.columns([4, 1])
            c1.info(f"**{t['time']}** — {t['name']}")
            if c2.button("Done", key=f"t_{i}"):
                t['status'] = "Done"
                st.rerun()

# ==========================================================
# 8. HEALTH SECTION
# ==========================================================
elif section == "Health":
    st.header("🏥 Health Optimizer")
    st.markdown("### The 20-20-20 Rule")
    st.write("To reduce eye strain: Every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    
    
    st.progress(min(st.session_state.water / 2000, 1.0))
    st.write(f"Current Intake: {st.session_state.water} / 2000 ml")

# ==========================================================
# 9. DASHBOARD
# ==========================================================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names='status', title='Goal Completion Rate', hole=0.4,
                     color_discrete_map={'Done':'#10b981', 'Pending':'#f59e0b'})
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data yet.")

# ==========================================================
# 10. NOTIFICATION ENGINE
# ==========================================================
st.sidebar.divider()
if st.sidebar.button("🥤 Log 250ml Water"):
    st.session_state.water += 250
    st.rerun()

# Check every 30 minutes
seconds_since_check = (now - st.session_state.last_check).total_seconds()
if seconds_since_check >= 1800:
    st.toast("💧 Time to hydrate!", icon="🥤")
    st.session_state.last_check = now

time.sleep(2)
st.rerun()
