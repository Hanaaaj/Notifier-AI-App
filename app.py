import json
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ---------------------- SIMPLE DICT DATA (NO DATACLASSES) ----------------------
def create_study_task(module, topic, date, start_time, duration_min, is_break=False, completed=False):
    return {
        "module": module,
        "topic": topic,
        "date": date,
        "start_time": start_time,
        "duration_min": duration_min,
        "is_break": is_break,
        "completed": completed
    }

def create_work_task(title, date, start_time, duration_min, priority="Medium", completed=False):
    return {
        "title": title,
        "date": date,
        "start_time": start_time,
        "duration_min": duration_min,
        "priority": priority,
        "completed": completed
    }

def create_health_day(date, water_goal=8, water_done=0, exercise_goal=30, exercise_done=0, sleep_goal=8.0, sleep_done=0.0):
    return {
        "date": date,
        "water_goal_glasses": water_goal,
        "water_taken_glasses": water_done,
        "exercise_minutes_target": exercise_goal,
        "exercise_minutes_done": exercise_done,
        "sleep_hours_target": sleep_goal,
        "sleep_hours_done": sleep_done
    }

# ---------------------- PLANNER ----------------------
class Planner:
    def plan_study(self, module, exam_date, topics, daily_hours):
        days_remaining = max(1, (exam_date.date() - datetime.now().date()).days)
        total_minutes = min(int(daily_hours * 60), 360)
        topics_per_day = max(1, len(topics) // days_remaining)
        
        plan = []
        topic_idx = 0
        current_date = datetime.now().date()
        
        for day in range(days_remaining):
            day_topics = topics[topic_idx:topic_idx + topics_per_day]
            topic_idx += len(day_topics)
            
            if not day_topics:
                break
                
            available_min = total_minutes
            current_time = datetime.combine(current_date, datetime.min.time()).replace(hour=9)
            
            for topic in day_topics:
                if available_min <= 0:
                    break
                duration = min(60, available_min)
                plan.append(create_study_task(module, topic, current_date.isoformat(), 
                                            current_time.strftime("%H:%M"), duration))
                available_min -= duration
                current_time += timedelta(minutes=duration)
                
                if available_min > 0 and duration >= 60:
                    plan.append(create_study_task(module, "BREAK", current_date.isoformat(), 
                                                current_time.strftime("%H:%M"), 20, True))
                    available_min -= 20
                    current_time += timedelta(minutes=20)
            
            current_date += timedelta(days=1)
        return plan

    def plan_work(self, meetings, deadlines):
        tasks = []
        for deadline in deadlines:
            day_before = (datetime.strptime(deadline["date"], "%Y-%m-%d").date() - timedelta(days=1)).isoformat()
            tasks.append(create_work_task(f"Focus: {deadline['title']}", day_before, "14:00", 50, "High"))
        for meeting in meetings:
            tasks.append(create_work_task(meeting["title"], meeting["date"], meeting["start_time"], 60, "Medium"))
        return tasks

# ---------------------- STORAGE ----------------------
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"study_plan": [], "work_tasks": [], "health_days": {}, "analytics": {"dates": [], "study": [0,0], "work": [0,0], "wellness": []}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------------- INIT ----------------------
def init_app():
    if "planner" not in st.session_state:
        st.session_state.planner = Planner()
        st.session_state.study_plan = []
        st.session_state.work_tasks = []
        st.session_state.health_days = {}
        st.session_state.temp_meetings = []
        st.session_state.temp_deadlines = []
        st.session_state.last_hydration = None
        st.session_state.analytics = {"dates": [], "study": [0,0], "work": [0,0], "wellness": []}
        data = load_data()
        st.session_state.study_plan = data.get("study_plan", [])
        st.session_state.work_tasks = data.get("work_tasks", [])
        st.session_state.health_days = data.get("health_days", {})

# ---------------------- REMINDERS ----------------------
def check_reminders():
    plan = st.session_state.study_plan
    now = datetime.now()
    today = now.date().isoformat()
    
    for task in plan:
        if (task["date"] == today and not task["is_break"] and 
            task["completed"] == False):
            start = datetime.strptime(f"{task['date']} {task['start_time']}", "%Y-%m-%d %H:%M")
            end = start + timedelta(minutes=task["duration_min"])
            if start <= now <= end:
                if st.session_state.last_hydration is None or (now - st.session_state.last_hydration).seconds > 600:
                    st.session_state.last_hydration = now
                    st.warning("💧 **HYDRATION REMINDER**: Drink water now!")
                return
    st.session_state.last_hydration = now

# ---------------------- STUDY PAGE ----------------------
def study_page():
    st.header("📚 Study Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        module = st.text_input("Module Name")
        exam_date = st.date_input("Exam Date", datetime.now())
    with col2:
        daily_hours = st.number_input("Daily Hours", 1.0, 8.0, 2.0)
    
    topics = st.text_area("Topics (one per line)").strip().split("\n")
    topics = [t.strip() for t in topics if t.strip()]
    
    if st.button("🎯 Generate Timetable") and module and topics:
        plan = st.session_state.planner.plan_study(module, exam_date, topics, daily_hours)
        st.session_state.study_plan = plan
        save_data({"study_plan": plan})
        st.success("✅ Timetable created!")
        st.rerun()
    
    if st.session_state.study_plan:
        st.subheader("📋 Your Schedule")
        for i, task in enumerate(st.session_state.study_plan):
            col1, col2 = st.columns([5, 1])
            with col1:
                icon = "⏸️" if task["is_break"] else "📖"
                status = "✅" if task["completed"] else "⏳"
                st.write(f"{status} {icon} {task['date']} {task['start_time']} ({task['duration_min']}min) {task['topic']}")
            with col2:
                if not task["is_break"]:
                    key = f"study_{i}"
                    st.session_state[key] = st.session_state.get(key, False)
                    st.checkbox("Done", key=key)
        
        st.subheader("🔔 Live Reminders")
        check_reminders()

# ---------------------- WORK PAGE ----------------------
def work_page():
    st.header("💼 Work Planner")
    
    st.subheader("➕ Add Meeting")
    col1, col2, col3 = st.columns(3)
    with col1: title = st.text_input("Title")
    with col2: date = st.date_input("Date")
    with col3: time = st.time_input("Time")
    
    if st.button("Add Meeting") and title:
        st.session_state.temp_meetings.append({"title": title, "date": date.isoformat(), "start_time": str(time)[:5]})
        st.rerun()
    
    if st.button("🎯 Generate Work Plan") and st.session_state.temp_meetings:
        tasks = st.session_state.planner.plan_work(st.session_state.temp_meetings, st.session_state.temp_deadlines)
        st.session_state.work_tasks = tasks
        st.success("✅ Work plan created!")
    
    if st.session_state.work_tasks:
        st.subheader("📋 Work Tasks")
        for i, task in enumerate(st.session_state.work_tasks):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📅 {task['date']} {task['start_time']} - {task['title']}")
            with col2:
                key = f"work_{i}"
                st.session_state[key] = st.session_state.get(key, False)
                st.checkbox("Done", key=key)

# ---------------------- HEALTH PAGE ----------------------
def health_page():
    st.header("💚 Health Tracker")
    
    today = datetime.now().date().isoformat()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Goals")
        water_goal = st.number_input("Water (glasses)", 4, 16, 8)
        exercise_goal = st.number_input("Exercise (min)", 0, 120, 30)
        sleep_goal = st.number_input("Sleep (hours)", 4.0, 12.0, 8.0)
    with col2:
        st.subheader("✅ Actual")
        water_done = st.number_input("Water done", 0, 16, 0)
        exercise_done = st.number_input("Exercise done", 0, 120, 0)
        sleep_done = st.number_input("Sleep done", 0.0, 12.0, 0.0)
    
    if st.button("💾 Save Today"):
        health = create_health_day(today, water_goal, water_done, exercise_goal, exercise_done, sleep_goal, sleep_done)
        st.session_state.health_days[today] = health
        save_data({
            "study_plan": st.session_state.study_plan,
            "work_tasks": st.session_state.work_tasks,
            "health_days": st.session_state.health_days
        })
        st.success("✅ Saved!")
    
    if today in st.session_state.health_days:
        h = st.session_state.health_days[today]
        col1, col2, col3 = st.columns(3)
        col1.metric("💧 Water", f"{h['water_taken_glasses']}/{h['water_goal_glasses']}")
        col2.metric("🏃 Exercise", f"{h['exercise_minutes_done']}/{h['exercise_minutes_target']}")
        col3.metric("😴 Sleep", f"{h['sleep_hours_done']}/{h['sleep_hours_target']}")

# ---------------------- DASHBOARD ----------------------
def dashboard_page():
    st.header("📊 Analytics Dashboard")
    
    if not st.session_state.study_plan and not st.session_state.work_tasks:
        st.info("👆 Use Study/Work tabs first to see charts!")
        return
    
    # Simple analytics
    study_tasks = [t for t in st.session_state.study_plan if not t["is_break"]]
    study_done = sum(1 for t in study_tasks if t["completed"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Study Sessions", f"{study_done}/{len(study_tasks)}")
        st.metric("💼 Work Tasks", f"{sum(1 for t in st.session_state.work_tasks if t['completed'])}/{len(st.session_state.work_tasks)}")
    
    # Charts
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    
    # Study progress
    ax[0].pie([study_done, len(study_tasks)-study_done], labels=["Done", "Pending"], autopct='%1.1f%%', colors=['green', 'orange'])
    ax[0].set_title("Study Progress")
    
    # Work progress  
    work_done = sum(1 for t in st.session_state.work_tasks if t["completed"])
    work_total = len(st.session_state.work_tasks)
    ax[1].pie([work_done, work_total-work_done], labels=["Done", "Pending"], autopct='%1.1f%%', colors=['blue', 'lightblue'])
    ax[1].set_title("Work Progress")
    
    st.pyplot(fig)

# ---------------------- MAIN APP ----------------------
def main():
    st.set_page_config(page_title="Study Notifier", layout="wide")
    
    init_app()
    
    st.title("🚀 AI Study • Work • Health Notifier")
    
    page = st.sidebar.selectbox("📂 Go to", ["Study", "Work", "Health", "Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ✨ **Features:**
    - 📚 Smart study timetables  
    - 💼 Work task planner
    - 💚 Health tracking
    - 🔔 Auto reminders
    - 📊 Live analytics
    """)
    
    if page == "Study":
        study_page()
    elif page == "Work":
        work_page()
    elif page == "Health":
        health_page()
    elif page == "Dashboard":
        dashboard_page()
    
    if st.sidebar.button("💾 Save Everything"):
        save_data({
            "study_plan": st.session_state.study_plan,
            "work_tasks": st.session_state.work_tasks,
            "health_days": st.session_state.health_days
        })
        st.sidebar.success("✅ Saved!")

if __name__ == "__main__":
    main()

