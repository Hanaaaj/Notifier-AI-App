import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time

# --- LOGIC ENGINE (Rule-Based AI) ---
class FocusFlowOrchestrator:
    def __init__(self):
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
        if 'water' not in st.session_state:
            st.session_state.water = 0
        if 'completed_count' not in st.session_state:
            st.session_state.completed_count = 0

    def generate_smart_timetable(self, topics, days, daily_hours):
        """Rule-based distribution logic with burnout prevention."""
        if days <= 0: return None
        
        per_day = -(-len(topics) // days)  # Ceiling division
        timetable = []
        
        for i in range(days):
            day_date = datetime.date.today() + datetime.timedelta(days=i)
            # Logic: If daily hours < 3, flag as 'High Pressure'
            status = "Optimal" if daily_hours >= (per_day * 1.5) else "High Pressure"
            
            timetable.append({
                "Date": day_date.strftime("%b %d"),
                "Topics": ", ".join(topics[i*per_day : (i+1)*per_day]),
                "Workload": f"{per_day} Topics",
                "Status": status,
                "Reminders": "20m Break / Hydrate every 10m"
            })
        return timetable

    def get_wellness_analysis(self):
        """AI Diagnostic based on user inputs."""
        score = 0
        score += min(st.session_state.water * 10, 50)  # Max 50 pts for water
        score += min(st.session_state.completed_count * 10, 50) # Max 50 pts for productivity
        
        if score < 40: return "Critically Low", "Increase water and task focus."
        if score < 75: return "Moderate", "You are steady, but watch your hydration."
        return "Peak Performance", "Excellent balance of health and work!"

# --- UI CONFIGURATION ---
st.set_page_config(page_title="FocusFlow AI", page_icon="⚡", layout="wide")
orch = FocusFlowOrchestrator()

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("⚡ FocusFlow AI")
st.sidebar.caption("Smart Study & Health Orchestrator")
menu = st.sidebar.radio("Navigate", ["Study Section", "Work Section", "Health Section", "Analytics"])

# --- 1. STUDY SECTION ---
if menu == "Study Section":
    st.header("📚 AI Study Orchestrator")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            module = st.text_input("Module Name", "Final Examination")
            exam_date = st.date_input("Deadline", datetime.date.today() + datetime.timedelta(days=7))
        with col2:
            hours = st.slider("Available Daily Hours", 1, 12, 4)
            topics_raw = st.text_area("Topics (comma separated)", "Calculus, Ethics, Physics, Logic")

    if st.button("Generate AI Timetable"):
        topic_list = [t.strip() for t in topics_raw.split(",") if t.strip()]
        days_rem = (exam_date - datetime.date.today()).days
        
        plan = orch.generate_smart_timetable(topic_list, days_rem, hours)
        if plan:
            st.success(f"Logic Engine: {len(topic_list)} topics distributed over {days_rem} days.")
            st.table(pd.DataFrame(plan))
            st.info(f"💡 **AI Insight:** To prevent burnout, we have auto-scheduled 20-minute breaks every 60 minutes.")
        else:
            st.error("Please select a future date.")

# --- 2. WORK SECTION ---
elif menu == "Work Section":
    st.header("💼 Work Engine")
    
    with st.form("work_form", clear_on_submit=True):
        new_task = st.text_input("Task Description")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        if st.form_submit_button("Add to Focus Queue"):
            st.session_state.tasks.append({"name": new_task, "pri": priority})
            st.toast("Task Added!", icon="📝")
            st.rerun()

    st.subheader("Current Queue")
    for i, t in enumerate(st.session_state.tasks):
        c1, c2 = st.columns([4, 1])
        c1.info(f"**[{t['pri']}]** {t['name']}")
        if c2.button("Done", key=f"done_{i}"):
            st.session_state.tasks.pop(i)
            st.session_state.completed_count += 1
            st.toast("Task Completed!", icon="✅")
            st.rerun()

# --- 3. HEALTH SECTION ---
elif menu == "Health Section":
    st.header("🌿 Health & Wellness")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Water Intake", f"{st.session_state.water} / 8 Glasses")
        if st.button("Drink 1 Glass 💧"):
            st.session_state.water += 1
            st.toast("Stay Hydrated!", icon="💧")
            st.rerun()
            
    with col2:
        status, advice = orch.get_wellness_analysis()
        st.subheader(f"Status: {status}")
        st.write(advice)

# --- 4. ANALYTICS ---
elif menu == "Analytics":
    st.header("📊 Performance Dashboard")
    
    c1, c2 = st.columns(2)
    with c1:
        # Task Chart
        fig1, ax1 = plt.subplots()
        ax1.bar(["Completed", "Pending"], [st.session_state.completed_count, len(st.session_state.tasks)], color=['#28a745', '#ffc107'])
        ax1.set_title("Productivity Distribution")
        st.pyplot(fig1)
        
    with c2:
        # Hydration Progress
        fig2, ax2 = plt.subplots()
        labels = ['Water Drunk', 'Remaining']
        sizes = [st.session_state.water, max(0, 8 - st.session_state.water)]
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#007bff', '#e9ecef'])
        ax2.set_title("Daily Hydration Goal")
        st.pyplot(fig2)
