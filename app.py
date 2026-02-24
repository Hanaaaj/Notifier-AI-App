import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import pytz
import time

# --- 1. GLOBAL SYNC & CONFIG ---
st.set_page_config(page_title="AuraFlow | Unified Assistant", page_icon="🚀", layout="wide")

def get_uae_now():
    """Universal UAE time sync to prevent TypeErrors."""
    return datetime.now(pytz.timezone('Asia/Dubai'))

# Initialize Session States
for key in ['tasks', 'deadlines', 'meetings', 'water_ml', 'last_water_check', 'notified_cache']:
    if key not in st.session_state:
        if key == 'water_ml': st.session_state[key] = 0
        elif key == 'last_water_check': st.session_state[key] = get_uae_now()
        elif key == 'notified_cache': st.session_state[key] = set()
        else: st.session_state[key] = []

# --- 2. THE AI BRAIN (Suggestions Engine) ---
def get_ai_logic():
    now = get_uae_now()
    suggestions = []
    
    # Study Logic: Reverse planning from deadlines
    for dl in st.session_state.deadlines:
        days_to = (dl['date'] - now.date()).days
        if 0 < days_to <= 7:
            suggestions.append({"title": f"Study: {dl['sub']}", "desc": f"{days_to} days to {dl['type']}. Start deep work.", "cat": "Study"})

    # Work Logic: Meeting density
    if len(st.session_state.meetings) > 3:
        suggestions.append({"title": "Meeting Fatigue", "desc": "High meeting volume. Schedule a 10m 'No-Screen' break.", "cat": "Work"})

    # Universal Health Logic
    if now.hour > 20:
        suggestions.append({"title": "Blue Light Alert", "desc": "Evening detected. Enable night shift mode.", "cat": "Health"})
    
    return suggestions

# --- 3. UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .main-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #EEE; margin-bottom: 15px; }
    .section-header { color: #1E293B; font-weight: 700; border-bottom: 2px solid #3B82F6; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NAVIGATION & HEADER ---
now = get_uae_now()
curr_time = now.strftime("%H:%M")

st.title("AuraFlow Unified Dashboard 🇦🇪")
st.info(f"Real-time sync: {now.strftime('%H:%M:%S')} (GST)")

tab_study, tab_work, tab_health, tab_ai = st.tabs(["🎓 Study", "💼 Work", "🏥 Health", "✨ AI Insights"])

# --- 5. MODULE: STUDY ---
with tab_study:
    st.markdown('<div class="section-header">Academic Resilience</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("study_form"):
            sub = st.text_input("Module/Subject")
            dtype = st.selectbox("Type", ["Exam", "Project", "Assignment"])
            ddate = st.date_input("Deadline", min_value=now.date())
            if st.form_submit_button("Log Deadline"):
                st.session_state.deadlines.append({"sub": sub, "type": dtype, "date": ddate})
                st.rerun()
    with c2:
        for dl in sorted(st.session_state.deadlines, key=lambda x: x['date']):
            st.warning(f"⏳ **{dl['date']}** | {dl['sub']} ({dl['type']})")

# --- 6. MODULE: WORK ---
with tab_work:
    st.markdown('<div class="section-header">Professional Performance</div>', unsafe_allow_html=True)
    wc1, wc2 = st.columns([1, 2])
    with wc1:
        meeting_name = st.text_input("Meeting Title")
        meeting_time = st.text_input("Time (HH:MM)", value=curr_time)
        if st.button("Add Meeting"):
            st.session_state.meetings.append({"name": meeting_name, "time": meeting_time})
            st.rerun()
    with wc2:
        if st.session_state.meetings:
            df_m = pd.DataFrame(st.session_state.meetings)
            st.table(df_m)

# --- 7. MODULE: HEALTH ---
with tab_health:
    st.markdown('<div class="section-header">Vitals & Wellness</div>', unsafe_allow_html=True)
    hc1, hc2, hc3 = st.columns(3)
    hc1.metric("Hydration", f"{st.session_state.water_ml}ml")
    hc2.metric("Screen Breaks", "4/6")
    hc3.metric("Daily Movement", "15m")
    
    # Health Dashboard
    df_health = pd.DataFrame({'Activity': ['Water', 'Exercise', 'Sleep'], 'Score': [st.session_state.water_ml/20, 40, 80]})
    fig_h = px.polar_bar(df_health, r='Score', theta='Activity', template="plotly_white")
    st.plotly_chart(fig_h, width="stretch")

# --- 8. AI & NOTIFICATIONS ---
with tab_ai:
    st.subheader("✨ Proactive Guidance")
    for s in get_ai_logic():
        with st.container():
            st.markdown(f"**[{s['cat']}] {s['title']}**")
            st.caption(s['desc'])
            if st.button("Schedule this", key=s['title']):
                st.session_state.tasks.append({"name": s['title'], "time": curr_time, "status": "Pending"})
                st.toast("Scheduled!")

# --- 9. REAL-TIME ENGINE ---
# Check Water/Exercise Timer (Every 30m)
if (now - st.session_state.last_water_check).total_seconds() / 60 >= 30:
    st.toast("💧 Health Reminder: Drink 250ml water and stretch for 2 minutes!", icon="🧘")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now

# Exact Minute Notifications
for t in (st.session_state.tasks + st.session_state.meetings):
    target_time = t.get('time')
    if target_time == curr_time:
        nid = f"{t.get('name')}_{curr_time}"
        if nid not in st.session_state.notified_cache:
            st.toast(f"🔔 ALERT: {t.get('name')} is happening now!", icon="⏰")
            st.session_state.notified_cache.add(nid)

time.sleep(1)
st.rerun()
