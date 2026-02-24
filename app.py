import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="AuraFlow: Adaptive Intelligence", page_icon="🧠", layout="wide")

# Advanced CSS for Gamification & Categorized Alerts
st.markdown("""
    <style>
    .badge { background: linear-gradient(45deg, #FFD700, #FFA500); color: black; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-right: 5px; }
    .work-tag { border-left: 5px solid #4facfe; padding-left: 10px; }
    .health-tag { border-left: 5px solid #00ffa3; padding-left: 10px; }
    .meeting-tag { border-left: 5px solid #f093fb; padding-left: 10px; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #4facfe , #00ffa3); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ADVANCED SESSION STATE (Memory & Habit Tracking) ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"Work": 0, "Health": 0, "Meeting": 0, "streak": 0}
if 'start_session' not in st.session_state:
    st.session_state.start_session = datetime.now()
if 'badges' not in st.session_state:
    st.session_state.badges = []

# --- 3. THE INTELLIGENCE ENGINE ---

def trigger_alert(title, msg, sound=True):
    """Triggers Desktop Notification and optional Audio via JS"""
    js = f"""<script>
    if (Notification.permission === 'granted') {{
        new Notification("{title}", {{body: "{msg}"}});
        { 'var audio = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg"); audio.play();' if sound else '' }
    }} else {{ Notification.requestPermission(); }}
    </script>"""
    st.components.v1.html(js, height=0)

def get_ai_motivation(task_name):
    """Requirement 5: Smart Motivational Popups"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Give a 1-sentence badass motivational push for the task: {task_name}"
        return model.generate_content(prompt).text
    except:
        return "You've got this! Focus on the finish line."

# --- 4. SIDEBAR: HABIT MONITORING ---
with st.sidebar:
    st.title("🌊 AuraFlow")
    st.write("### 🧠 Proactive Brain Monitor")
    
    # Logic for Requirement 1: Proactive Suggestions
    work_duration = datetime.now() - st.session_state.start_session
    minutes_worked = work_duration.seconds // 60
    
    if minutes_worked > 120:
        st.error("⚠️ Overload detected! You've worked for 2 hours. AI suggests a 15-min break.")
        if st.button("Start AI-Suggested Break"):
            trigger_alert("Proactive Health Alert", "2 Hours reached. Step away from the screen.")
    else:
        st.info(f"Session focus: {minutes_worked} minutes. You are in optimal flow.")

    st.markdown("---")
    if st.button("🔔 Enable System Sound & Alerts"):
        st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)

# --- 5. MAIN UI ---
tabs = st.tabs(["🎯 Productivity Center", "📈 Performance Dashboard", "🏆 Rewards"])

# TAB 1: CATEGORIZED ALERTS & SCHEDULING
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Add Categorized Alert")
        with st.form("task_form", clear_on_submit=True):
            t_name = st.text_input("Task/Event Name")
            t_cat = st.selectbox("Category", ["Work", "Health", "Meeting", "Personal"])
            t_type = st.radio("Frequency", ["One-time", "Recurring (Hourly)", "Recurring (Daily)"])
            if st.form_submit_button("Add to Engine"):
                st.session_state.tasks.append({"name": t_name, "cat": t_cat, "freq": t_type, "status": "Pending", "created": datetime.now()})
                st.rerun()

    with c2:
        st.subheader("Live Notification Queue")
        for i, t in enumerate(st.session_state.tasks):
            if t['status'] == "Pending":
                # Color coding based on Category (Requirement 2)
                tag_class = f"{t['cat'].lower()}-tag"
                st.markdown(f'<div class="{tag_class}"><b>{t["cat"]}</b>: {t["name"]} ({t["freq"]})</div>', unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                if b1.button("✅ Complete", key=f"done{i}"):
                    st.session_state.tasks[i]['status'] = "Done"
                    st.session_state.stats[t['cat']] += 1
                    st.session_state.stats["streak"] += 1
                    # Requirement 6: Gamification Check
                    if st.session_state.stats["streak"] % 3 == 0:
                        st.session_state.badges.append(f"🔥 {st.session_state.stats['streak']} Streak")
                    st.balloons()
                    st.rerun()
                if b2.button("💡 Get Motivation", key=f"mot{i}"):
                    st.warning(get_ai_motivation(t['name']))

# TAB 2: VISUAL DASHBOARD (Requirement 3)
with tabs[1]:
    st.subheader("Visual Performance Tracking")
    m1, m2, m3 = st.columns(3)
    m1.metric("Tasks Completed", st.session_state.stats["Work"] + st.session_state.stats["Meeting"])
    m2.metric("Health Milestones", st.session_state.stats["Health"])
    m3.metric("Current Streak", f"{st.session_state.stats['streak']} Tasks")

    # Interactive Dashboard Chart
    df = pd.DataFrame([
        {"Category": "Work", "Completed": st.session_state.stats["Work"]},
        {"Category": "Health", "Completed": st.session_state.stats["Health"]},
        {"Category": "Meeting", "Completed": st.session_state.stats["Meeting"]}
    ])
    fig = px.bar(df, x="Category", y="Completed", color="Category", title="Weekly Habit Distribution")
    st.plotly_chart(fig, use_container_width=True)

# TAB 3: REWARDS & CALENDAR (Requirement 6 & 7)
with tabs[2]:
    st.subheader("Achievement Vault")
    if not st.session_state.badges:
        st.write("No badges yet. Complete 3 tasks to unlock your first streak badge!")
    else:
        for b in st.session_state.badges:
            st.markdown(f'<span class="badge">{b}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🗓️ Calendar Integration (Mock Mode)")
    st.write("Calendar Sync Active: Auto-imported 2 events from G-Calendar.")
    if st.button("Simulate Auto-Import"):
        st.session_state.tasks.append({"name": "Team Standup", "cat": "Meeting", "freq": "One-time", "status": "Pending"})
        st.rerun()
