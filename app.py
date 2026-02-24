import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
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
    """Consistently returns a timezone-aware UAE datetime."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# ==========================================================
# 2. AI CONFIGURATION (Modern SDK)
# ==========================================================
def get_ai_response(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "API Key not found in Streamlit Secrets."
    
    try:
        # Using the new Google GenAI SDK
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        # 'gemini-1.5-flash' is the most compatible and fastest model
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI is resting (Error: {str(e)[:50]}...)"

# ==========================================================
# 3. STATE INITIALIZATION
# ==========================================================
if "tasks" not in st.session_state: st.session_state.tasks = []
if "water" not in st.session_state: st.session_state.water = 0
if "last_check" not in st.session_state: st.session_state.last_check = get_uae_now()

# ==========================================================
# 4. NAVIGATION
# ==========================================================
now = get_uae_now()
st.sidebar.title("✨ MindFlow")
section = st.sidebar.radio("Navigate", ["Home", "Work", "Health", "Dashboard"])

# ==========================================================
# 5. HOME SECTION
# ==========================================================
if section == "Home":
    st.title("Command Center 🏠")
    st.caption(f"UAE Time: {now.strftime('%I:%M %p')} | Status: Optimized")

    m1, m2 = st.columns(2)
    m1.metric("Hydration", f"{st.session_state.water} ml", "Goal: 2000ml")
    pending = len([t for t in st.session_state.tasks if t.get('status') != 'Done'])
    m2.metric("Workload", f"{pending} Tasks")

    st.divider()
    
    st.subheader("🤖 AI Strategy Brief")
    if st.button("Generate Strategy"):
        with st.spinner("AI is analyzing your flow..."):
            ctx = f"Pending tasks: {pending}, Water consumed: {st.session_state.water}ml."
            strategy = get_ai_response(f"Give a short 2-sentence productivity tip based on: {ctx}")
            st.info(strategy)

# ==========================================================
# 6. WORK & HEALTH
# ==========================================================
elif section == "Work":
    st.header("💼 Task Focus")
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("What needs to be done?")
        if st.form_submit_button("Add Task"):
            st.session_state.tasks.append({"name": t_name, "status": "Pending"})
            st.rerun()

    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            c1, c2 = st.columns([5, 1])
            c1.write(f"• {t['name']}")
            if c2.button("Done", key=f"t_{i}"):
                t['status'] = "Done"
                st.rerun()

elif section == "Health":
    st.header("🏥 Wellness Hub")
    st.subheader("The 20-20-20 Rule")
    st.write("To prevent eye strain: Every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    
    
    st.divider()
    st.progress(min(st.session_state.water / 2000, 1.0))
    st.write(f"Current Intake: {st.session_state.water} / 2000 ml")

# ==========================================================
# 7. DASHBOARD
# ==========================================================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names='status', title='Task Progress', hole=0.4)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Log some tasks to see your progress chart!")

# ==========================================================
# 8. NOTIFICATION ENGINE
# ==========================================================
st.sidebar.divider()
if st.sidebar.button("🥤 Log 250ml Water"):
    st.session_state.water += 250
    st.rerun()

# Hydration check logic (30-minute interval)
if (now - st.session_state.last_check).total_seconds() > 1800:
    st.toast("💧 Time to hydrate! Grab a glass of water.", icon="🥤")
    st.session_state.last_check = now

# Keep the clock/alerts live
time.sleep(2)
st.rerun()
