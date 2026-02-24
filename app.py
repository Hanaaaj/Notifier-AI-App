import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from datetime import datetime
import pytz
import time

# --- 1. SETTINGS & TIMEZONE ---
st.set_page_config(page_title="MindFlow AI", page_icon="✨", layout="wide")
uae_tz = pytz.timezone('Asia/Dubai')

def get_now():
    return datetime.now(uae_tz)

# --- 2. AI INITIALIZATION ---
def get_ai_response(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "API Key not found."
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI logic paused: {str(e)[:50]}"

# --- 3. SESSION STATE ---
if "tasks" not in st.session_state: st.session_state.tasks = []
if "water_ml" not in st.session_state: st.session_state.water_ml = 0
if "last_water_check" not in st.session_state: 
    # FIX: Ensure initial state is timezone-aware to match 'now'
    st.session_state.last_water_check = get_now()

# --- 4. UI NAVIGATION ---
now = get_now()
st.sidebar.title("✨ MindFlow")
page = st.sidebar.radio("Go to", ["Dashboard", "Tasks", "Wellness"])

# --- 5. DASHBOARD PAGE ---
if page == "Dashboard":
    st.title("Performance Dashboard 📈")
    st.caption(f"Current Time (UAE): {now.strftime('%I:%M %p')}")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Hydration", f"{st.session_state.water_ml} ml", "Goal: 2000ml")
    with c2:
        pending = len([t for t in st.session_state.tasks if t['status'] == "Pending"])
        st.metric("Pending Tasks", pending)

    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        # Replacing use_container_width with width='stretch' per deprecation notice
        fig = px.pie(df, names='status', title="Task Completion", hole=0.4)
        st.plotly_chart(fig, width='stretch')
    
    if st.button("Get AI Performance Strategy"):
        with st.spinner("AI analyzing..."):
            tip = get_ai_response(f"I have {pending} tasks and {st.session_state.water_ml}ml water. Give a 1-sentence tip.")
            st.success(tip)

# --- 6. TASKS PAGE ---
elif page == "Tasks":
    st.header("💼 Task Manager")
    with st.form("add_task", clear_on_submit=True):
        name = st.text_input("Task Description")
        if st.form_submit_button("Add Task"):
            st.session_state.tasks.append({"name": name, "status": "Pending"})
            st.rerun()

    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"• {t['name']}")
            if col_b.button("Done", key=f"btn_{i}"):
                t['status'] = "Done"
                st.rerun()

# --- 7. WELLNESS PAGE ---
elif page == "Wellness":
    st.header("🏥 Wellness Hub")
    st.markdown("### The 20-20-20 Rule")
    st.write("To prevent eye strain, every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    
    
    st.divider()
    st.progress(min(st.session_state.water_ml / 2000, 1.0))
    if st.button("🥤 Drink 250ml"):
        st.session_state.water_ml += 250
        st.rerun()

# --- 8. GLOBAL NOTIFICATION LOGIC ---
# FIX: 'now' and 'last_water_check' are both offset-aware (pytz)
time_diff = (now - st.session_state.last_water_check).total_seconds() / 60
if time_diff >= 30:
    st.toast("💧 Time to hydrate! Stay sharp.", icon="🥤")
    st.session_state.last_water_check = now

# Keep the app active
time.sleep(5)
st.rerun()
