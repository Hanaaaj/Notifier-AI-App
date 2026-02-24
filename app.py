import streamlit as st
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ========================================
# STORAGE
# ========================================
@st.cache_data
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {"study_plan": [], "completed_tasks": []}

def save_data(data):
    try:
        with open("data.json", "w") as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

# Init
if "data" not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.plan_id = 0

# ========================================
# STUDY PLANNER
# ========================================
def study_page():
    st.header("📚 AI Study Planner")
    
    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        module = st.text_input("Module", "Mathematics")
        exam_date = st.date_input("Exam Date", value=datetime.now())
    with col2:
        hours = st.number_input("Daily Hours", 1.0, 8.0, 2.0)
    
    topics_text = st.text_area("Topics (one per line)", 
                              "Topic 1\nTopic 2\nTopic 3\nTopic 4")
    topics = [t.strip() for t in topics_text.splitlines() if t.strip()]
    
    # Generate
    if st.button("🎯 GENERATE TIMETABLE", use_container_width=True):
        plan = []
        current_date = datetime.now().date()
        
        # Create 1-week plan
        for i in range(min(7, len(topics))):
            topic = topics[i % len(topics)]
            date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Study session
            plan.append({
                "id": st.session_state.plan_id + i,
                "module": module,
                "topic": topic[:25],
                "date": date_str,
                "time": f"09:00",
                "duration": 60,
                "type": "study",
                "completed": False
            })
            
            # Break
            plan.append({
                "id": st.session_state.plan_id + i + 1000,
                "module": module,
                "topic": "BREAK (20min)",
                "date": date_str,
                "time": f"10:00",
                "duration": 20,
                "type": "break",
                "completed": False
            })
        
        st.session_state.data["study_plan"] = plan
        st.session_state.plan_id += 10000
        if save_data(st.session_state.data):
            st.success(f"✅ Generated {len([t for t in plan if t['type']=='study'])} study sessions!")
        st.rerun()
    
    # Show plan
    plan = st.session_state.data.get("study_plan", [])
    if plan:
        st.subheader("📅 Your Schedule")
        
        # Group by unique task IDs to avoid duplicate keys
        task_checkboxes = {}
        
        for task in plan:
            col1, col2 = st.columns([5, 1])
            with col1:
                icon = "⏸️" if task["type"] == "break" else "📖"
                status = "✅" if task.get("completed", False) else "⏳"
                st.write(f"{status} **{icon}** {task['date']} {task['time']} "
                        f"({task['duration']}m) {task['topic']}")
            
            # Checkbox with UNIQUE key per task
            if task["type"] == "study":
                task_id = task["id"]
                if task_id not in task_checkboxes:
                    task_checkboxes[task_id] = st.checkbox(
                        "Done ✓", 
                        key=f"task_{task_id}",
                        value=task.get("completed", False)
                    )
                    
                    # Update if changed
                    if task_checkboxes[task_id] != task.get("completed", False):
                        for t in plan:
                            if t["id"] == task_id:
                                t["completed"] = task_checkboxes[task_id]
                                break
                        st.session_state.data["study_plan"] = plan
                        save_data(st.session_state.data)
                        st.rerun()
        
        # Stats
        study_tasks = [t for t in plan if t["type"] == "study"]
        done_count = sum(1 for t in study_tasks if t.get("completed", False))
        total_count = len(study_tasks)
        st.info(f"📊 **Progress**: {done_count}/{total_count} "
                f"({done_count/total_count*100:.0f}% done)")
        
        st.markdown("---")
        st.subheader("🔔 **AUTO REMINDERS**")
        
        # Hydration check
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        for task in study_tasks:
            if (task["date"] == today_str and not task.get("completed", False)):
                try:
                    start_time = datetime.strptime(task["time"], "%H:%M").time()
                    start_datetime = datetime.combine(now.date(), start_time)
                    end_datetime = start_datetime + timedelta(minutes=task["duration"])
                    
                    if start_datetime <= now <= end_datetime:
                        st.error("💧 **HYDRATION REMINDER!** ⏰\n"
                                f"Drink water now - you're studying **{task['topic']}**")
                        break
                except:
                    continue

# ========================================
# OTHER PAGES (SIMPLE)
# ========================================
def work_page():
    st.header("💼 Work Tasks")
    st.info("➕ Add meetings, deadlines, and tasks")
    st.button("Test Work Page")

def health_page():
    st.header("💚 Health Tracker")
    col1, col2, col3 = st.columns(3)
    with col1: st.number_input("💧 Water glasses", 0, 20, 8)
    with col2: st.number_input("🏃 Exercise min", 0, 120, 30)
    with col3: st.number_input("😴 Sleep hours", 0.0, 12.0, 8.0)
    st.button("Save Health")

def dashboard_page():
    st.header("📊 Dashboard")
    plan = st.session_state.data.get("study_plan", [])
    study_tasks = [t for t in plan if t["type"] == "study"]
    
    if not study_tasks:
        st.warning("👆 Create a study plan first!")
        return
    
    done = sum(1 for t in study_tasks if t.get("completed", False))
    total = len(study_tasks)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Study Tasks", f"{done}/{total}")
        st.metric("📈 Progress", f"{done/total*100:.1f}%")
    
    # Chart
    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie([done, total-done], labels=["✅ Done", "⏳ Pending"], 
           autopct='%1.1f%%', colors=['#10B981','#F59E0B'])
    ax.set_title("Study Progress")
    st.pyplot(fig)

# ========================================
# MAIN APP
# ========================================
def main():
    st.set_page_config(
        page_title="AI Study Notifier",
        page_icon="🚀",
        layout="wide"
    )
    
    # Header
    st.title("🚀 AI Study Notifier")
    st.markdown("*Smart schedules • Auto reminders • Progress tracking*")
    
    # Navigation
    page = st.sidebar.selectbox("📂 Go To", ["Study", "Work", "Health", "Dashboard"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **✨ Features:**
    • 📚 Auto study timetables  
    • 💧 Hydration alerts (every 10min)
    • ⏸️ 20min breaks after 60min
    • 📊 Live progress charts
    • 💾 Auto-save to JSON
    """)
    
    # Render pages
    if page == "Study":
        study_page()
    elif page == "Work":
        work_page()
    elif page == "Health":
        health_page()
    elif page == "Dashboard":
        dashboard_page()
    
    # Save button
    if st.sidebar.button("💾 Save Data"):
        save_data(st.session_state.data)
        st.sidebar.success("✅ Saved!")

if __name__ == "__main__":
    main()
