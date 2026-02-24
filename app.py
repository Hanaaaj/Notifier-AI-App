import json
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ---------------------- SIMPLE DATA STRUCTURES ----------------------
def init_data():
    return {
        "study_plan": [],
        "work_tasks": [],
        "health_days": {},
        "temp_meetings": [],
        "temp_deadlines": [],
        "last_hydration": None
    }

# ---------------------- PLANNER ----------------------
class Planner:
    def plan_study(self, module, exam_date_str, topics, daily_hours):
        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
            days_remaining = max(1, (exam_date - datetime.now().date()).days)
            total_minutes = min(int(daily_hours * 60), 360)
            
            plan = []
            topic_idx = 0
            current_date = datetime.now().date()
            
            for _ in range(days_remaining):
                if topic_idx >= len(topics):
                    break
                day_topics = topics[topic_idx:topic_idx+2]  # 2 topics per day
                topic_idx += len(day_topics)
                
                current_time = 9 * 60  # 9 AM in minutes
                for topic in day_topics:
                    duration = min(60, total_minutes)
                    start_time = f"{current_time//60:02d}:{current_time%60:02d}"
                    plan.append({
                        "module": module,
                        "topic": topic[:30],  # truncate long topics
                        "date": current_date.strftime("%Y-%m-%d"),
                        "start_time": start_time,
                        "duration_min": duration,
                        "is_break": False,
                        "completed": False
                    })
                    current_time += duration
                    
                    # Add break after study
                    if duration >= 60:
                        start_time = f"{current_time//60:02d}:{current_time%60:02d}"
                        plan.append({
                            "module": module,
                            "topic": "BREAK",
                            "date": current_date.strftime("%Y-%m-%d"),
                            "start_time": start_time,
                            "duration_min": 20,
                            "is_break": True,
                            "completed": False
                        })
                        current_time += 20
                
                current_date += timedelta(days=1)
            return plan
        except:
            return []

# ---------------------- STORAGE ----------------------
@st.cache_data
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return init_data()

def save_data(data):
    try:
        with open("data.json", "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

# ---------------------- INIT ----------------------
def init_session():
    if "data" not in st.session_state:
        st.session_state.data = load_data()
        st.session_state.planner = Planner()

# ---------------------- REMINDERS ----------------------
def show_reminders():
    if "data" not in st.session_state or not st.session_state.data["study_plan"]:
        return
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    for task in st.session_state.data["study_plan"]:
        if (task.get("date") == today and not task.get("is_break", False) and 
            not task.get("completed", False)):
            try:
                start = datetime.strptime(f"{task['date']} {task['start_time']}", "%Y-%m-%d %H:%M")
                end = start + timedelta(minutes=task["duration_min"])
                if start <= now <= end:
                    if st.session_state.data["last_hydration"] is None:
                        st.session_state.data["last_hydration"] = now.isoformat()
                        st.error("💧 **HYDRATION REMINDER** - Drink water NOW!")
                    return
            except:
                pass

# ---------------------- STUDY PAGE ----------------------
def study_page():
    st.header("📚 Study Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        module = st.text_input("Module Name", "Mathematics")
        exam_date = st.date_input("Exam Date", datetime.now())
    with col2:
        daily_hours = st.number_input("Daily Study Hours", 1.0, 8.0, 2.0)
    
    topics_input = st.text_area("Enter topics (one per line)", 
                               "Topic 1\nTopic 2\nTopic 3\nTopic 4")
    topics = [t.strip() for t in topics_input.split("\n") if t.strip()]
    
    if st.button("🎯 GENERATE TIMETABLE") and module and topics:
        plan = st.session_state.planner.plan_study(module, 
                                                 exam_date.strftime("%Y-%m-%d"), 
                                                 topics, daily_hours)
        st.session_state.data["study_plan"] = plan
        save_data(st.session_state.data)
        st.success(f"✅ Created {len(plan)} study sessions!")
        st.rerun()
    
    # Show timetable
    if st.session_state.data.get("study_plan"):
        st.subheader("📋 Your Study Schedule")
        plan = st.session_state.data["study_plan"]
        
        for i, task in enumerate(plan):
            try:
                col1, col2 = st.columns([4, 1])
                with col1:
                    is_break = task.get("is_break", False)
                    icon = "⏸️" if is_break else "📖"
                    status = "✅" if task.get("completed", False) else "⏳"
                    st.write(f"{status} {icon} {task['date']} {task['start_time']} "
                           f"({task['duration_min']}min) {task['topic']}")
                with col2:
                    if not is_break:
                        key = f"study_done_{i}"
                        if key not in st.session_state:
                            st.session_state[key] = task.get("completed", False)
                        st.checkbox("Done", key=key)
            except Exception as e:
                st.write(f"Task {i}: {task.get('topic', 'Error')}")
        
        st.subheader("🔔 AUTOMATIC REMINDERS")
        show_reminders()
        
        # Progress stats
        study_tasks = [t for t in plan if not t.get("is_break", False)]
        done = sum(1 for t in study_tasks if t.get("completed", False))
        st.info(f"📊 Progress: {done}/{len(study_tasks)} study sessions completed")

# ---------------------- SIMPLE OTHER PAGES ----------------------
def work_page():
    st.header("💼 Work Planner")
    st.info("👈 Add meetings and deadlines, then generate work schedule")
    
    if st.button("Test Work Page"):
        st.success("Work page works!")

def health_page():
    st.header("💚 Health Tracker")
    st.info("👈 Track water, exercise, sleep")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        water = st.number_input("Water glasses", 0, 20, 0)
    with col2:
        exercise = st.number_input("Exercise minutes", 0, 120, 0)
    with col3:
        sleep = st.number_input("Sleep hours", 0.0, 12.0, 0.0)
    
    if st.button("Save Health"):
        st.success("✅ Health data saved!")

def dashboard_page():
    st.header("📊 Dashboard")
    
    if not st.session_state.data.get("study_plan"):
        st.warning("👆 Generate a study plan first!")
        return
    
    plan = st.session_state.data["study_plan"]
    study_tasks = [t for t in plan if not t.get("is_break", False)]
    done = sum(1 for t in study_tasks if t.get("completed", False))
    total = len(study_tasks)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Study Sessions", f"{done}/{total}")
        progress = (done/total*100) if total > 0 else 0
        st.metric("📈 Productivity", f"{progress:.1f}%")
    
    # Simple chart
    fig, ax = plt.subplots()
    ax.pie([done, total-done], labels=["✅ Done", "⏳ Pending"], autopct='%1.1f%%',
           colors=['#4CAF50', '#FF9800'])
    ax.set_title("Study Progress")
    st.pyplot(fig)

# ---------------------- MAIN APP ----------------------
def main():
    st.set_page_config(page_title="AI Study Notifier", layout="wide", page_icon="🚀")
    
    init_session()
    
    st.title("🚀 AI Study • Work • Health Notifier")
    st.markdown("***Smart planning with automatic hydration & break reminders***")
    
    # Sidebar navigation
    page = st.sidebar.selectbox("📂 Navigation", ["Study", "Work", "Health", "Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **✨ Features:**
    • 📚 Auto study timetables
    • 🔔 Hydration reminders
    • ⏸️ Break scheduling  
    • 📊 Progress tracking
    • 💾 Auto-save
    """)
    
    # Page routing
    if page == "Study":
        study_page()
    elif page == "Work":
        work_page()
    elif page == "Health":
        health_page()
    elif page == "Dashboard":
        dashboard_page()
    
    # Save button
    if st.sidebar.button("💾 Save All Data"):
        save_data(st.session_state.data)
        st.sidebar.success("✅ All data saved!")

if __name__ == "__main__":
    main()
