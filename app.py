import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any
import copy

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
    is_break: bool = False
    completed: bool = False


@dataclass
class WorkTask:
    title: str
    date: str
    start_time: str
    duration_min: int
    priority: str
    completed: bool = False


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

    def plan_study(
        self,
        module_name: str,
        exam_date: datetime,
        project_deadline: datetime,
        topics: List[str],
        daily_hours: float,
        start_hour: int = 9,
    ) -> List[StudyTask]:
        days_remaining = (exam_date.date() - datetime.now().date()).days
        if days_remaining <= 0:
            days_remaining = 1

        total_minutes_per_day = int(daily_hours * 60)
        total_minutes_per_day = min(total_minutes_per_day, self.max_study_minutes_per_day)

        topics_per_day = max(1, len(topics) // days_remaining)
        if topics_per_day * days_remaining < len(topics):
            topics_per_day += 1

        plan: List[StudyTask] = []
        topic_index = 0
        current_date = datetime.now().date()

        while topic_index < len(topics):
            day_topics = topics[topic_index: topic_index + topics_per_day]
            topic_index += len(day_topics)

            available_minutes = total_minutes_per_day
            current_start = datetime.combine(current_date, datetime.min.time()).replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )

            per_topic_minutes = max(30, available_minutes // max(1, len(day_topics)))

            for topic in day_topics:
                if available_minutes <= 0:
                    break

                duration = min(per_topic_minutes, available_minutes)
                plan.append(
                    StudyTask(
                        module=module_name,
                        topic=topic,
                        date=current_date.isoformat(),
                        start_time=current_start.strftime("%H:%M"),
                        duration_min=duration,
                        is_break=False,
                        completed=False,
                    )
                )

                available_minutes -= duration

                if available_minutes > 0 and duration >= 60:
                    break_start = current_start + timedelta(minutes=duration)
                    plan.append(
                        StudyTask(
                            module=module_name,
                            topic="Break",
                            date=current_date.isoformat(),
                            start_time=break_start.strftime("%H:%M"),
                            duration_min=20,
                            is_break=True,
                            completed=False,
                        )
                    )
                    available_minutes -= 20
                    current_start = break_start + timedelta(minutes=20)
                else:
                    current_start = current_start + timedelta(minutes=duration)

            current_date += timedelta(days=1)

        return plan

    def plan_work(
        self,
        meetings: List[Dict[str, Any]],
        deadlines: List[Dict[str, Any]],
        focus_block_minutes: int = 50,
    ) -> List[WorkTask]:
        tasks: List[WorkTask] = []

        for d in deadlines:
            deadline_date = datetime.strptime(d["date"], "%Y-%m-%d").date()
            day_before = (deadline_date - timedelta(days=1)).isoformat()
            tasks.append(
                WorkTask(
                    title=f"Focus: {d['title']}",
                    date=day_before,
                    start_time="14:00",
                    duration_min=focus_block_minutes,
                    priority="High",
                    completed=False,
                )
            )

        for m in meetings:
            tasks.append(
                WorkTask(
                    title=f"Meeting: {m['title']}",
                    date=m["date"],
                    start_time=m["start_time"],
                    duration_min=m.get("duration_min", 60),
                    priority="Medium",
                    completed=False,
                )
            )

        tasks_by_date: Dict[str, List[WorkTask]] = {}
        for t in tasks:
            tasks_by_date.setdefault(t.date, []).append(t)

        balanced: List[WorkTask] = []
        for date, day_tasks in tasks_by_date.items():
            used = 0
            for t in day_tasks:
                if used + t.duration_min > self.max_work_minutes_per_day:
                    allowed = max(20, self.max_work_minutes_per_day - used)
                    t.duration_min = allowed
                used += t.duration_min
                balanced.append(t)

        return balanced

    def generate_feedback_message(self, study_plan: List[StudyTask]) -> str:
        if not study_plan:
            return "No study sessions scheduled yet. Add topics to generate a plan."

        first = study_plan[0]
        last = study_plan[-1]
        days = (datetime.strptime(last.date, "%Y-%m-%d").date() -
                datetime.strptime(first.date, "%Y-%m-%d").date()).days + 1

        topics = [t for t in study_plan if not t.is_break]
        if days <= 0:
            days = 1
        topics_per_day = max(1, len(topics) // days)
        start_time = first.start_time

        completed = len([t for t in topics if t.completed])
        return (
            f"You have {days} days remaining and {len(topics)} topics. "
            f"Study about {topics_per_day} topics per day starting at {start_time}. "
            f"({completed}/{len(topics)} topics completed)"
        )


# ---------------------- STORAGE ----------------------

DATA_FILE = "schedule_data.json"


def load_data() -> Dict[str, Any]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data: Dict[str, Any]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------- SESSION HELPERS ----------------------

def init_session_state():
    if "planner" not in st.session_state:
        st.session_state["planner"] = RuleBasedPlanner()
    if "study_plan" not in st.session_state:
        st.session_state["study_plan"] = []
    if "work_tasks" not in st.session_state:
        st.session_state["work_tasks"] = []
    if "health_days" not in st.session_state:
        st.session_state["health_days"] = {}
    if "analytics" not in st.session_state:
        st.session_state["analytics"] = {
            "history_dates": [],
            "study_completed": [],
            "study_total": [],
            "work_completed": [],
            "work_total": [],
            "wellness_scores": [],
        }
    if "last_hydration_check" not in st.session_state:
        st.session_state["last_hydration_check"] = None
    if "study_minutes_in_current_block" not in st.session_state:
        st.session_state["study_minutes_in_current_block"] = 0
    if "temp_meetings" not in st.session_state:
        st.session_state["temp_meetings"] = []
    if "temp_deadlines" not in st.session_state:
        st.session_state["temp_deadlines"] = []


def load_state_from_file():
    data = load_data()
    planner = RuleBasedPlanner()
    study_plan = []
    work_tasks = []
    health_days = {}

    for item in data.get("study_plan", []):
        study_plan.append(StudyTask(**item))
    for item in data.get("work_tasks", []):
        work_tasks.append(WorkTask(**item))
    for date, hd in data.get("health_days", {}).items():
        health_days[date] = HealthDay(**hd)

    st.session_state["planner"] = planner
    st.session_state["study_plan"] = study_plan
    st.session_state["work_tasks"] = work_tasks
    st.session_state["health_days"] = health_days
    st.session_state["analytics"] = data.get(
        "analytics",
        {
            "history_dates": [],
            "study_completed": [],
            "study_total": [],
            "work_completed": [],
            "work_total": [],
            "wellness_scores": [],
        },
    )


def save_state_to_file():
    study_plan = [asdict(s) for s in st.session_state["study_plan"]]
    work_tasks = [asdict(w) for w in st.session_state["work_tasks"]]
    health_days = {d: asdict(h) for d, h in st.session_state["health_days"].items()}
    analytics = st.session_state["analytics"]

    data = {
        "study_plan": study_plan,
        "work_tasks": work_tasks,
        "health_days": health_days,
        "analytics": analytics,
    }
    save_data(data)


# ---------------------- STUDY REMINDERS ----------------------

def check_study_reminders():
    plan: List[StudyTask] = st.session_state["study_plan"]
    if not plan:
        return

    now = datetime.now()
    today_str = now.date().isoformat()

    current_block = None
    for s in plan:
        if s.date != today_str or s.is_break:
            continue
        start = datetime.strptime(f"{s.date} {s.start_time}", "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=s.duration_min)
        if start <= now <= end:
            current_block = (s, start, end)
            break

    if current_block is None:
        st.session_state["study_minutes_in_current_block"] = 0
        return

    s, start, end = current_block
    minutes_since_start = int((now - start).total_seconds() // 60)
    st.session_state["study_minutes_in_current_block"] = minutes_since_start

    last = st.session_state["last_hydration_check"]
    if last is None:
        st.session_state["last_hydration_check"] = now
        st.info("💧 Hydration reminder: drink water. (Auto)")
    else:
        diff_min = (now - last).total_seconds() / 60
        if diff_min >= 10:
            st.session_state["last_hydration_check"] = now
            st.warning("💧 Hydration reminder: drink water. (Every 10 minutes)")

    if minutes_since_start >= 60:
        st.error("⏸️ Break reminder: Take a 20-minute break now!")


# ---------------------- STUDY PAGE ----------------------

def page_study():
    st.header("📚 Study Planner")

    module = st.text_input("Module name")
    exam_date = st.date_input("Exam date")
    project_deadline = st.date_input("Project deadline")
    topics_text = st.text_area(
        "Topics list (one per line)",
        help="Enter each topic on a new line.",
    )
    daily_hours = st.number_input("Daily available study hours", min_value=0.5, max_value=12.0, value=2.0, step=0.5)

    if st.button("Generate Study Timetable"):
        topics = [t.strip() for t in topics_text.splitlines() if t.strip()]
        if not module or not topics:
            st.error("Please enter module name and at least one topic.")
            return

        planner: RuleBasedPlanner = st.session_state["planner"]
        plan = planner.plan_study(
            module_name=module,
            exam_date=datetime.combine(exam_date, datetime.min.time()),
            project_deadline=datetime.combine(project_deadline, datetime.min.time()),
            topics=topics,
            daily_hours=daily_hours,
        )
        st.session_state["study_plan"] = plan
        save_state_to_file()
        st.success("✅ Study timetable generated and saved.")

    st.subheader("📋 Generated Timetable")
    plan = st.session_state["study_plan"]
    if not plan:
        st.info("No study timetable yet. Generate one above.")
    else:
        for idx, s in enumerate(plan):
            cols = st.columns([4, 1])
            with cols[0]:
                label = "⏸️ Break" if s.is_break else "📖 Study"
                status = "✅" if s.completed else "⏳"
                st.write(
                    f"{status} {label} | {s.date} {s.start_time} | {s.duration_min} min | "
                    f"{s.module} - {s.topic}"
                )
            with cols[1]:
                if not s.is_break:
                    # FIXED: Use session_state directly for checkboxes
                    key = f"study_done_{idx}"
                    if key not in st.session_state:
                        st.session_state[key] = s.completed
                    
                    done = st.checkbox("Done", value=st.session_state[key], key=key)
                    if done != s.completed:
                        # Update the actual task
                        plan[idx].completed = done
                        st.session_state["study_plan"] = plan
                        save_state_to_file()

        planner: RuleBasedPlanner = st.session_state["planner"]
        st.subheader("🤖 Smart Feedback")
        st.info(planner.generate_feedback_message(plan))

        st.subheader("🔔 Live Reminders (while page is open)")
        check_study_reminders()


# ---------------------- WORK PAGE ----------------------

def page_work():
    st.header("💼 Work Planner")

    st.subheader("📅 Add meetings")
    with st.form("meetings_form"):
        meeting_title = st.text_input("Meeting title")
        meeting_date = st.date_input("Meeting date")
        meeting_time = st.time_input("Meeting start time")
        meeting_duration = st.number_input("Meeting duration (minutes)", min_value=15, max_value=480, value=60, step=15)
        submitted_meeting = st.form_submit_button("Add meeting")

    if submitted_meeting:
        st.session_state["temp_meetings"].append(
            {
                "title": meeting_title,
                "date": meeting_date.isoformat(),
                "start_time": meeting_time.strftime("%H:%M"),
                "duration_min": int(meeting_duration),
            }
        )
        st.success("✅ Meeting added.")

    st.write("Current meetings:")
    for m in st.session_state["temp_meetings"]:
        st.write(f"📅 {m['date']} {m['start_time']} - {m['title']} ({m['duration_min']} min)")

    st.subheader("⏰ Add project deadlines")
    with st.form("deadlines_form"):
        deadline_title = st.text_input("Task/Project title")
        deadline_date = st.date_input("Deadline date")
        submitted_deadline = st.form_submit_button("Add deadline")

    if submitted_deadline:
        st.session_state["temp_deadlines"].append(
            {
                "title": deadline_title,
                "date": deadline_date.isoformat(),
            }
        )
        st.success("✅ Deadline added.")

    st.write("Current deadlines:")
    for d in st.session_state["temp_deadlines"]:
        st.write(f"⏰ {d['date']} - {d['title']}")

    if st.button("Generate Work Schedule"):
        planner: RuleBasedPlanner = st.session_state["planner"]
        tasks = planner.plan_work(
            meetings=st.session_state["temp_meetings"],
            deadlines=st.session_state["temp_deadlines"],
        )
        st.session_state["work_tasks"] = tasks
        save_state_to_file()
        st.success("✅ Work schedule generated.")

    st.subheader("📋 Work tasks")
    tasks = st.session_state["work_tasks"]
    if not tasks:
        st.info("No work tasks yet. Add meetings/deadlines above.")
    else:
        for idx, t in enumerate(tasks):
            cols = st.columns([4, 1])
            with cols[0]:
                status = "✅" if t.completed else "⏳"
                st.write(f"{status} {t.date} {t.start_time} | {t.title} | {t.duration_min} min | {t.priority}")
            with cols[1]:
                key = f"work_done_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = t.completed
                
                done = st.checkbox("Done", value=st.session_state[key], key=key)
                if done != t.completed:
                    tasks[idx].completed = done
                    st.session_state["work_tasks"] = tasks
                    save_state_to_file()


# ---------------------- HEALTH PAGE ----------------------

def compute_wellness_score(h: HealthDay) -> float:
    if h.water_goal_glasses == 0 or h.exercise_minutes_target == 0 or h.sleep_hours_target == 0:
        return 0.0

    water_score = min(1.0, h.water_taken_glasses / h.water_goal_glasses)
    exercise_score = min(1.0, h.exercise_minutes_done / h.exercise_minutes_target)
    sleep_score = min(1.0, h.sleep_hours_done / h.sleep_hours_target)

    return round((water_score + exercise_score + sleep_score) / 3 * 100, 1)


def update_analytics_for_today():
    today = datetime.now().date().isoformat()
    analytics = st.session_state["analytics"]

    study_today = [s for s in st.session_state["study_plan"] if s.date == today and not s.is_break]
    work_today = [w for w in st.session_state["work_tasks"] if w.date == today]

    study_total = len(study_today)
    study_completed = len([s for s in study_today if s.completed])
    work_total = len(work_today)
    work_completed = len([w for w in work_today if w.completed])

    health_days: Dict[str, HealthDay] = st.session_state["health_days"]
    wellness = compute_wellness_score(health_days.get(today, HealthDay(today, 0, 0, 0, 0, 0, 0)))

    if analytics["history_dates"] and analytics["history_dates"][-1] == today:
        analytics["study_total"][-1] = study_total
        analytics["study_completed"][-1] = study_completed
        analytics["work_total"][-1] = work_total
        analytics["work_completed"][-1] = work_completed
        analytics["wellness_scores"][-1] = wellness
    else:
        analytics["history_dates"].append(today)
        analytics["study_total"].append(study_total)
        analytics["study_completed"].append(study_completed)
        analytics["work_total"].append(work_total)
        analytics["work_completed"].append(work_completed)
        analytics["wellness_scores"].append(wellness)

    st.session_state["analytics"] = analytics


def page_health():
    st.header("💚 Health Tracker")

    today = datetime.now().date().isoformat()
    health_days: Dict[str, HealthDay] = st.session_state["health_days"]

    st.subheader("🎯 Set goals for today")
    col1, col2, col3 = st.columns(3)
    with col1:
        water_goal = st.number_input("💧 Water (glasses)", min_value=1, max_value=30, value=8)
    with col2:
        exercise_goal = st.number_input("🏃 Exercise (min)", min_value=0, max_value=300, value=30)
    with col3:
        sleep_goal = st.number_input("😴 Sleep (hours)", min_value=0.0, max_value=14.0, value=8.0, step=0.5)

    st.subheader("📊 Track today")
    col1, col2, col3 = st.columns(3)
    with col1:
        water_taken = st.number_input("💧 Taken", min_value=0, max_value=30, value=0)
    with col2:
        exercise_done = st.number_input("🏃 Done", min_value=0, max_value=300, value=0)
    with col3:
        sleep_done = st.number_input("😴 Done", min_value=0.0, max_value=14.0, value=0.0, step=0.5)

    if st.button("💾 Save health data"):
        h = HealthDay(
            date=today,
            water_goal_glasses=int(water_goal),
            water_taken_glasses=int(water_taken),
            exercise_minutes_target=int(exercise_goal),
            exercise_minutes_done=int(exercise_done),
            sleep_hours_target=float(sleep_goal),
            sleep_hours_done=float(sleep_done),
        )
        health_days[today] = h
        st.session_state["health_days"] = health_days

        update_analytics_for_today()
        save_state_to_file()
        st.success("✅ Health data saved!")

    if today in health_days:
        st.subheader("📈 Today summary")
        h = health_days[today]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💧 Water", f"{h.water_taken_glasses}/{h.water_goal_glasses}")
        with col2:
            st.metric("🏃 Exercise", f"{h.exercise_minutes_done}/{h.exercise_minutes_target}")
        with col3:
            st.metric("😴 Sleep", f"{h.sleep_hours_done}/{h.sleep_hours_target}")
        st.metric("⭐ Wellness", f"{compute_wellness_score(h)}/100")

    update_analytics_for_today()
    save_state_to_file()


# ---------------------- DASHBOARD PAGE ----------------------

def page_dashboard():
    st.header("📊 Analytics Dashboard")

    analytics = st.session_state["analytics"]
    dates = analytics["history_dates"]
    study_completed = analytics["study_completed"]
    study_total = analytics["study_total"]
    work_completed = analytics["work_completed"]
    work_total = analytics["work_total"]
    wellness = analytics["wellness_scores"]

    if not dates:
        st.info("📈 No data yet. Use Study/Work/Health tabs first.")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Study Productivity")
        study_prod = [c / t * 100 if t > 0 else 0 for c, t in zip(study_completed, study_total)]
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        x = range(len(dates))
        ax1.bar(x, study_prod, color="skyblue")
        ax1.set_xticks(x)
        ax1.set_xticklabels(dates, rotation=45, ha="right")
        ax1.set_ylabel("Study Productivity (%)")
        ax1.set_title("Study Performance Over Time")
        st.pyplot(fig1)

    with col2:
        st.subheader("💼 Work Performance")
        work_perf = [c / t * 100 if t > 0 else 0 for c, t in zip(work_completed, work_total)]
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        x2 = range(len(dates))
        ax2.bar(x2, work_perf, color="lightgreen")
        ax2.set_xticks(x2)
        ax2.set_xticklabels(dates, rotation=45, ha="right")
        ax2.set_ylabel("Work Performance (%)")
        ax2.set_title("Work Performance Over Time")
        st.pyplot(fig2)

    st.subheader("💚 Wellness Score")
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    ax3.plot(dates, wellness, marker="o", linewidth=2, markersize=8, color="purple")
    ax3.fill_between(dates, wellness, alpha=0.3, color="purple")
    ax3.set_xticklabels(dates, rotation=45, ha="right")
    ax3.set_ylabel("Wellness Score (0-100)")
    ax3.set_title("Daily Wellness Trend")
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)


# ---------------------- MAIN APP ----------------------

def main():
    st.set_page_config(
        page_title="Study • Work • Health Notifier", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    if "loaded_from_file" not in st.session_state:
        load_state_from_file()
        st.session_state["loaded_from_file"] = True

    st.title("🚀 Study • Work • Health Notifier")

    page = st.sidebar.radio("📂 Navigate", ["Study", "Work", "Health", "Dashboard"])

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ **How it works**")
    st.sidebar.markdown("""
    - 📚 **Study**: Auto-generates timetable with breaks  
    - 💼 **Work**: Plans meetings + focus blocks  
    - 💚 **Health**: Tracks water, exercise, sleep  
    - 📊 **Dashboard**: Shows productivity & performance  
    - 🔔 **Reminders**: Auto hydration + break alerts  
    """)

    if page == "Study":
        page_study()
    elif page == "Work":
        page_work()
    elif page == "Health":
        page_health()
    elif page == "Dashboard":
        page_dashboard()

    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Save All Data"):
        save_state_to_file()
        st.sidebar.success("✅ All data saved!")


if __name__ == "__main__":
    main()
