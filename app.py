import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai  # Switching to the new SDK
import time
from datetime import datetime
import pytz

# ==========================================================
# 1. PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="MindFlow | 2026 AI Assistant", 
    page_icon="✨", 
    layout="wide"
)

def get_uae_now():
    return datetime.now(pytz.timezone('Asia/Dubai'))

# ==========================================================
# 2. AI CONFIGURATION (New SDK Logic)
# ==========================================================
def get_ai_response(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "Key missing in secrets."
    
    try:
        # Initializing the new Client
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        # Using 'gemini-1.5-flash' which is the most reliable for current API versions
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI is offline: {str(e)[:50]}"

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
section = st.sidebar.radio("Navigate", ["Home", "Tasks", "Health", "Dashboard"])

# ==========================================================
# 5. HOME SECTION
# ==========================================================
if section == "Home":
    st.title("Command Center 🏠")
    st.caption(f"UAE Local Time: {now.strftime('%I:%M %p')}")

    m1, m2 = st.columns(2)
    m1.metric("Hydration", f"{st.session_state.water} ml", "Goal: 2k")
    pending = len([t for t in st.session_state.tasks if t['status'] == "Pending"])
    m2.metric("Workload", f"{pending} Tasks")

    st.divider()
    
    st.subheader("🤖 AI Performance Strategy")
    if st.button("Generate Strategy"):
        with st.spinner("AI is thinking..."):
            ctx = f"Pending tasks: {pending}, Water: {st.session_state.water}ml."
            tip = get_ai_response(f"Based on: {ctx}, give a 2-sentence productivity tip.")
            st.info(tip)

# ==========================================================
# 6. TASKS SECTION
# ==========================================================
elif section == "Tasks":
    st.header("💼 Task Focus")
    with st.form("task_entry", clear_on_submit=True):
        t_name = st.text_input("New Task")
        if st.form_submit_button("Add Task"):
            st.session_state.tasks.append({"name": t_name, "status": "Pending"})
            st.rerun()

    for i, t in enumerate(st.session_state.tasks):
        if t['status'] == "Pending":
            c1, c2 = st.columns([5, 1])
            c1.write(f"🔹 {t['name']}")
            if c2.button("Done", key=f"t_{i}"):
                t['status'] = "Done"
                st.rerun()

# ==========================================================
# 7. HEALTH SECTION
# ==========================================================
elif section == "Health":
    st.header("🏥 Wellness")
    st.markdown("### The 20-20-20 Rule")
    st.write("To prevent digital eye strain, every 20 minutes, look at something 20 feet away for 20 seconds.")
    
    
    
    st.divider()
    st.progress(min(st.session_state.water / 2000, 1.0))
    st.write(f"Water: {st.session_state.water}/2000 ml")

# ==========================================================
# 8. DASHBOARD
# ==========================================================
elif section == "Dashboard":
    st.header("📊 Performance Data")
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.pie(df, names='status', hole=0.4, title="Goal Progress")
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data available yet.")

# ==========================================================
# 9. BACKGROUND LOGIC
# ==========================================================
st.sidebar.divider()
if st.sidebar.button("🥤 Log 250ml Water"):
    st.session_state.water += 250
    st.rerun()

# Toast alert for water
if (now - st.session_state.last_check).total_seconds() > 1800:
    st.toast("Time for water! 💧", icon="🥤")
    st.session_state.last_check = now

# Auto-refresh app every few seconds to keep clock and toasts active
time.sleep(5)
st.rerun()
