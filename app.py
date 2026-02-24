import streamlit as st
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ========================================
# SIMPLE STORAGE - NO CLASSES, NO ERRORS
# ========================================
def load_data():
    try:
        with open("app_data.json", "r") as f:
            return json.load(f)
    except:
        return {
            "study_plan": [],
            "work_tasks": [],
            "health_data": {},
            "last_hydration": None
        }

def save_data(data):
    try:
        with open("app_data.json", "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

# Initialize session
if "data" not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.show_reminder = False

# Save function
def update_and_save(key, value):
    st.session_state.data[key] = value
    save_data(st.session_state.data)

# ========================================
# STUDY PLANNER
# ========================================
def study_page():
    st.header("📚 AI Study Planner")
    
    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        module = st.text_input("Module Name", "Mathematics")
        exam_date = st.date_input("Exam Date", datetime.now())
    with col2:
        hours = st.number_input("Daily Hours", 1.0, 8.0, 2.0)
    
    topics = st.text_area("Topics (one per line)", 
                         "Algebra\nGeometry\nCalculus\nStatistics").split("\n")
    topics = [t.strip() for t in topics if t.strip()]
    
    # Generate button
    if st.button("🎯 GENERATE TIMETABLE", type="primary"):
        plan = []
        days = 7  # 1 week plan
        topics_per_day = max(1, len(topics) // days)
        
        current_date = datetime.now().date()
        for day in range(days):
            day_topics = topics[day*topics_per_day:(day+1)*topics_per_day]
            if day_topics:
                # Morning study
                start_hour = 9
                for topic in day_topics:
                    plan.append({
                        "module": module,
                        "topic": topic[:30],
                        "date": current_date.strftime("%Y-%m-%d"),
                        "start_time": f"{start_hour:02d}:00",
                        "duration": 60,
                        "type": "study",
                        "completed": False
                    })
                    # Break after study
                    plan.append({
                        "module": module,
                        "topic": "BREAK",
                        "date": current_date.strftime("%Y-%m-%d"),
                        "start_time": f"{start_hour+1:02d}:00",
                        "duration": 20,
                        "type": "break",
                        "completed": False
                    })
                    start_hour += 2
        
        update_and_save("study_plan", plan)
        st.success(f"✅ Generated {len([t for t in plan if t['type']=='study'])} study sessions!")
        st.rerun()
    
    # Show schedule
    if st.session_state.data.get("study_plan"):
        st.subheader("📋 Your Schedule")
        plan = st.session_state.data["study_plan"]
        
        study_count = 0
        for i, task in enumerate(plan):
            col1, col2 = st.columns([5, 1])
            with col1:
                icon = "⏸️" if task["type"] == "break" else "📖"
                status = "✅" if task.get("completed", False) else "⏳"
                st.write(f"{status} {icon} {task['date']} {task['start_time']} "
                        f"({task['duration']}min) {task['topic']}")
            
            # Done checkbox for study tasks only
            if task["type"] == "study":
                key = f"study_{i}"
                if key not in st.session_state:
                    st.session_state[key] = task.get("completed", False)
                if st.checkbox("Done", key=key, label_visibility="collapsed"):
                    if not st.session_state[key]:
                        st.session_state.data["study_plan"][i]["completed"] = True
                        save_data(st.session_state.data)
                        st.rerun()
                st.session_state[key] = st.checkbox("Done", key=key, label_visibility="collapsed")
        
        # Progress
        study_tasks = [t for t in plan if t["type"] == "study"]
        done = sum(1 for t in study_tasks if t.get("completed", False))
        st.info(f"📊 **Progress**: {done}/{len(study_tasks)} sessions completed "
                f"({done/len(study_tasks)*100:.0f}%)")

# ========================================
# AUTOMATIC REMINDERS
# ========================================
def check_reminders():
    plan = st.session_state.data.get("study_plan", [])
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    for task in plan:
        if (task.get("date") == today and task["type"] == "study" and 
            not task.get("completed", False)):
            try:
                start_time = datetime.strptime(task["start_time"], "%H:%M")
                start_today = datetime.combine(now.date(), start_time.time())
                end_today = start_today + timedelta(minutes=task["duration"])
                
                if start_today <= now <= end_today:
                    last_hydration = st.session_state.data.get("last_hydration")
                    if last_hydration is None or (now - datetime.fromisoformat(last_hydration)).seconds > 600:
                        st.session_state.data["last_hydration"] = now.isoformat()
                        save_data(st.session_state.data)
                        st.error("🔔 **HYDRATION REMINDER** ⏰\n"
                                f"💧 Drink water now!\n"
                                f"📖 You're studying: **{task['topic']}**")
                        return True
            except:
                continue
    return False

# ========================================
# OTHER PAGES (SIMPLE)
# ========================================
def work_page():
    st.header("💼 Work Planner")
    st.info("📝 Add meetings and deadlines here")
    if st.button("🧪 Test Work"):
        st.success("✅ Work page works!")

def health_page():
    st.header("💚 Health Tracker")
    col1, col2, col3 = st.columns(3)
    with col1:
        water = st.number_input("💧 Water (glasses)", 0, 20, 8)
    with col2:
        exercise = st.number_input("🏃 Exercise (min)", 0, 120, 30)
    with col3:
        sleep = st.number_input("😴 Sleep (hours)", 0.0, 12.0, 8.0)
    
    if st.button("💾 Save Health"):
        today = datetime.now().strftime("%Y-%m-%d")
        st.session_state.data["health_data"][today] = {
            "water": water, "exercise": exercise, "sleep": sleep
        }
        save_data(st.session_state.data)
        st.success("✅ Health saved!")

def dashboard_page():
    st.header("📊 Analytics Dashboard")
    
    plan = st.session_state.data.get("study_plan", [])
    study_tasks = [t for t in plan if t["type"] == "study"]
    done = sum(1 for t in study_tasks if t.get("completed", False))
    total = len(study_tasks)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Study Sessions", f"{done}/{total}")
        st.metric("📈 Productivity", f"{done/total*100:.0f}%" if total else "0%")
    
    # Chart
    if total > 0:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie([done, total-done], labels=["✅ Completed", "⏳ Pending"], 
               autopct='%1.1f%%', colors=['#4CAF50', '#FF9800'])
        ax.set_title("Study Progress")
        st.pyplot(fig)
    else:
        st.info("👆 Generate a study plan first!")

# ========================================
# MAIN APP
# ========================================
def main():
    st.set_page_config(
        page_title="AI Study Notifier", 
        page_icon="🚀",
        layout="wide"
    )
    
    # Title
    st.title("🚀 AI Study • Work • Health Notifier")
    st.markdown("**Smart timetables • Auto reminders • Progress tracking**")
    
    # Sidebar
    st.sidebar.title("📂 Navigation")
    page = st.sidebar.radio("", ["Study", "Work", "Health", "Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ✨ **What it does:**
    • 📚 Creates study schedules
    • 💧 Hydration reminders every 10min
    • ⏸️ 20min breaks after 60min study
    • 📊 Live progress tracking
    • 💾 Auto saves everything
    """)
    
    # Pages
    if page == "Study":
        study_page()
    elif page == "Work":
        work_page()
    elif page == "Health":
        health_page()
    elif page == "Dashboard":
        dashboard_page()
    
    # Auto reminders (only on study page)
    if page == "Study":
        check_reminders()
    
    # Save button
    if st.sidebar.button("💾 Save All Data"):
        save_data(st.session_state.data)
        st.sidebar.success("✅ Saved!")

if __name__ == "__main__":
    main()
