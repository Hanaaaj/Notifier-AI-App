import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import streamlit.components.v1 as components

# --- AI ORCHESTRATION ENGINE ---
class FocusFlowAI:
    @staticmethod
    def generate_smart_schedule(topics, days, start_hour):
        """Rule-based AI that auto-calculates reminder and tracking timestamps"""
        if days <= 0: return []
        
        per_day = -(-len(topics) // days)
        schedule = []
        
        # Base time set to today at the professor's chosen start hour
        base_time = datetime.datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
        
        for i in range(len(topics)):
            # Distribute topics across hours (e.g., 1 topic every 1.5 hours)
            task_time = base_time + datetime.timedelta(hours=i * 1.5)
            
            schedule.append({
                "id": i,
                "Topic": topics[i],
                "Time": task_time,
                "DisplayTime": task_time.strftime("%H:%M (%p)"),
                "Status": "Pending", # Options: Pending, Done, Missed
                "Reminded": False
            })
        return schedule

# --- UI SETUP ---
st.set_page_config(page_title="FocusFlow AI", layout="wide", page_icon="🤖")

# Initialize Session States
if 'schedule' not in st.session_state:
    st.session_state.schedule = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"done": 0, "missed": 0}

# --- JAVASCRIPT AUDIO ALERT ---
def play_notification(message):
    js_code = f"""
    <script>
    var audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
    audio.play();
    alert("🚨 FOCUSFLOW ALERT: {message}");
    </script>
    """
    components.html(js_code, height=0)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🤖 FocusFlow AI")
menu = st.sidebar.radio("Navigation", ["AI Scheduler", "Live Task Tracker", "Analytics"])

# --- 1. AI SCHEDULER ---
if menu == "AI Scheduler":
    st.header("📅 AI Automatic Timetable & Setup")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            topics_raw = st.text_area("Enter Topics (comma separated)", "Logic Design, Python Dev, Database SQL")
            days = st.number_input("Days to Deadline", 1, 30, 3)
        with col2:
            start_hour = st.slider("Start Time (Hour)", 0, 23, 9)
            if st.button("Generate & Automate Schedule"):
                topic_list = [t.strip() for t in topics_raw.split(",") if t.strip()]
                st.session_state.schedule = FocusFlowAI.generate_smart_schedule(topic_list, days, start_hour)
                st.session_state.stats = {"done": 0, "missed": 0} # Reset stats
                st.success("AI has generated your schedule and set triggers!")

    if st.session_state.schedule:
        st.subheader("Your AI-Planned Sessions")
        df = pd.DataFrame(st.session_state.schedule)[["DisplayTime", "Topic", "Status"]]
        st.table(df)

# --- 2. LIVE TASK TRACKER (The Core Logic) ---
elif menu == "Live Task Tracker":
    st.header("🔔 Live Focus Queue")
    st.write(f"Current Time: **{datetime.datetime.now().strftime('%H:%M:%S')}**")
    
    if not st.session_state.schedule:
        st.info("Please generate a schedule first.")
    else:
        now = datetime.datetime.now()
        
        for i, task in enumerate(st.session_state.schedule):
            # AUTOMATIC MISSED CALCULATION
            # Logic: If current time > task time AND status is still Pending
            if now > task['Time'] and task['Status'] == "Pending":
                st.session_state.schedule[i]['Status'] = "Missed"
                st.session_state.stats['missed'] += 1
                play_notification(f"You missed the window for: {task['Topic']}")

            # ALERT TRIGGER
            if now >= task['Time'] and not task['Reminded'] and task['Status'] != "Done":
                st.session_state.schedule[i]['Reminded'] = True
                play_notification(f"Time to start: {task['Topic']}")

            # DISPLAY TASKS
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 3, 2])
                c1.write(f"🕒 **{task['DisplayTime']}**")
                c2.write(f"📖 {task['Topic']}")
                
                if task['Status'] == "Pending":
                    if c3.button("Click to Done ✅", key=f"btn_{i}"):
                        st.session_state.schedule[i]['Status'] = "Done"
                        st.session_state.stats['done'] += 1
                        st.rerun()
                else:
                    color = "green" if task['Status'] == "Done" else "red"
                    c3.markdown(f":{color}[**{task['Status']}**]")

        if st.button("Refresh Clock"):
            st.rerun()

# --- 3. ANALYTICS ---
elif menu == "Analytics":
    st.header("📊 Performance Metrics")
    done = st.session_state.stats['done']
    missed = st.session_state.stats['missed']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tasks Completed", done)
        st.metric("Tasks Missed", missed)
    
    with col2:
        if done + missed > 0:
            fig, ax = plt.subplots()
            ax.pie([done, missed], labels=['Done', 'Missed'], autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
            st.pyplot(fig)
        else:
            st.write("No data to display yet. Complete some tasks!")
