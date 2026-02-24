import streamlit as st
from datetime import datetime
import time

# 1. Setup
st.set_page_config(page_title="Simple Notifier", page_icon="🔔")

# 2. Initialize Session State
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# 3. Sidebar - Settings
st.sidebar.title("🔔 Settings")
interval = st.sidebar.slider("Notification Interval (mins)", 1, 60, 20)
if st.sidebar.button("Reset Timer"):
    st.session_state.start_time = time.time()
    st.toast("Timer Reset!")

# 4. Main UI
st.title("Focus & Notify")

# Task Input
with st.form("task_form", clear_on_submit=True):
    new_task = st.text_input("Enter a priority task:")
    if st.form_submit_button("Add Task"):
        if new_task:
            st.session_state.tasks.append(new_task)
            st.rerun()

# Display Tasks
if st.session_state.tasks:
    st.subheader("Your Priorities")
    for i, task in enumerate(st.session_state.tasks):
        col1, col2 = st.columns([4, 1])
        col1.write(f"✅ {task}")
        if col2.button("Done", key=f"done_{i}"):
            st.session_state.tasks.pop(i)
            st.rerun()
else:
    st.info("No active tasks. Add one above!")

# 5. The Notifier Logic
elapsed_time = time.time() - st.session_state.start_time
remaining = (interval * 60) - elapsed_time

st.divider()
if remaining <= 0:
    st.balloons()
    st.toast("🔔 TIME'S UP! Take a break or drink water!", icon="💧")
    st.warning("⏰ Notification Triggered! Please reset the timer in the sidebar.")
else:
    mins, secs = divmod(int(remaining), 60)
    st.metric("Next Notification In", f"{mins:02d}:{secs:02d}")
    # Auto-refresh every 10 seconds to update the countdown
    time.sleep(10)
    st.rerun()
