import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import time

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="AuraFlow Study", page_icon="🎓", layout="wide")

def get_uae_now():
    uae_tz = pytz.timezone('Asia/Dubai')
    return datetime.now(uae_tz)

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); text-align: center;
    }
    .deadline-card {
        background: #FFFBEB; border-left: 5px solid #F59E0B;
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    .suggestion-box {
        background-color: #F0F9FF; border-left: 5px solid #0EA5E9;
        padding: 15px; border-radius: 10px; margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSISTENT STATE ---
if 'deadlines' not in st.session_state:
    st.session_state.deadlines = [] # Stores: Subject, Date, Type (Exam/Project)
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state:
    st.session_state.notified_cache = set()

# --- 3. THE STUDY AI LOGIC ---
now = get_uae_now()
curr_time_hm = now.strftime("%H:%M")

def get_study_suggestions():
    suggestions = []
    
    # 1. Deadline Proximity Check
    for dl in st.session_state.deadlines:
        days_left = (dl['date'] - now.date()).days
        if 0 < days_left <= 7:
            suggestions.append({
                "title": f"Prep: {dl['subject']}",
                "desc": f"{days_left} days until {dl['type']}. Start a 45-min deep work session.",
                "cat": "Study"
            })
    
    # 2. Wellness / Resilience Check
    suggestions.append({"title": "Active Break", "desc": "Do 10 jumping jacks to boost brain blood flow.", "cat": "Exercise"})
    suggestions.append({"title": "Mindful Hydration", "desc": "Drink a glass of water before next module.", "cat": "Health"})
    
    return suggestions

# --- 4. TOP BAR & STATS ---
st.title("🎓 Academic Resilience Planner")
st.caption(f"UAE Time: {now.strftime('%A, %b %d')} | Tracking {len(st.session_state.deadlines)} Deadlines")

m1, m2, m3 = st.columns(3)
with m1: st.markdown(f'<div class="metric-card"><span>Active Projects</span><h3>{len(st.session_state.deadlines)}</h3></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><span>Next Break In</span><h3>25m</h3></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="metric-card"><span>Study Streak</span><h3>4 Days</h3></div>', unsafe_allow_html=True)

# --- 5. DEADLINE INPUT ---
with st.sidebar:
    st.header("📌 Add Deadline")
    sub = st.text_input("Subject/Module")
    d_type = st.selectbox("Type", ["Exam", "Project Deadline", "Quiz"])
    d_date = st.date_input("Date", min_value=now.date())
    if st.button("Log Deadline"):
        st.session_state.deadlines.append({"subject": sub, "type": d_type, "date": d_date})
        st.rerun()

    st.header("⏰ Custom Reminder")
    r_name = st.text_input("Task Name")
    r_time = st.text_input("Time (HH:MM)", value=curr_time_hm)
    if st.button("Set Alarm"):
        st.session_state.tasks.append({"name": r_name, "time": r_time, "status": "Pending", "cat": "Study"})
        st.rerun()

# --- 6. AI SUGGESTIONS (The "When to Start" Engine) ---
st.subheader("✨ AI Study Strategy")
suggestions = get_study_suggestions()
for s in suggestions:
    col_s1, col_s2 = st.columns([5, 1])
    col_s1.markdown(f"""
        <div class="suggestion-box">
            <strong>[{s['cat']}] {s['title']}</strong><br><small>{s['desc']}</small>
        </div>
        """, unsafe_allow_html=True)
    if col_s2.button("Start Now", key=s['title']):
        st.session_state.tasks.append({"name": s['title'], "cat": s['cat'], "time": curr_time_hm, "status": "Pending"})
        st.rerun()

# --- 7. DASHBOARD & TIMELINE ---
st.divider()
c_left, c_right = st.columns(2)

with c_left:
    st.subheader("📅 Upcoming Deadlines")
    for dl in sorted(st.session_state.deadlines, key=lambda x: x['date']):
        st.markdown(f"""
            <div class="deadline-card">
                <strong>{dl['date'].strftime('%b %d')}</strong> — {dl['subject']} ({dl['type']})
            </div>
            """, unsafe_allow_html=True)

with c_right:
    st.subheader("📈 Study Workload")
    if st.session_state.deadlines:
        df = pd.DataFrame(st.session_state.deadlines)
        fig = px.histogram(df, x="date", title="Exam/Project Density", color_discrete_sequence=['#F59E0B'])
        st.plotly_chart(fig, width='stretch')

# --- 8. LIVE NOTIFICATION LOOP ---
# Water & Movement Loop
time_diff = now - st.session_state.last_water_check
if time_diff.total_seconds() / 60 >= 30:
    st.toast("💧 Health Check: Drink water & stretch for 2 mins!", icon="🧘")
    st.session_state.last_water_check = now

# Reminder Popups
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_time_hm:
        notif_id = f"{t['name']}_{curr_time_hm}"
        if notif_id not in st.session_state.notified_cache:
            st.toast(f"🔔 STUDY ALERT: {t['name']}", icon="📖")
            st.session_state.notified_cache.add(notif_id)

time.sleep(1)
st.rerun()
