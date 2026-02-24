import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai  # Keep for now, but fixed model names
import time
import math
from datetime import datetime
import pytz

# ==========================================================
# 1. PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="MindFlow | Adaptive AI", 
    page_icon="✨", 
    layout="wide"
)

def get_uae_now():
    return datetime.now(pytz.timezone('Asia/Dubai'))

# ==========================================================
# 2. AI CONFIGURATION (Resilient Logic)
# ==========================================================
def get_ai_response(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "Please add your API key to continue."
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # These are the most reliable model strings for the current API
    model_options = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    for model_name in model_options:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # If we hit the 404/NotFound, we just try the next model in the list
            continue
            
    return "AI models are currently unreachable. Please check your API key permissions."

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
    st.caption(f"UAE Local Time: {now.strftime('%I:%M %p')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Hydration", f"{st.session_state.water} ml", "Goal: 2k")
    
    pending = len([t for t in st.session_state.tasks if t.get('status') != 'Done'])
    col2.metric("Workload", f"{pending} Tasks")
    
    mod = st.session_state.study_plan.get('module', 'None Active')
    col3.metric("Study Focus", mod)

    st.divider()
    
    st.subheader("🤖 AI Performance Briefing")
    if st.button("Generate Strategy"):
        with st.spinner("Analyzing data..."):
            prompt = f"Tasks pending: {pending}, Water: {st.session_state.water}ml. Give me a 3-sentence productivity hack."
            strategy = get_ai_response(prompt)
            st.info(strategy)

# ==========================================================
# 6. STUDY & WORK (Simplified for stability)
# ==========================================================
elif section == "Study":
    st.header("📚 Study Planner")
    with st.form("study_form"):
        name = st.text_input("Module")
        exam = st.date_input("Exam Date", min_value=now.date())
        if st.form_submit_button("Set Plan"):
            st.session_state.study_plan = {"module": name, "date": str(exam)}
            st.success("Plan saved!")

elif section == "Work":
    st.header("💼 Task Manager")
    with st.form("task_form"):
        t_name = st.text_input("New Task")
        if st.form_submit_button("Add"):
            st.session_state.tasks.append({"name": t_name, "status": "Pending"})
            st.rerun()
            
    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            c1, c2 = st.columns([5, 1])
            c1.write(f"🔹 {t['name']}")
            if c2.button("Done", key=f"btn_{i}"):
                t['status'] = "Done"
                st.rerun()

# ==========================================================
# 7. HEALTH & 20-20-20 RULE
# ==========================================================
elif section == "Health":
    st.header("🏥 Wellness Hub")
    st.subheader("Prevent Digital Strain")
    st.write("Follow the 20-20-20 rule to protect your vision while working:")
    
    
    
    st.info("Every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    st.divider()
    st.progress(min(st.session_state.water / 2000, 1.0))
    st.write(f"Water Intake: {st.session_state.water}/2000 ml")

# ==========================================================
# 8. DASHBOARD (Fixed Chart)
# ==========================================================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names='status', hole=0.4, title="Task Completion")
        st.plotly_chart(fig, width="stretch")
    else:
        st.write("No task data to display yet.")

# ==========================================================
# 9. NOTIFICATION & REFRESH
# ==========================================================
st.sidebar.divider()
if st.sidebar.button("🥤 Log 250ml Water"):
    st.session_state.water += 250
    st.rerun()

# Hydration check logic
if (now - st.session_state.last_check).total_seconds() > 1800:
    st.toast("Time to drink some water! 💧")
    st.session_state.last_check = now

# Keep app alive for real-time updates
time.sleep(2)
st.rerun()
