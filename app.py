import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from datetime import datetime
import time

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Smart Productivity Assistant",
    page_icon="🚀",
    layout="wide"
)

# -----------------------------
# GEMINI CONFIGURATION
# -----------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-pro")

# -----------------------------
# SESSION STATE INITIALIZATION
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "tasks_completed" not in st.session_state:
    st.session_state.tasks_completed = 0

if "water_intake" not in st.session_state:
    st.session_state.water_intake = 0

if "last_water_popup" not in st.session_state:
    st.session_state.last_water_popup = time.time()

# -----------------------------
# TITLE
# -----------------------------
st.title("🚀 Smart Productivity Assistant")
st.markdown("AI-powered assistant with tracking, analytics & hydration reminders")

# -----------------------------
# SIDEBAR - PROGRESS TRACKER
# -----------------------------
st.sidebar.header("📊 Daily Progress")

task_goal = 5
water_goal = 8

task_progress = st.session_state.tasks_completed / task_goal
water_progress = st.session_state.water_intake / water_goal

st.sidebar.subheader("Tasks Completed")
st.sidebar.progress(min(task_progress, 1.0))
st.sidebar.write(f"{st.session_state.tasks_completed} / {task_goal}")

st.sidebar.subheader("Water Intake (glasses)")
st.sidebar.progress(min(water_progress, 1.0))
st.sidebar.write(f"{st.session_state.water_intake} / {water_goal}")

# -----------------------------
# MAIN CHAT SECTION
# -----------------------------
st.subheader("💬 Chat with AI")

user_input = st.text_input("Ask something...")

if st.button("Send"):
    if user_input:
        response = model.generate_content(user_input)
        ai_reply = response.text

        # Store chat history
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("AI", ai_reply))

# Display chat history
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**🧑 {sender}:** {message}")
    else:
        st.markdown(f"**🤖 {sender}:** {message}")

# -----------------------------
# TASK COMPLETION BUTTON
# -----------------------------
st.subheader("✅ Complete a Task")

if st.button("Mark Task as Completed"):
    st.session_state.tasks_completed += 1
    st.success("Great job! Task completed 🎉")

# -----------------------------
# WATER TRACKER
# -----------------------------
st.subheader("💧 Hydration Tracker")

if st.button("Drank a Glass of Water"):
    st.session_state.water_intake += 1
    st.success("Hydration updated 💦")

# -----------------------------
# AUTOMATIC HYDRATION POPUP SIMULATION
# -----------------------------
current_time = time.time()

if current_time - st.session_state.last_water_popup > 30:  # every 30 sec for demo
    st.warning("⏰ Hydration Reminder: Drink water!")
    st.session_state.last_water_popup = current_time

# -----------------------------
# ANALYTICS SECTION
# -----------------------------
st.subheader("📈 Productivity Analytics")

data = {
    "Category": ["Tasks Completed", "Water Intake"],
    "Count": [st.session_state.tasks_completed, st.session_state.water_intake]
}

df = pd.DataFrame(data)

st.bar_chart(df.set_index("Category"))

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
