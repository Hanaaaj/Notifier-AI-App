import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pytz
import time

# --- 1. UAE TIME SETUP ---
uae_tz = pytz.timezone('Asia/Dubai')

def get_uae_now():
    return datetime.now(uae_tz)

st.set_page_config(page_title="AuraFlow | UAE Notifier", page_icon="🔔")

# --- 2. CLEAN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .clock-display {
        font-size: 50px; font-family: 'Courier New', monospace;
        font-weight: bold; color: #1E293B; text-align: center;
        padding: 20px; background: white; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .reminder-card {
        background: white; padding: 15px; border-radius: 10px;
        border-left: 5px solid #3B82F6; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'reminders' not in st.session_state:
    st.session_state.reminders = []
if 'triggered' not in st.session_state:
    st.session_state.triggered = set() # To ensure alert only pops once

# --- 4. REAL-TIME CLOCK ---
now = get_uae_now()
curr_time = now.strftime("%H:%M") # HH:MM for matching
display_time = now.strftime("%H:%M:%S") # HH:MM:SS for display

st.markdown(f'<div class="clock-display">{display_time}</div>', unsafe_allow_html=True)

# --- 5. NOTIFICATION LOGIC ---
# This checks your list every second to see if the time matches
for r in st.session_state.reminders:
    if r['time'] == curr_time and r['active']:
        alert_id = f"{r['name']}_{curr_time}"
        if alert_id not in st.session_state.triggered:
            st.toast(f"🔔 NOTIFICATION: {r['name']}", icon="📢")
            # Trigger a simple browser beep via JS
            st.components.v1.html(
                '<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>',
                height=0
            )
            st.session_state.triggered.add(alert_id)

# Auto-Water Logic (Every 30 minutes)
if now.minute % 30 == 0 and now.second == 0:
    st.toast("💧 HYDRATION: Drink water now!", icon="🥤")

# --- 6. ADD REMINDERS & AI SORTING ---
with st.form("reminder_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    name = col1.text_input("Reminder Name")
    tm = col2.text_input("Time (HH:MM)", value=curr_time)
    cat = col3.selectbox("Importance", ["Work", "Study", "Health", "Other"])
    
    if st.form_submit_button("Set Alert"):
        st.session_state.reminders.append({
            "name": name, "time": tm, "cat": cat, "active": True
        })
        # AI-like Sorting by Category Importance
        prio = {"Work": 1, "Study": 2, "Health": 3, "Other": 4}
        st.session_state.reminders.sort(key=lambda x: prio.get(x['cat']))
        st.rerun()

# --- 7. ACTIVE REMINDERS LIST ---
st.write("### Active Alerts")
for i, r in enumerate(st.session_state.reminders):
    if r['active']:
        with st.container():
            c_a, c_b = st.columns([4, 1])
            c_a.markdown(f"""
                <div class="reminder-card">
                    <strong>{r['time']}</strong> — {r['name']} <i>({r['cat']})</i>
                </div>
                """, unsafe_allow_html=True)
            if c_b.button("Delete", key=f"del_{i}"):
                st.session_state.reminders.pop(i)
                st.rerun()

# --- 8. THE HEARTBEAT (Auto-Refresh) ---
time.sleep(1) # Refresh every 1 second
st.rerun()
