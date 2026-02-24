import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="AuraFlow: Adaptive Intelligence", page_icon="🧠", layout="wide")

# Custom Styling for "Gamification" and "Mood"
st.markdown("""
    <style>
    .badge { background: #4facfe; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-right: 5px; }
    .mood-card { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ADVANCED SESSION STATE (The App's Memory) ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"completed": 0, "missed": 0, "water": 0, "ignore_count": 0}
if 'mood' not in st.session_state:
    st.session_state.mood = "Neutral"
if 'badges' not in st.session_state:
    st.session_state.badges = []

# --- 3. THE "ADAPTIVE" ENGINE (Logic Layer) ---
def get_adaptive_priority(task_type):
    # Rule-based AI: Increase urgency if user is ignoring reminders
    if st.session_state.stats["ignore_count"] >= 3:
        return "⚠️ HIGH URGENCY: You've missed several alerts!"
    if st.session_state.mood == "Stressed":
        return "🌸 TAKE IT SLOW: Focus on one thing at a time."
    return f"Standard {task_type} Alert"

def check_achievements():
    if st.session_state.stats["water"] >= 5 and "Hydration Hero" not in st.session_state.badges:
        st.session_state.badges.append("Hydration Hero")
    if st.session_state.stats["completed"] >= 5 and "Task Master" not in st.session_state.badges:
        st.session_state.badges.append("Task Master")

# --- 4. MAIN UI ---
st.title("🌊 AuraFlow: Adaptive Intelligence")

# Header: Mood & Badges
c1, c2 = st.columns([1, 2])
with c1:
    st.session_state.mood = st.select_slider("How is your stress level?", ["Relaxed", "Neutral", "Stressed"])
with c2:
    st.write("### Your Achievements")
    if not st.session_state.badges: st.write("No badges yet. Start your day!")
    for b in st.session_state.badges:
        st.markdown(f'<span class="badge">🏆 {b}</span>', unsafe_allow_html=True)

st.markdown("---")
tabs = st.tabs(["🎯 Productivity Hub", "📈 Insight Dashboard", "🤖 AI Coach"])

# --- TAB 1: PRODUCTIVITY HUB ---
with tabs[0]:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Add Task")
        name = st.text_input("Task Name")
        category = st.selectbox("Type", ["Work", "Hydration", "Break"])
        if st.button("Add to Queue"):
            st.session_state.tasks.append({"name": name, "cat": category, "status": "Pending", "time": datetime.now()})
            st.toast("Task added to adaptive engine.")

    with col_b:
        st.subheader("Live Queue")
        for i, t in enumerate(st.session_state.tasks):
            if t['status'] == "Pending":
                priority = get_adaptive_priority(t['cat'])
                st.warning(f"{priority}\n\n**{t['name']}**")
                if st.button(f"Done", key=f"d{i}"):
                    st.session_state.tasks[i]['status'] = "Done"
                    st.session_state.stats["completed"] += 1
                    if t['cat'] == "Hydration": st.session_state.stats["water"] += 1
                    st.session_state.stats["ignore_count"] = 0
                    check_achievements()
                    st.rerun()
                if st.button(f"Snooze", key=f"s{i}"):
                    st.session_state.stats["ignore_count"] += 1
                    st.rerun()

# --- TAB 2: DYNAMIC DASHBOARD (Data Storytelling) ---
with tabs[1]:
    total = st.session_state.stats["completed"] + st.session_state.stats["missed"]
    score = int((st.session_state.stats["completed"] / total * 100)) if total > 0 else 0
    
    st.subheader("Data Insights")
    st.metric("Productivity Score", f"{score}%", delta="Adaptive Calculation")
    
    # "Storytelling" Insight
    if st.session_state.stats["water"] < st.session_state.stats["completed"]:
        st.error("📊 **Insight:** Your Work focus is high, but your Hydration is lagging. This may lead to an afternoon crash!")
    elif score > 80:
        st.success("📊 **Insight:** You are in a 'Flow State'. Keep this momentum!")

    if total > 0:
        fig = px.bar(x=["Done", "Snoozed"], y=[st.session_state.stats["completed"], st.session_state.stats["ignore_count"]], 
                     title="Action Habits", color_discrete_sequence=['#4facfe'])
        st.plotly_chart(fig)

# --- TAB 3: AI COACH (Smart Feedback Engine) ---
with tabs[2]:
    st.subheader("Personal AI Assistant")
    if st.button("Generate Performance Analysis"):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            Analyze this productivity data: 
            Score: {score}%, Completed: {st.session_state.stats['completed']}, 
            Water: {st.session_state.stats['water']}, Mood: {st.session_state.mood}.
            Give a 2-sentence context-aware piece of advice.
            """
            st.write(model.generate_content(prompt).text)
        except:
            st.write("You're doing great! Keep balancing your hydration with your workload.")
