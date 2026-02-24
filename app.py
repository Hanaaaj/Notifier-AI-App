import streamlit as st
import pandas as pd
import plotly.express as px
import json
import threading
import time
import math
from datetime import datetime
from google import genai

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="MindFlow | Adaptive Intelligence",
    page_icon="✨",
    layout="wide"
)

# ==========================================================
# GEMINI SETUP (NEW SDK - WORKING VERSION)
# ==========================================================
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def generate_ai_feedback(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI temporarily unavailable: {e}"

# ==========================================================
# DATA STORAGE
# ==========================================================
DATA_FILE = "mindflow_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

if "db" not in st.session_state:
    st.session_state.db = load_data()

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "water" not in st.session_state:
    st.session_state.water = 0

if "hydration_alert" not in st.session_state:
    st.session_state.hydration_alert = False

# ==========================================================
# BACKGROUND HYDRATION REMINDER (NON-BLOCKING)
# ==========================================================
def hydration_loop():
    while True:
        time.sleep(600)  # 10 minutes
        st.session_state.hydration_alert = True

if "thread_started" not in st.session_state:
    thread = threading.Thread(target=hydration_loop, daemon=True)
    thread.start()
    st.session_state.thread_started = True

if st.session_state.hydration_alert:
    st.warning("💧 Hydration Reminder: Drink Water!")
    st.session_state.hydration_alert = False

# ==========================================================
# STUDY ENGINE (RULE-BASED AI)
# ==========================================================
def generate_study_plan(module, exam_date, topics, daily_hours):
    today = datetime.today().date()
    days_remaining = (exam_date - today).days

    if days_remaining <= 0:
        raise ValueError("Exam date must be in the future.")

    topics_per_day = math.ceil(len(topics) / days_remaining)

    # Overload prevention
    if topics_per_day > 3:
        topics_per_day = 3

    schedule = {}
    topic_index = 0

    for d in range(days_remaining):
        daily_topics = topics[topic_index: topic_index + topics_per_day]
        if not daily_topics:
            break

        schedule[f"Day {d+1}"] = {
            "topics": daily_topics,
            "study_hours": daily_hours,
            "break_rule": "20 min break after 60 min",
            "hydration": "Every 10 minutes",
            "exercise": "After 3 hours study"
        }
        topic_index += topics_per_day

    return {
        "module": module,
        "days_remaining": days_remaining,
        "topics_per_day": topics_per_day,
        "schedule": schedule
    }

# ==========================================================
# WORK ENGINE
# ==========================================================
def generate_focus_blocks(tasks, priorities):
    combined = list(zip(tasks, priorities))
    combined.sort(key=lambda x: x[1])

    blocks = []
    for task, p in combined:
        blocks.append({
            "task": task,
            "focus_block": "90 minutes",
            "hydration": "Every 10 minutes",
            "screen_break": "5 min after 60 minutes",
            "priority": p
        })
    return blocks

# ==========================================================
# HEALTH ENGINE
# ==========================================================
def calculate_wellness(water, exercise, sleep):
    score = (water/2000)*40 + (exercise/60)*30 + (sleep/8)*30
    return round(min(score, 100), 2)

# ==========================================================
# UI HEADER
# ==========================================================
st.title("MindFlow Adaptive Intelligence ✨")
st.caption("AI-powered Study • Work • Health Optimizer")

# ==========================================================
# NAVIGATION
# ==========================================================
section = st.sidebar.radio("Navigate", ["Study", "Work", "Health", "Dashboard"])

# ==========================================================
# STUDY SECTION
# ==========================================================
if section == "Study":
    st.header("📚 AI Study Planner")

    module = st.text_input("Module Name")
    exam_date = st.date_input("Exam Date")
    topics = st.text_area("Topics (comma separated)")
    daily_hours = st.number_input("Daily Study Hours", 1, 12)

    if st.button("Generate Study Plan"):
        try:
            topic_list = [t.strip() for t in topics.split(",")]
            plan = generate_study_plan(module, exam_date, topic_list, daily_hours)

            st.success("Study Plan Generated!")
            st.json(plan)

            feedback = generate_ai_feedback(
                f"Provide motivational academic feedback for this study plan: {plan}"
            )
            st.info(feedback)

        except Exception as e:
            st.error(str(e))

# ==========================================================
# WORK SECTION
# ==========================================================
elif section == "Work":
    st.header("💼 Work Focus Planner")

    tasks = st.text_area("Tasks (comma separated)")
    priorities = st.text_area("Priorities (comma separated numbers)")

    if st.button("Generate Focus Blocks"):
        try:
            task_list = [t.strip() for t in tasks.split(",")]
            priority_list = [int(p.strip()) for p in priorities.split(",")]

            blocks = generate_focus_blocks(task_list, priority_list)

            st.success("Focus Blocks Generated")
            st.json(blocks)

        except Exception as e:
            st.error(str(e))

# ==========================================================
# HEALTH SECTION
# ==========================================================
elif section == "Health":
    st.header("🏥 Health Optimizer")

    exercise = st.number_input("Exercise Minutes", 0, 180, 30)
    sleep = st.number_input("Sleep Hours", 4, 12, 7)

    if st.button("Calculate Wellness"):
        score = calculate_wellness(st.session_state.water, exercise, sleep)
        st.metric("Wellness Score", f"{score}/100")

# ==========================================================
# DASHBOARD
# ==========================================================
elif section == "Dashboard":
    st.header("📊 Performance Dashboard")

    completed = len([t for t in st.session_state.tasks if t.get("status") == "Done"])
    pending = len([t for t in st.session_state.tasks if t.get("status") == "Pending"])

    df = pd.DataFrame({
        "Status": ["Completed", "Pending"],
        "Count": [completed, pending]
    })

    fig = px.bar(df, x="Status", y="Count", color="Status")
    st.plotly_chart(fig, use_container_width=True)

    trend = [3, 5, 4, 6, 7, 5, 8]
    trend_df = pd.DataFrame({"Day": range(1, 8), "Score": trend})
    fig2 = px.line(trend_df, x="Day", y="Score", title="Productivity Trend")
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================================
# SIDEBAR HYDRATION
# ==========================================================
st.sidebar.markdown("### 💧 Hydration Tracker")
add_water = st.sidebar.select_slider("Add water (ml)", options=[250, 500, 750])
if st.sidebar.button("Log Water"):
    st.session_state.water += add_water
    st.sidebar.success(f"Added {add_water}ml")
    st.rerun()
