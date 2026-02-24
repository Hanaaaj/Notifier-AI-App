import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import threading
import datetime
import json
import os
import google.generativeai as genai
from plyer import notification

# --- 1. CORE AI & LOGIC ENGINE ---
class FocusFlowEngine:
    def __init__(self):
        self.data_file = "focus_flow_data.json"
        self.api_key = None
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.initialize_default_data()
        else:
            self.initialize_default_data()

    def initialize_default_data(self):
        self.data = {
            "study_plans": [],
            "work_tasks": [],
            "health": {"water": 0, "exercise": False, "sleep": 8},
            "stats": {"completed": 0, "missed": 0, "daily_history": []}
        }
        self.save_data()

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f)

    def configure_gemini(self, key):
        self.api_key = key
        genai.configure(api_key=key)

    def get_gemini_advice(self, prompt_type, context):
        """Generative AI Layer for Smart Feedback"""
        if not self.api_key:
            return "Enter a Gemini API Key in the sidebar for AI insights!"
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"Context: {context}. Task: {prompt_type}. Keep it concise and encouraging."
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"AI logic paused: {str(e)}"

    def calculate_study_logic(self, topics, days, hours):
        """Rule-based scheduling with burnout prevention"""
        if days <= 0: return []
        
        # Burnout Prevention: Limit workload if hours > 8
        intensity = "High" if hours > 6 else "Balanced"
        topics_per_day = -(-len(topics) // days) # Ceiling division
        
        plan = []
        for i in range(days):
            day_topics = topics[i*topics_per_day : (i+1)*topics_per_day]
            if not day_topics: break
            plan.append({
                "Date": str(datetime.date.today() + datetime.timedelta(days=i)),
                "Topics": ", ".join(day_topics),
                "Routine": "60m Study / 20m Break",
                "Reminders": "Water every 10m"
            })
        return plan

# --- 2. BACKGROUND NOTIFIER THREAD ---
def background_notifier():
    """Independent thread for system notifications"""
    # Note: Streamlit's architecture re-runs the script on interaction. 
    # We use a global check to ensure this thread only starts once.
    count = 0
    while True:
        # Every 10 minutes (600 seconds)
        time.sleep(600)
        notification.notify(
            title="💧 FocusFlow: Hydration",
            message="10 minutes passed! Take a sip of water.",
            timeout=5
        )
        count += 1
        # Every 3 hours (18 * 10 mins)
        if count % 18 == 0:
            notification.notify(
                title="🧘 FocusFlow: Movement",
                message="3 hours of work reached. Stretch for 5 minutes!",
                timeout=10
            )

# --- 3. STREAMLIT UI SETUP ---
st.set_page_config(page_title="FocusFlow AI", page_icon="🚀", layout="wide")

if 'engine' not in st.session_state:
    st.session_state.engine = FocusFlowEngine()

if 'notifier_started' not in st.session_state:
    threading.Thread(target=background_notifier, daemon=True).start()
    st.session_state.notifier_started = True

# --- SIDEBAR ---
st.sidebar.title("🚀 FocusFlow AI")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Dashboard", ["Study Orchestrator", "Work Engine", "Health Hub", "Analytics"])
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your key at aistudio.google.com")

if api_key:
    st.session_state.engine.configure_gemini(api_key)

# --- SECTION 1: STUDY ---
if menu == "Study Orchestrator":
    st.header("📚 AI Study Orchestrator")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            mod_name = st.text_input("Module Name", placeholder="e.g. Data Science")
            exam_date = st.date_input("Exam/Deadline Date")
            daily_hours = st.slider("Daily Study Hours", 1, 12, 4)
        with c2:
            topics_input = st.text_area("List Topics (comma-separated)", placeholder="Topic 1, Topic 2, ...")
    
    if st.button("Generate Smart Timetable"):
        topics = [t.strip() for t in topics_input.split(",") if t.strip()]
        days_rem = (exam_date - datetime.date.today()).days
        
        if not topics or days_rem <= 0:
            st.error("Please enter topics and a future date.")
        else:
            plan = st.session_state.engine.calculate_study_logic(topics, days_rem, daily_hours)
            st.session_state.engine.data['study_plans'] = plan
            st.session_state.engine.save_data()
            
            # AI Insight
            with st.spinner("AI Analysis..."):
                advice = st.session_state.engine.get_gemini_advice(
                    "Break down these topics for a student and suggest a logical order", topics_input
                )
                st.info(f"🧠 AI Breakdown Assistant:\n{advice}")

    if st.session_state.engine.data['study_plans']:
        st.subheader("Current Timetable")
        st.table(pd.DataFrame(st.session_state.engine.data['study_plans']))

# --- SECTION 2: WORK ---
elif menu == "Work Engine":
    st.header("💼 Work & Focus Block Engine")
    
    with st.form("task_form"):
        t_name = st.text_input("Task Description")
        t_pri = st.select_slider("Priority", options=["Low", "Medium", "High"])
        if st.form_submit_button("Add to Focus Block"):
            st.session_state.engine.data['work_tasks'].append({"task": t_name, "priority": t_pri, "done": False})
            st.session_state.engine.save_data()
            st.rerun()

    st.subheader("Focus Queue")
    for i, t in enumerate(st.session_state.engine.data['work_tasks']):
        col_t, col_b = st.columns([4, 1])
        col_t.write(f"**[{t['priority']}]** {t['task']}")
        if col_b.button("Complete ✅", key=f"btn_{i}"):
            st.session_state.engine.data['work_tasks'].pop(i)
            st.session_state.engine.data['stats']['completed'] += 1
            st.session_state.engine.save_data()
            st.rerun()

# --- SECTION 3: HEALTH ---
elif menu == "Health Hub":
    st.header("🌿 Health & Wellness Tracker")
    h = st.session_state.engine.data['health']
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Hydration Goal", f"{h['water']} / 10 Glasses")
        if st.button("Drink Water 💧"):
            h['water'] += 1
            st.session_state.engine.save_data()
            st.rerun()
    with c2:
        st.write("Daily Movement")
        ex = st.toggle("Exercise Completed Today", value=h['exercise'])
        h['exercise'] = ex
        st.session_state.engine.save_data()
    with c3:
        sleep = st.number_input("Sleep Hours", 0, 15, h['sleep'])
        h['sleep'] = sleep
        st.session_state.engine.save_data()

    if st.button("Get AI Wellness Feedback"):
        context = f"Water: {h['water']}, Exercise: {h['exercise']}, Sleep: {h['sleep']}"
        feedback = st.session_state.engine.get_gemini_advice("Provide health advice based on these daily stats", context)
        st.success(feedback)

# --- SECTION 4: ANALYTICS ---
elif menu == "Analytics":
    st.header("📊 Performance Dashboard")
    stats = st.session_state.engine.data['stats']
    
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots()
        ax.bar(["Tasks Completed", "Tasks Pending"], [stats['completed'], len(st.session_state.engine.data['work_tasks'])], color=['#2ecc71', '#e74c3c'])
        ax.set_title("Work Progress")
        st.pyplot(fig)
    
    with c2:
        # Wellness Gauge
        score = (st.session_state.engine.data['health']['water'] * 5) + (30 if st.session_state.engine.data['health']['exercise'] else 0)
        st.subheader(f"Current Wellness Score: {min(score, 100)}/100")
        st.progress(min(score/100, 1.0))
