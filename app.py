import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime
import json
import time

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="AuraFlow Pro", page_icon="🧠", layout="wide")

# Modern UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffa3; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1e2130; border-radius: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE MOCKUP (Persistent for Session) ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"completed": 0, "missed": 0, "water": 0}

# --- 3. CORE LOGIC: NOTIFICATIONS & AI ---
def send_notification(title, message):
    """Triggers a browser-level notification."""
    js = f"""<script>
    if (Notification.permission === "granted") {{
        new Notification("{title}", {{ body: "{message}" }});
    }} else {{ Notification.requestPermission(); }}
    </script>"""
    st.components.v1.html(js, height=0)

def get_ai_feedback(score):
    """Prompt Engineering: AI Analysis of the user's day."""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"The user has a productivity score of {score}%. Give one actionable, supportive tip."
        return model.generate_content(prompt).text
    except:
        return "Keep focusing! Consistency is the key to success."

# --- 4. APP LAYOUT ---
st.title("🌊 AuraFlow: Intelligence Notifier")
st.caption("2026 Hackathon Submission | AI-Driven Productivity")

# Request permissions early
if st.button("🔔 Enable Background Notifications (Click First)"):
    st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)

tabs = st.tabs(["🎯 Task Manager", "📈 Analytics Dashboard", "🤖 Smart Feedback"])

# --- TAB 1: TASK MANAGEMENT ---
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Add New Goal")
        t_name = st.text_input("Task Title", placeholder="e.g., Weekly Sync")
        t_type = st.selectbox("Category", ["Meeting", "Deadline", "Hydration"])
        t_time = st.time_input("Scheduled Time", datetime.now())
        
        if st.button("➕ Schedule Task"):
            st.session_state.tasks.append({
                "id": len(st.session_state.tasks),
                "name": t_name,
                "type": t_type,
                "time": t_time.strftime("%H:%M"),
                "status": "Pending"
            })
            st.toast("Task added successfully!")

    with col2:
        st.subheader("Pending Reminders")
        for i, task in enumerate(st.session_state.tasks):
            if task["status"] == "Pending":
                with st.expander(f"{task['time']} - {task['name']} ({task['type']})"):
                    if st.button(f"Mark Complete", key=f"done_{i}"):
                        st.session_state.tasks[i]["status"] = "Completed"
                        st.session_state.stats["completed"] += 1
                        if task['type'] == "Hydration": st.session_state.stats["water"] += 1
                        st.rerun()
                    if st.button(f"Mark Missed", key=f"miss_{i}"):
                        st.session_state.tasks[i]["status"] = "Missed"
                        st.session_state.stats["missed"] += 1
                        st.rerun()

# --- TAB 2: ANALYTICS DASHBOARD ---
with tabs[1]:
    # Calculate Score
    total = st.session_state.stats["completed"] + st.session_state.stats["missed"]
    score = int((st.session_state.stats["completed"] / total) * 100) if total > 0 else 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Productivity Score", f"{score}%")
    m2.metric("Completed Tasks", st.session_state.stats["completed"])
    m3.metric("Hydration Level", f"{st.session_state.stats['water']} Cups")

    if total > 0:
        df = pd.DataFrame([
            {"Label": "Completed", "Value": st.session_state.stats["completed"]},
            {"Label": "Missed", "Value": st.session_state.stats["missed"]}
        ])
        fig = px.bar(df, x="Label", y="Value", color="Label", 
                     color_discrete_map={"Completed": "#00ffa3", "Missed": "#ff4b4b"},
                     title="Task Performance Overview")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet. Schedule and complete tasks to generate charts!")

# --- TAB 3: SMART FEEDBACK ---
with tabs[2]:
    st.subheader("AI Performance Insights")
    if total > 0:
        feedback = get_ai_feedback(score)
        st.success(feedback)
    else:
        st.write("Complete your first task to unlock AI insights.")

# --- 5. THE BACKGROUND TICKER (Simulated) ---
# In a real Streamlit app, this checks if current time matches scheduled tasks
now = datetime.now().strftime("%H:%M")
for task in st.session_state.tasks:
    if task["time"] == now and task["status"] == "Pending":
        send_notification(f"Time for {task['name']}!", f"Category: {task['type']}")
