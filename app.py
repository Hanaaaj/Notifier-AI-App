import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

import streamlit as st
import matplotlib.pyplot as plt


# ---------------------- DATA MODELS ----------------------
@dataclass
class StudyTask:
    module: str
    topic: str
    date: str
    start_time: str
    duration_min: int
    is_break: bool
    completed: bool

@dataclass
class WorkTask:
    title: str
    date: str
    start_time: str
    duration_min: int
    priority: str
    completed: bool

@dataclass
class HealthDay:
    date: str
    water_goal_glasses: int
    water_taken_glasses: int
    exercise_minutes_target: int
    exercise_minutes_done: int
    sleep_hours_target: float
    sleep_hours_done: float


# ---------------------- RULE-BASED ENGINE ----------------------
class RuleBasedPlanner:
    def __init__(self, max_study_minutes_per_day=360, max_work_minutes_per_day=420):
        self.max_study_minutes_per_day = max_study_minutes_per_day
        self.max_work_minutes_per_day = max_work_minutes_per_day

    def plan_study(self, module_name: str, exam_date: datetime, project_deadline: datetime,
                   topics: List[str], daily_hours: float, start_hour: int = 9) -> List[StudyTask]:
        days_remaining = max(1, (exam_date.date() - datetime.now().date()).days)
        total_minutes_per_day = min(int(daily_hours * 60), self.max_study_minutes_per_day)
        topics_per_day = max(1, len(topics) // days_remaining)
        
        plan = []
        topic_index = 0
        current_date = datetime.now().date()

        while topic_index < len(topics):
            day_topics = topics[topic_index:topic_index + topics_per_day]
            topic_index += len(day_topics)
            
            available_minutes = total_minutes_per_day
            current_start = datetime.combine(current_date, datetime.min.time()).replace(
                hour=start_hour, minute=0)
            
            per_topic_minutes = max(30, available_minutes // max(1, len(day_topics)))

            for topic in day_topics:
                if available_minutes <= 0:
                    break
                duration = min(per_topic_minutes, available_minutes)
                plan.append(StudyTask(module_name, topic, current_date.isoformat(),
                                    current_start.strftime("%H:%M"), duration, False, False))
                available_minutes -= duration

                if available_minutes > 0 and duration >= 60:
                    break_start = current_start + timedelta(minutes=duration)
                    plan.append(StudyTask(module_name, "Break", current_date.isoformat(),
                                        break_start.strftime("%H:%M"), 20, True, False))
                    available_minutes -= 20
                    current_start = break_start + timedelta(minutes=20)
                else:
                    current_start += timedelta(minutes=duration)
            
            current_date += timedelta(days=1)
        return plan

    def plan_work(self, meetings: List[Dict], deadlines: List[Dict], focus_block_minutes=50) -> List[WorkTask]:
        tasks = []
        for d in deadlines:
            day_before = (datetime.strptime(d["date"], "%Y-%m-%d").date() - timedelta(days=1)).isoformat()
            tasks.append(WorkTask(f"Focus: {d['title']}", day_before, "14:00", focus_block_minutes, "High", False))
        for m in meetings:
            tasks.append(WorkTask(f"Meeting: {m['title']}", m["date"], m["start_time"], 
                                m.get("duration_min", 60), "Medium", False))
        return tasks

    def generate_feedback_message(self, study_plan: List[StudyTask]) -> str:
        if not study_plan:
            return "No study sessions scheduled yet."
        first = study_plan[0]
        topics = [t for t in study_plan if not t.is_break]
        completed = len([t for t in topics if t.completed])
        return f"{len(topics)} topics total ({completed} done). Study starting at {first.start_time}. Hydrate every 10 min, break after 60 min."


# ---------------------- STORAGE ----------------------
DATA_FILE = "schedule_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------- SESSION HELPERS ----------------------
def init_session_state():
    defaults = {
        "planner": RuleBasedPlanner(),
        "study_plan": [],
        "work_tasks": [],
        "health_days": {},
        "analytics": {"history_dates": [], "study_completed": [], "study_total": [], 
                     "work_completed": [], "work_total": [], "wellness_scores": []},
        "last_hydration_check": None,
        "study_minutes_in_current_block": 0,
        "temp_meetings": [],
        "temp_deadlines": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_state_from_file():
    data = load_data()
    st.session_state["study_plan"] = [StudyTask(**item) for item in data.get("study_plan", [])]
    st.session_state["work_tasks"] = [WorkTask(**item) for item in data.get("work_tasks", [])]
    st.session_state["health_days"] = {d: HealthDay(**hd) for d, hd in data.get("health_days", {}).items()}
    st.session_state["analytics"] = data.get("analytics", st.session_state["analytics"])


def save_state_to_file():
    data = {
        "study_plan": [asdict(s) for s in st.session_state["study_plan"]],
        "work_tasks": [asdict(w) for w in st.session_state["work_tasks"]],
        "health_days": {d: asdict(h) for d, h in st.session_state["health_days"].items()},
        "analytics": st.session_state["analytics"]
    }
    save_data(data)


# ---------------------- STUDY REMINDERS ----------------------
def check_study_reminders():
    plan = st.session_state["study_plan"]
    if not plan:
        return

    now = datetime.now()
    today_str = now.date().isoformat()
    
    for s in plan:
        if s.date == today_str and not s.is_break:
            start = datetime.strptime(f"{s.date} {s.start_time}", "%Y-%m-%d %H:%M")
            end = start + timedelta(minutes=s.duration_min)
            if start <= now <= end:
                minutes_since_start = int((now - start).total_seconds() // 60)
                
                last = st.session_state["last_hydration_check"]
                if last is None or (now - last).total_seconds() / 60 >= 10:
                    st.session_state["last_hydration_check"] = now
                    st.warning("💧 Hydration reminder: drink water!")
                
                if minutes_since_start >= 60:
                    st.error("⏸️ Break reminder: Take a 20-minute break now!")
                return


# ---------------------- PAGES ----------------------
def page_study():
    st.header("📚 Study Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        module = st.text_input("Module name")
        exam_date = st.date_input("Exam date")
    with col2:
        project_deadline = st.date_input("Project deadline")
        daily_hours = st.number_input("Daily study hours", min_value=0.5, max_value=12.0, value=2.0)
    
    topics_text = st.text_area("Topics (one per line)")
    
    if st.button("Generate Timetable"):
        topics = [t.strip() for t in topics_text.splitlines() if t.strip()]
        if module and topics:
            planner = st.session_state["planner"]
            plan = planner.plan_study(module, exam_date, project_deadline, topics, daily_hours)
            st.session_state["study_plan"] = plan
            save_state_to_file()
            st.success("✅ Timetable generated!")

    st.subheader("📋 Timetable")
    plan = st.session_state["study_plan"]
    if plan:
        for i, task in enumerate(plan):
            cols = st.columns([4, 1])
            with cols[0]:
                label = "⏸️ Break" if task.is_break else "📖 Study"
                st.write(f"{label} | {task.date} {task.start_time} | {task.duration_min}min | {task.topic}")
            with cols[1]:
                if not task.is_break:
                    key = f"study_{i}"
                    st.session_state[key] = st.session_state.get(key, task.completed)
                    st.checkbox("Done", key=key)

        st.info(st.session_state["planner"].generate_feedback_message(plan))
        st.subheader("🔔 Live Reminders")
        check_study_reminders()


def page_work():
    st.header("💼 Work Planner")
    
    st.subheader("Add Meetings")
    col1, col2, col3 = st.columns(3)
    with col1: meeting_title = st.text_input("Title")
    with col2: meeting_date = st.date_input("Date")
    with col3: meeting_time = st.time_input("Time")
    
    if st.button("Add Meeting") and meeting_title:
        st.session_state["temp_meetings"].append({
            "title": meeting_title, "date": meeting_date.isoformat(),
            "start_time": meeting_time.strftime("%H:%M"), "duration_min": 60
        })
        st.rerun()

    st.subheader("Generate Work Schedule")
    if st.button("Generate") and st.session_state["temp_meetings"]:
        planner = st.session_state["planner"]
        tasks = planner.plan_work(st.session_state["temp_meetings"], st.session_state["temp_deadlines"])
        st.session_state["work_tasks"] = tasks
        save_state_to_file()
        st.success("✅ Work schedule created!")

    st.subheader("Work Tasks")
    tasks = st.session_state["work_tasks"]
    if tasks:
        for i, task in enumerate(tasks):
            cols = st.columns([4, 1])
            with cols[0]: st.write(f"{task.date} {task.start_time} | {task.title}")
            with cols[1]:
                key = f"work_{i}"
                st.session_state[key] = st.session_state.get(key, task.completed)
                st.checkbox("Done", key=key)


def page_health():
    st.header("💚 Health Tracker")
    
    today = datetime.now().date().isoformat()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Goals")
        water_goal = st.number_input("Water (glasses)", value=8)
        exercise_goal = st.number_input("Exercise (min)", value=30)
    with col2:
        st.subheader("Actual")
        water_done = st.number_input("Water done", value=0)
        exercise_done = st.number_input("Exercise done", value=0)
    with col3:
        sleep_goal = st.number_input("Sleep goal (hrs)", value=8.0)
        sleep_done = st.number_input("Sleep done", value=0.0)
    
    if st.button("Save Health Data"):
        h = HealthDay(today, water_goal, water_done, exercise_goal, exercise_done, sleep_goal, sleep_done)
        st.session_state["health_days"][today] = h
        save_state_to_file()
        st.success("✅ Saved!")


def page_dashboard():
    st.header("📊 Analytics Dashboard")
    
    analytics = st.session_state["analytics"]
    if not analytics["history_dates"]:
        st.info("No data yet. Use other tabs first.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📚 Study Productivity")
        study_pct = [c/t*100 if t else 0 for c,t in zip(analytics["study_completed"], analytics["study_total"])]
        fig, ax = plt.subplots()
        ax.bar(range(len(study_pct)), study_pct, color="skyblue")
        ax.set_ylabel("Productivity %")
        st.pyplot(fig)
    
    with col2:
        st.subheader("💼 Work Performance")
        work_pct = [c/t*100 if t else 0 for c,t in zip(analytics["work_completed"], analytics["work_total"])]
        fig, ax = plt.subplots()
        ax.bar(range(len(work_pct)), work_pct, color="lightgreen")
        ax.set_ylabel("Performance %")
        st.pyplot(fig)


# ---------------------- MAIN APP ----------------------
def main():
    st.set_page_config(page_title="Study • Work • Health Notifier", layout="wide")
    
    init_session_state()
    if "loaded_from_file" not in st.session_state:
        load_state_from_file()
        st.session_state["loaded_from_file"] = True

    st.title("🚀 Study • Work • Health Notifier")
    
    page = st.sidebar.radio("Navigate", ["Study", "Work", "Health", "Dashboard"])
    
    if page == "Study":
        page_study()
    elif page == "Work":
        page_work()
    elif page == "Health":
        page_health()
    elif page == "Dashboard":
        page_dashboard()
    
    if st.sidebar.button("💾 Save All"):
        save_state_to_file()
        st.sidebar.success("Saved!")


if __name__ == "__main__":
    main()
