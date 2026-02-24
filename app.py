import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time

# --- 1. SETTINGS & UAE TIMEZONE ---
st.set_page_config(page_title="AuraFlow | Smart Dashboard", page_icon="🕒", layout="wide")

def get_uae_now():
    """Ensures all time objects are UAE-aware to prevent TypeErrors."""
    uae_tz = pytz.timezone('Asia/Dubai')
    return datetime.now(uae_tz)

# --- 2. MODERN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .metric-card {
        background: white; padding: 24px; border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #F0F2F6;
        text-align: center;
    }
    .suggestion-box {
        background-color: #FDF4FF; padding: 16px; border-radius: 12px;
        border: 1px solid #FAE8FF; margin-bottom: 12px;
        border-left: 5px solid #7E22CE;
    }
    .badge-ai { background: #F3E8FF; color: #7E22CE; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PERSISTENT STATE ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water_ml' not in st.session_state:
    st.session_state.water_ml = 0
if 'last_water_check' not in st.session_state:
    st.session_state.last_water_check = get_uae_now()
if 'notified_cache' not in st.session_state:
    st.session_state.notified_cache = set()

# --- 4. ENGINE LOGIC ---
now = get_uae_now()
curr_time_hm = now.strftime("%H:%M")

def get_smart_suggestions():
    """AI logic to suggest health and focus reminders."""
    suggestions = []
    if st.session_state.water_ml < 1500:
        suggestions.append({"title": "Hydration Hit", "desc": "Drink 250ml to stay focused.", "cat": "Health"})
    # Afternoon energy slump check (UAE Time)
    if 13 <= now.hour <= 16:
        suggestions.append({"title": "Post-Lunch Walk", "desc": "Quick 5-min walk for energy.", "cat": "Health"})
    suggestions.append({"title": "20/20/20 Rule", "desc": "Rest your eyes from the screen.", "cat": "Personal"})
    return suggestions

# --- 5. TOP BAR & CLOCK ---
c_title, c_clock = st.columns([4, 1])
with c_title:
    st.title("Good afternoon! 👋")
    st.caption(f"UAE Standard Time | {now.strftime('%A, %b %d, %Y')}")
with c_clock:
    st.markdown(f'<div class="metric-card"><b>{now.strftime("%H:%M:%S")}</b></div>', unsafe_allow_html=True)

# --- 6. DASHBOARD METRICS ---
m1, m2, m3, m4 = st.columns(4)
done_tasks = len([t for t in st.session_state.tasks if t.get('status') == 'Done'])

with m1: st.markdown(f'<div class="metric-card"><span>Tasks Done</span><h3>{done_tasks}</h3></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="metric-card"><span>Water Log</span><h3>{st.session_state.water_ml}ml</h3></div>', unsafe_allow_html=True)
with m3: st.markdown('<div class="metric-card"><span>Focus Time</span><h3>2.4h</h3></div>', unsafe_allow_html=True)
with m4: st.markdown('<div class="metric-card"><span>Streak</span><h3>12</h3></div>', unsafe_allow_html=True)

# --- 7. SMART AI SUGGESTIONS ---
st.markdown("### ✨ Smart Suggestions")
for s in get_smart_suggestions():
    col_s1, col_s2 = st.columns([5, 1])
    col_s1.markdown(f"""
        <div class="suggestion-box">
            <strong>{s['title']}</strong> <span class="badge-ai">AI</span><br>
            <small>{s['desc']}</small>
        </div>
        """, unsafe_allow_html=True)
    if col_s2.button("Add", key=s['title']):
        st.session_state.tasks.append({"name": s['title'], "cat": s['cat'], "time": curr_time_hm, "status": "Pending"})
        st.rerun()

# --- 8. REMINDERS & SCHEDULING ---
st.markdown("---")
st.subheader("📋 Scheduled Reminders")

if not st.session_state.tasks:
    st.info("No reminders set yet. Use the expander below or AI suggestions!")

# Display Tasks
for i, t in enumerate(st.session_state.tasks):
    if t['status'] == 'Pending':
        col_t1, col_t2 = st.columns([5, 1])
        col_t1.info(f"**{t['time']}** — {t['name']} ({t['cat']})")
        if col_t2.button("Done", key=f"d_{i}"):
            t['status'] = 'Done'
            st.rerun()

# Add New Reminder
with st.expander("➕ Set New Manual Reminder"):
    ca, cb, cc = st.columns(3)
    r_name = ca.text_input("Reminder Name")
    r_time = cb.text_input("Time (HH:MM)", value=curr_time_hm)
    r_cat = cc.selectbox("Category", ["Work", "Study", "Health", "Personal"])
    if st.button("Schedule Alert"):
        st.session_state.tasks.append({"name": r_name, "cat": r_cat, "time": r_time, "status": "Pending"})
        st.rerun()

# --- 9. ANALYTICS ---
st.markdown("---")
st.subheader("📈 Performance Analysis")
df_week = pd.DataFrame({'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 'Tasks': [5, 4, 7, 2, 5, 8, 3]})
fig = px.bar(df_week, x='Day', y='Tasks', color_discrete_sequence=['#A7F3D0'])
# Fixed width parameter for Streamlit 2026
st.plotly_chart(fig, width='stretch')

# --- 10. NOTIFICATION ENGINE (LIVE) ---
# Water Timer: Uses total_seconds() to compare aware datetimes
time_diff = now - st.session_state.last_water_check
if time_diff.total_seconds() / 60 >= 30:
    st.toast("💧 UAE Health: Time to drink water!", icon="🥛")
    st.session_state.water_ml += 250
    st.session_state.last_water_check = now

# Scheduled Alerts
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == curr_time_hm:
        notif_id = f"{t['name']}_{curr_time_hm}"
        if notif_id not in st.session_state.notified_cache:
            st.toast(f"⏰ REMINDER: {t['name']} is starting now!", icon="🔔")
            st.session_state.notified_cache.add(notif_id)

# The Heartbeat: Reruns the script to update clock and check times
time.sleep(1)
st.rerun()
