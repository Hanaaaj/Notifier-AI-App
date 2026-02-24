import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

# Config
st.set_page_config(page_title="Study Notifier", layout="wide", page_icon="📚")

st.title("📚 Study • Work • Health Notifier")
st.markdown("**Automatic reminders • Timetables • Progress tracking**")

# Sidebar navigation
page = st.sidebar.selectbox("Go to", ["Study", "Work", "Health", "Dashboard"])

# ========================================
# STUDY PLANNER
# ========================================
if page == "Study":
    st.header("📚 Study Planner")
    
    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        module = st.text_input("Module", "Mathematics")
        topics = st.text_area("Topics", "Topic 1\nTopic 2\nTopic 3").split("\n")
    with col2:
        exam_date = st.date_input("Exam Date", datetime.now())
        hours = st.slider("Daily hours", 1, 6, 2)
    
    if st.button("Generate Timetable"):
        st.session_state.plan = []
        for i, topic in enumerate([t.strip() for t in topics if t.strip()]):
            st.session_state.plan.append({
                "module": module,
                "topic": topic,
                "date": "2026-02-25",
                "time": f"09:0{i}",
                "duration": 60,
                "completed": False
            })
        st.success("✅ Timetable created!")
    
    # Show plan
    if "plan" in st.session_state and st.session_state.plan:
        st.subheader("📋 Your Schedule")
        for i, task in enumerate(st.session_state.plan):
            col1, col2 = st.columns([4, 1])
            with col1:
                status = "✅" if task["completed"] else "⏳"
                st.write(f"{status} 📖 {task['date']} {task['time']} - {task['topic']}")
            with col2:
                st.session_state[f"task_{i}"] = st.checkbox("Done", 
                    key=f"task_{i}", value=task["completed"])
                task["completed"]
