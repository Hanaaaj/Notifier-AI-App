import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json
import time
from datetime import datetime

# --- 1. INITIALIZATION & STYLING ---
st.set_page_config(page_title="AuraFlow: Adaptive Intelligence", page_icon="🧠", layout="wide")

# Modern Professional CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .metric-card { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 20px; border: 1px solid #333; }
    .badge { background: linear-gradient(45deg, #4facfe, #00f2fe); color: black; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin: 2px; font-size: 0.8rem; display: inline-block; }
    .aura-box { border-radius: 50%; width: 80px; height: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 40px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE (The Memory) ---
if 'tasks' not in st.session_state:
    # Pre-loaded mock data for "Zero Instruction" visual impact
    st.session_state.tasks = [
        {"name": "Morning Sync", "cat": "Work", "status": "Done", "time": "09:00"},
        {"name": "Water Intake", "cat": "Hydration", "status": "Done", "time": "10:30"}
    ]
if 'stats' not in st.session_state:
    st.session_state.stats = {"completed": 2, "missed": 0, "water": 1, "ignore_count": 0}
if 'mood' not in st.session_state:
    st.session_state.mood = "Neutral"
if 'badges' not in st.session_state:
    st.session_state.badges = ["Quick Starter"]

# --- 3. CORE ENGINES (Logic Layer) ---

def notify(title, body):
    """Native Browser Notification Bridge"""
    js = f"""<script>
    if (Notification.permission === 'granted') {{ new Notification("{title}", {{body: "{body}"}}); }}
    else {{ Notification.requestPermission(); }}
    </script>"""
    st.components.v1.html(js, height=0)

def ai_coach(score, mood, mode="tip"):
    """Prompt Engineering: Adaptive Feedback"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        if mode == "tip":
            prompt = f"Productivity {score}%, Mood {mood}. Give a 1-sentence smart advice."
        else:
            prompt = f"Create a short 1-sentence sarcastic encouragement for a high-achiever."
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Keep the momentum going! You're doing great."

# --- 4. SIDEBAR (The Aura Heartbeat) ---
with st.sidebar:
    st.title("🌊 AuraFlow")
    
    # Calculate Metrics
    total = st.session_state.stats["completed"] + st.session_state.stats["missed"]
    score = int((st.session_state.stats["completed"] / total * 100)) if total > 0 else 100
    
    # Aura Visual State Engine
    aura_icon = "🌊"
    aura_color = "#4facfe"
    aura_msg = "Balanced State"
    
    if st.session_state.mood == "Stressed":
        aura_icon, aura_color, aura_msg = "🔥", "#ff4b4b", "High Stress Alert"
    elif score > 80:
        aura_icon, aura_color, aura_msg = "🌟", "#00ffa3", "Flow State Active"

    st.markdown(f"""
        <div class="aura-box" style="border: 4px solid {aura_color}; box-shadow: 0 0 15px {aura_color};">
            {aura_icon}
        </div>
        <p style="text-align: center; color: {aura_color}; font-weight: bold; margin-top: 10px;">{aura_msg}</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.session_state.mood = st.select_slider("Current Mood", ["Relaxed", "Neutral", "Stressed"])
    
    if st.button("🔔 Enable Desktop Alerts"):
        st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)

# --- 5. MAIN INTERFACE ---
tabs = st.tabs(["🎯 Productivity Hub", "📈 Analytics Dashboard", "🏆 Achievements"])

# TAB 1: TASK & ADAPTIVE REMINDERS
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Schedule Intent")
        with st.form("task_form"):
            name = st.text_input("What's the goal?")
            cat = st.selectbox("Category", ["Work", "Hydration", "Break"])
            if st.form_submit_button("Add Task"):
                st.session_state.tasks.append({"name": name, "cat": cat, "status": "Pending", "time": datetime.now().strftime("%H:%M")})
                st.rerun()
                
    with col2:
        st.subheader("Adaptive Queue")
        for i, t in enumerate(st.session_state.tasks):
            if t['status'] == "Pending":
                # Adaptive logic: Check if user is ignoring
                urgency = "⚠️ URGENT" if st.session_state.stats["ignore_count"] > 2 else "🔔 Normal"
                with st.expander(f"{urgency}: {t['name']}"):
                    c_a, c_b = st.columns(2)
                    if c_a.button("Complete", key=f"done{i}"):
                        st.session_state.tasks[i]['status'] = "Done"
                        st.session_state.stats["completed"] += 1
                        if t['cat'] == "Hydration": st.session_state.stats["water"] += 1
                        st.session_state.stats["ignore_count"] = 0
                        st.balloons()
                        st.rerun()
                    if c_b.button("Snooze", key=f"snooze{i}"):
                        st.session_state.stats["ignore_count"] += 1
                        notify("Task Snoozed", "Urgency level increasing for next reminder.")
                        st.rerun()

# TAB 2: DYNAMIC ANALYTICS
with tabs[1]:
    st.subheader("Productivity Intelligence")
    m1, m2, m3 = st.columns(3)
    m1.metric("Score", f"{score}%")
    m2.metric("Completed", st.session_state.stats["completed"])
    m3.metric("Water Intake", f"{st.session_state.stats['water']} Cups")
    
    # Data Storytelling Chart
    df = pd.DataFrame([
        {"Metric": "Done", "Value": st.session_state.stats["completed"]},
        {"Metric": "Missed/Snoozed", "Value": st.session_state.stats["ignore_count"]}
    ])
    fig = px.pie(df, values='Value', names='Metric', hole=0.5, color_discrete_sequence=['#00ffa3', '#ff4b4b'])
    st.plotly_chart(fig, use_container_width=True)
    
    # Smart Feedback
    st.info(f"**AI Coach:** {ai_coach(score, st.session_state.mood)}")

# TAB 3: GAMIFICATION
with tabs[2]:
    st.subheader("Unlocked Badges")
    # Check for new badges
    if st.session_state.stats["water"] >= 3 and "Hydration Hero" not in st.session_state.badges:
        st.session_state.badges.append("Hydration Hero")
    
    if not st.session_state.badges:
        st.write("Complete tasks to earn achievements!")
    else:
        for badge in st.session_state.badges:
            st.markdown(f'<span class="badge">🏆 {badge}</span>', unsafe_allow_html=True)

# --- 6. BACKGROUND TICKER SIMULATION ---
# This would normally run in a thread; here it checks time-based matches
now = datetime.now().strftime("%H:%M")
for t in st.session_state.tasks:
    if t['status'] == "Pending" and t['time'] == now:
        notify(f"Time for {t['name']}", f"Category: {t['cat']}")
