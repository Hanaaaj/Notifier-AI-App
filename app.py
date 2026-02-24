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
    date: str          # YYYY-MM-DD
    start_time: str    # HH:MM
    duration_min: int
    is_break: bool = False


@dataclass
class WorkTask:
    title: str
    date: str          # YYYY-MM-DD
    start_time: str    # HH:MM
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

    # --- STUDY PLANNING ---

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

        # Evenly distribute topics across days
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
                    )
                )

                available_minutes -= duration

                # Insert 20-min break after every 60 min of study
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
                        )
                    )
                    available_minutes -= 20
                    current_start = break_start + timedelta(minutes=20)
                else:
                    current_start = current_start + timedelta(minutes=duration)

            current_date += timedelta(days=1)

        return plan

    # --- WORK PLANNING ---

    def plan_work(
        self,
        meetings: List[Dict[str, Any]],
        deadlines: List[Dict[str, Any]],
        focus_block_minutes: int = 50,
    ) -> List[WorkTask]:
        tasks: List[WorkTask] = []

        # Focus blocks day before each deadline
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

        # Meetings
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

        # Overload prevention per day
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

    # --- FEEDBACK ---

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

        return (
            f"You have {days} days remaining and {len(topics)} topics. "
            f"Study about {topics_per_day} topics per day starting at {start_time}. "
            "Take a 20-minute break and hydrate every 10 minutes."
        )


# ---------------------- STORAGE ----------------------

DATA_FILE = "schedule_data.json"


def load_data() -> Dict[str, Any]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
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
            "completed_tasks": [],
            "total_tasks": [],
            "wellness_scores": [],
        }


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
            "completed_tasks": [],
            "total_tasks": [],
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


# ---------------------- STUDY PAGE ----------------------

def page_study():
    st.header("Study Planner")

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
        st.success("Study timetable generated and saved.")

    st.subheader("Generated Timetable")
    plan = st.session_state["study_plan"]
    if not plan:
        st.info("No study timetable yet. Generate one above.")
    else:
        for s in plan:
            label = "Break" if s.is_break else "Study"
            st.write(
                f"**{label}** | {s.date} {s.start_time} | {s.duration_min} min | "
                f"{s.module} - {s.topic}"
            )

        planner: RuleBasedPlanner = st.session_state["planner"]
        st.subheader("Smart Feedback")
        st.info(planner.generate_feedback_message(plan))

    st.subheader("JSON schedule (Study)")
    st.json([asdict(s) for s in plan])


# ---------------------- WORK PAGE ----------------------

def page_work():
    st.header("Work Planner")

    st.subheader("Add meetings")
    with st.form("meetings_form"):
        meeting_title = st.text_input("Meeting title")
        meeting_date = st.date_input("Meeting date")
        meeting_time = st.time_input("Meeting start time")
        meeting_duration = st.number_input("Meeting duration (minutes)", min_value=15, max_value=480, value=60, step=15)
        submitted_meeting = st.form_submit_button("Add meeting")

    if "temp_meetings" not in st.session_state:
        st.session_state["temp_meetings"] = []

    if submitted_meeting:
        st.session_state["temp_meetings"].append(
            {
                "title": meeting_title,
                "date": meeting_date.isoformat(),
                "start_time": meeting_time.strftime("%H:%M"),
                "duration_min": int(meeting_duration),
            }
        )
        st.success("Meeting added to temporary list.")

    st.write("Current meetings:")
    for m in st.session_state["temp_meetings"]:
        st.write(f"{m['date']} {m['start_time']} - {m['title']} ({m['duration_min']} min)")

    st.subheader("Add project deadlines")
    with st.form("deadlines_form"):
        deadline_title = st.text_input("Task/Project title")
        deadline_date = st.date_input("Deadline date")
        submitted_deadline = st.form_submit_button("Add deadline")

    if "temp_deadlines" not in st.session_state:
        st.session_state["temp_deadlines"] = []

    if submitted_deadline:
        st.session_state["temp_deadlines"].append(
            {
                "title": deadline_title,
                "date": deadline_date.isoformat(),
            }
        )
        st.success("Deadline added to temporary list.")

    st.write("Current deadlines:")
    for d in st.session_state["temp_deadlines"]:
        st.write(f"{d['date']} - {d['title']}")

    if st.button("Generate Work Schedule"):
        planner: RuleBasedPlanner = st.session_state["planner"]
        tasks = planner.plan_work(
            meetings=st.session_state["temp_meetings"],
            deadlines=st.session_state["temp_deadlines"],
        )
        st.session_state["work_tasks"] = tasks
        save_state_to_file()
        st.success("Work schedule generated and saved.")

    st.subheader("Work tasks")
    tasks = st.session_state["work_tasks"]
    if not tasks:
        st.info("No work tasks yet. Add meetings/deadlines and generate.")
    else:
        for idx, t in enumerate(tasks):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"{t.date} {t.start_time} | {t.title} | {t.duration_min} min | Priority: {t.priority}")
            with col2:
                st.write("Completed:" if t.completed else "Pending")
            with col3:
                if st.button("Toggle", key=f"toggle_{idx}"):
                    t.completed = not t.completed
                    st.session_state["work_tasks"][idx] = t
                    save_state_to_file()

    st.subheader("JSON schedule (Work)")
    st.json([asdict(w) for w in st.session_state["work_tasks"]])


# ---------------------- HEALTH PAGE ----------------------

def compute_wellness_score(h: HealthDay) -> float:
    if h.water_goal_glasses == 0 or h.exercise_minutes_target == 0 or h.sleep_hours_target == 0:
        return 0.0

    water_score = min(1.0, h.water_taken_glasses / h.water_goal_glasses)
    exercise_score = min(1.0, h.exercise_minutes_done / h.exercise_minutes_target)
    sleep_score = min(1.0, h.sleep_hours_done / h.sleep_hours_target)

    return round((water_score + exercise_score + sleep_score) / 3 * 100, 1)


def page_health():
    st.header("Health Tracker")

    today = datetime.now().date().isoformat()
    health_days: Dict[str, HealthDay] = st.session_state["health_days"]

    st.subheader("Set goals for today")
    water_goal = st.number_input("Hydration goal (glasses/day)", min_value=1, max_value=30, value=8)
    exercise_goal = st.number_input("Exercise time target (minutes)", min_value=0, max_value=300, value=30)
    sleep_goal = st.number_input("Sleep time target (hours)", min_value=0.0, max_value=14.0, value=8.0, step=0.5)

    st.subheader("Track today")
    water_taken = st.number_input("Water taken (glasses)", min_value=0, max_value=30, value=0)
    exercise_done = st.number_input("Exercise done (minutes)", min_value=0, max_value=300, value=0)
    sleep_done = st.number_input("Sleep done (hours)", min_value=0.0, max_value=14.0, value=0.0, step=0.5)

    if st.button("Save health data for today"):
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

        # update analytics
        analytics = st.session_state["analytics"]
        analytics["history_dates"].append(today)
        # use work tasks for task completion stats
        total_tasks = len(st.session_state["work_tasks"])
        completed = len([t for t in st.session_state["work_tasks"] if t.completed])
        analytics["completed_tasks"].append(completed)
        analytics["total_tasks"].append(total_tasks)
        analytics["wellness_scores"].append(compute_wellness_score(h))
        st.session_state["analytics"] = analytics

        save_state_to_file()
        st.success("Health data saved.")

    if today in health_days:
        st.subheader("Today summary")
        h = health_days[today]
        st.write(f"Water: {h.water_taken_glasses}/{h.water_goal_glasses} glasses")
        st.write(f"Exercise: {h.exercise_minutes_done}/{h.exercise_minutes_target} minutes")
        st.write(f"Sleep: {h.sleep_hours_done}/{h.sleep_hours_target} hours")
        st.write(f"Daily wellness score: {compute_wellness_score(h)} / 100")


# ---------------------- DASHBOARD PAGE ----------------------

def page_dashboard():
    st.header("Analytics Dashboard")

    analytics = st.session_state["analytics"]
    dates = analytics["history_dates"]
    completed = analytics["completed_tasks"]
    total = analytics["total_tasks"]
    wellness = analytics["wellness_scores"]

    if not dates:
        st.info("No analytics data yet. Save some health data first.")
        return

    # Completed vs missed tasks bar chart
    st.subheader("Completed vs Missed Tasks")
    missed = [t - c for t, c in zip(total, completed)]

    fig1, ax1 = plt.subplots()
    x = range(len(dates))
    ax1.bar(x, completed, label="Completed", color="green")
    ax1.bar(x, missed, bottom=completed, label="Missed", color="red")
    ax1.set_xticks(x)
    ax1.set_xticklabels(dates, rotation=45, ha="right")
    ax1.set_ylabel("Number of tasks")
    ax1.legend()
    st.pyplot(fig1)

    # Productivity trend (line chart)
    st.subheader("Productivity Trend")
    productivity = [c / t * 100 if t > 0 else 0 for c, t in zip(completed, total)]

    fig2, ax2 = plt.subplots()
    ax2.plot(dates, productivity, marker="o")
    ax2.set_ylabel("Productivity (%)")
    ax2.set_xticklabels(dates, rotation=45, ha="right")
    st.pyplot(fig2)

    # Hydration tracking: use water percentage
    st.subheader("Hydration Tracking")
    health_days: Dict[str, HealthDay] = st.session_state["health_days"]
    hydration_pct = []
    hyd_dates = []
    for d in dates:
        if d in health_days:
            h = health_days[d]
            if h.water_goal_glasses > 0:
                hydration_pct.append(h.water_taken_glasses / h.water_goal_glasses * 100)
            else:
                hydration_pct.append(0)
            hyd_dates.append(d)

    if hyd_dates:
        fig3, ax3 = plt.subplots()
        ax3.plot(hyd_dates, hydration_pct, marker="o", color="blue")
        ax3.set_ylabel("Hydration (%)")
        ax3.set_xticklabels(hyd_dates, rotation=45, ha="right")
        st.pyplot(fig3)
    else:
        st.write("No hydration data yet.")

    # Wellness score visualization
    st.subheader("Wellness Score")
    fig4, ax4 = plt.subplots()
    ax4.plot(dates, wellness, marker="o", color="purple")
    ax4.set_ylabel("Wellness score (0-100)")
    ax4.set_xticklabels(dates, rotation=45, ha="right")
    st.pyplot(fig4)


# ---------------------- MAIN APP ----------------------

def main():
    st.set_page_config(page_title="Study • Work • Health Notifier", layout="wide")

    init_session_state()

    # Load from file once per session
    if "loaded_from_file" not in st.session_state:
        load_state_from_file()
        st.session_state["loaded_from_file"] = True

    st.title("Study • Work • Health Notifier")

    page = st.sidebar.radio("Navigate", ["Study", "Work", "Health", "Dashboard"])

    st.sidebar.markdown("### Quick Info")
    st.sidebar.write(
        "This app generates smart study/work schedules, tracks health, and shows reminders "
        "while you have the page open."
    )

    if page == "Study":
        page_study()
    elif page == "Work":
        page_work()
    elif page == "Health":
        page_health()
    elif page == "Dashboard":
        page_dashboard()

    st.sidebar.markdown("---")
    if st.sidebar.button("Save now"):
        save_state_to_file()
        st.sidebar.success("Data saved to JSON.")


if __name__ == "__main__":
    main()
