import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import streamlit.components.v1 as components

# --- AI ORCHESTRATION LOGIC ---
class FocusFlowAI:
    @staticmethod
    def generate_full_schedule(topics, deadline, start_hour):
        """Rule-based AI: Generates study blocks, hydration pings, and breaks."""
        days_left = (deadline - datetime.date.today()).days
        if days_left <= 0: days_left = 1
        
        per_day = -(-len(topics) // days_left)
        schedule = []
        base_time = datetime.datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
        
        for i, topic in enumerate(topics):
            # 1. Study Block
            study_time = base_time + datetime.timedelta(hours=i * 2)
            schedule.append({
                "id": f"study_{i}",
                "Type": "Study",
                "Topic": topic,
                "Time": study_time,
                "DisplayTime": study_time.strftime("%H:%M"),
                "Status": "Pending",
                "Reminded": False
            })
            
            # 2. Automated Break (1 hour after study starts)
            break_time = study_time + datetime.timedelta(hours=1)
            schedule.append({
                "id": f"break_{i}",
                "Type": "Break",
                "Topic": "🧘 Mandatory AI Break",
                "Time": break_time,
                "DisplayTime": break_time.strftime("%H:%M"),
                "Status": "Pending",
                "Reminded": False
            })
            
            # 3. Hydration Reminder (every study cycle)
            hydro_time = study_time + datetime.timedelta(minutes=30)
            schedule.append({
                "id": f"hydro_{i}",
                "Type": "Health",
                "Topic": "💧 Hydration Ping",
                "Time": hydro_time,
                "DisplayTime": hydro_time.strftime("%H:%M"),
                "Status": "Pending",
                "Reminded": False
            })
            
        return schedule

# --- UI SETUP ---
st.set_page_config(page_title="FocusFlow AI", layout="wide", page_icon="🚀")

if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'health_stats' not in st.session_state:
    st.session_state.health_stats = {"water": 0, "breaks": 0}
if 'productivity' not in st.session_state:
    st.session_state.productivity = {"done": 0, "missed": 0}

# --- JS ALERT & BEEP ---
def trigger_alert(msg):
    js = f"""
    <script>
    var audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
    audio.play();
    alert("FocusFlow AI: {msg}");
    </script>
    """
    components.html(js, height=0)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 FocusFlow AI")
menu = st.sidebar.radio("Navigation", ["📚 Study", "💼 Work", "🌿 Health & Stats"])

if st.sidebar.button("🗑️ Reset All Data"):
    st.session_state.tasks = []
    st.session_state.health_stats = {"water": 0, "breaks": 0}
    st.session_state.productivity = {"done": 0, "missed": 0}
    st.rerun()

# --- 1. STUDY SECTION ---
if menu == "📚 Study":
    st.header("Study Orchestrator")
    with st.expander("Setup Plan", expanded=True):
        t_raw = st.text_area("Topics (comma separated)", "Neural Networks, Logic, Ethics")
        d_line = st.date_input("Deadline", datetime.date.today() + datetime.timedelta(days=3))
        s_hour = st.slider("Start Hour", 0, 23, 9)
        if st.button("Generate AI Schedule"):
            t_list = [t.strip() for t in t_raw.split(",") if t.strip()]
            st.session_state.tasks = FocusFlowAI.generate_full_schedule(t_list, d_line, s_hour)
            st.success("AI generated Study, Break, and Hydration slots!")

# --- 2. WORK SECTION ---
elif menu == "💼 Work":
    st.header("Work Priority Engine")
    with st.form("work_form"):
        w_task = st.text_input("Task Name")
        w_min = st.number_input("Minutes until due", 1, 120, 15)
        if st.form_submit_button("Add Task"):
            t_time = datetime.datetime.now() + datetime.timedelta(minutes=w_min)
            st.session_state.tasks.append({
                "id": f"work_{time.time()}", "Type": "Work", "Topic": w_task,
                "Time": t_time, "DisplayTime": t_time.strftime("%H:%M"),
                "Status": "Pending", "Reminded": False
            })
            st.rerun()

# --- 3. HEALTH & STATS SECTION ---
elif menu == "🌿 Health & Stats":
    st.header("Wellness & Performance Analytics")
    h = st.session_state.health_stats
    p = st.session_state.productivity
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Water Glasses", h['water'])
    c2.metric("Breaks Taken", h['breaks'])
    c3.metric("Productivity Score", f"{int((p['done']/(p['done']+p['missed']+1))*100)}%")
    
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Task Completion")
        fig, ax = plt.subplots()
        ax.bar(["Done", "Missed"], [p['done'], p['missed']], color=['#2ecc71', '#e74c3c'])
        st.pyplot(fig)
    with col_b:
        st.subheader("Daily Wellness")
        fig2, ax2 = plt.subplots()
        ax2.pie([h['water'], 8], labels=["Drank", "Goal"], colors=['#3498db', '#ecf0f1'])
        st.pyplot(fig2)

# --- LIVE MONITOR (ALERTS & AUTO-MISSED) ---
st.divider()
st.subheader("🔔 Live Monitor")
now = datetime.datetime.now()

for i, task in enumerate(st.session_state.tasks):
    # AUTO-MISSED LOGIC
    if now > task['Time'] and task['Status'] == "Pending":
        st.session_state.tasks[i]['Status'] = "Missed"
        st.session_state.productivity['missed'] += 1
        trigger_alert(f"MISSED: {task['Topic']}")

    # REMINDER LOGIC
    if now >= task['Time'] and not task['Reminded'] and task['Status'] != "Done":
        st.session_state.tasks[i]['Reminded'] = True
        trigger_alert(f"TIME TO START: {task['Topic']}")

    # RENDER TASKS
    with st.container(border=True):
        c_icon, c_info, c_act = st.columns([1, 4, 2])
        icons = {"Study": "📚", "Break": "🧘", "Health": "💧", "Work": "💼"}
        c_icon.write(f"### {icons.get(task['Type'], '📌')}")
        c_info.write(f"**{task['Topic']}** ({task['DisplayTime']})")
        
        if task['Status'] == "Pending":
            if c_act.button("Mark Done ✅", key=f"btn_{task['id']}"):
                st.session_state.tasks[i]['Status'] = "Done"
                st.session_state.productivity['done'] += 1
                if task['Type'] == "Health": st.session_state.health_stats['water'] += 1
                if task['Type'] == "Break": st.session_state.health_stats['breaks'] += 1
                st.rerun()
        else:
            clr = "green" if task['Status'] == "Done" else "red"
            c_act.markdown(f":{clr}[**{task['Status']}**]")

st.button("🔄 Refresh System Clock")
