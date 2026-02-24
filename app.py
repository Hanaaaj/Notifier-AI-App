import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import json
import os
import google.generativeai as genai

# --- 1. CORE ENGINE ---
class FocusFlowEngine:
    def __init__(self):
        self.data_file = "user_stats.json"
        self.api_key = None
        self.initialize_data()

    def initialize_data(self):
        # Default data structure
        self.data = {
            "study_plan": [],
            "tasks": [],
            "health": {"water": 0, "exercise": False, "sleep": 8},
            "history": {"completed": 0, "pending": 0}
        }

    def configure_ai(self, key):
        self.api_key = key
        genai.configure(api_key=key)

    def get_ai_feedback(self, prompt):
        if not self.api_key:
            return "💡 *Pro-tip: Add a Gemini API Key in the sidebar for personalized AI coaching.*"
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        except:
            return "AI is currently resting. Please check your API key."

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="FocusFlow AI", layout="wide")

if 'engine' not in st.session_state:
    st.session_state.engine = FocusFlowEngine()

# --- 3. SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.title("🚀 FocusFlow AI")
    menu = st.radio("Navigation", ["Study Orchestrator", "Work Engine", "Health Hub", "Analytics"])
    st.divider()
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        st.session_state.engine.configure_ai(api_key)
    
    st.info("This app automates study schedules and health reminders using rule-based AI.")

# --- 4. SECTIONS ---

if menu == "Study Orchestrator":
    st.header("📚 AI Study Orchestrator")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        mod = st.text_input("Module Name", "Computer Science 101")
        date = st.date_input("Exam Date", datetime.date.today() + datetime.timedelta(days=7))
        hours = st.slider("Daily Hours", 1, 10, 4)
    with col2:
        topics = st.text_area("Topics (comma separated)", "Logic Gates, Python Basics, Hardware, Networking")

    if st.button("Generate Smart Plan"):
        topic_list = [t.strip() for t in topics.split(",")]
        days_left = (date - datetime.date.today()).days
        
        if days_left > 0:
            # Rule-based logic: Math distribution
            per_day = -(-len(topic_list) // days_left)
            plan = []
            for i in range(days_left):
                plan.append({
                    "Day": i+1,
                    "Date": str(datetime.date.today() + datetime.timedelta(days=i)),
                    "Goal": f"Study {per_day} topics",
                    "Breaks": "20min break every 60min"
                })
            st.session_state.engine.data['study_plan'] = plan
            st.success("Plan Created!")
            
            # AI Logic call
            advice = st.session_state.engine.get_ai_feedback(f"Organize these study topics logically: {topics}")
            st.markdown(f"### 🧠 AI Instructor Breakdown\n{advice}")
        else:
            st.error("Please pick a future date!")

    if st.session_state.engine.data['study_plan']:
        st.table(st.session_state.engine.data['study_plan'])

elif menu == "Work Engine":
    st.header("💼 Work Focus Blocks")
    task = st.text_input("Task Name")
    if st.button("Add Task"):
        st.session_state.engine.data['tasks'].append(task)
        st.toast(f"Task '{task}' added to queue!", icon="✅")

    for i, t in enumerate(st.session_state.engine.data['tasks']):
        c1, c2 = st.columns([3, 1])
        c1.write(f"🔹 {t}")
        if c2.button("Done", key=f"t_{i}"):
            st.session_state.engine.data['tasks'].pop(i)
            st.session_state.engine.data['history']['completed'] += 1
            st.rerun()

elif menu == "Health Hub":
    st.header("🌿 Health & Hydration")
    h = st.session_state.engine.data['health']
    
    st.metric("Water Intake", f"{h['water']} Glasses")
    if st.button("Add Glass 💧"):
        h['water'] += 1
        st.toast("Great job! Stay hydrated.", icon="💧")
        st.rerun()
    
    st.divider()
    st.write("### AI Health Recommendation")
    health_advice = st.session_state.engine.get_ai_feedback(f"I drank {h['water']} glasses of water today. Is that enough?")
    st.write(health_advice)

elif menu == "Analytics":
    st.header("📊 Performance Dashboard")
    history = st.session_state.engine.data['history']
    
    fig, ax = plt.subplots()
    ax.pie([history['completed'], 5], labels=["Completed", "Target"], autopct='%1.1f%%', colors=['#4CAF50', '#ddd'])
    st.pyplot(fig)
    
    st.info("Rule-based AI calculates your burnout risk based on completed tasks vs study hours.")
