import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime
import time

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="AuraFlow: Adaptive Intelligence", page_icon="🧠", layout="wide")

# Custom Styling for "Aura", "Badges", and "Gradients"
st.markdown("""
    <style>
    .badge { background: linear-gradient(45deg, #4facfe, #00f2fe); color: black; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-right: 5px; font-size: 0.8rem;}
    .aura-container { text-align: center; padding: 20px; border-radius: 15px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #4facfe , #00f2fe); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ADVANCED SESSION STATE ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"completed": 0, "missed": 0, "water": 0, "ignore_count": 0}
if 'mood' not in st.session_state:
    st.session_state.mood = "Neutral"
if 'badges' not in st.session_state:
    st.session_state.badges = []

# --- 3. INTELLIGENCE ENGINES ---

def get_ai_response(prompt):
    """Universal AI connector for Briefings and Coaching"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except:
        return "I'm here to support your focus. Keep going!"

def get_adaptive_priority(task_type, snooze_count):
    if snooze_count >= 3:
        return "🔥 CRITICAL: High procrastination detected. Focus now!"
    if st.session_state.mood == "Stressed":
        return "🌸 CALM: Gentle reminder. One step at a time."
    return f"Standard {task_type} Alert"

# --- 4. SIDEBAR: THE AURA HEARTBEAT ---
with st.sidebar:
    st.title("🌊 AuraFlow")
    
    # Calculate Score for Visuals
    total = st.session_state.stats["completed"] + st.session_state.stats["ignore_count"]
    score = int((st.session_state.stats["completed"] / total * 100)) if total > 0 else 100
    
    # Visual State Engine
    aura_emoji = "🌊"
    aura_label = "Balanced"
    if st.session_state.mood == "Stressed":
        aura_emoji, aura_label = "🔥", "High Energy/Stress"
    elif score > 80:
        aura_emoji, aura_label = "🌟", "Flow State"
        
    st.markdown(f"""
        <div class="aura-container">
            <h1 style="font-size: 60px; margin: 0;">{aura_emoji}</h1>
            <p style="font-weight: bold; color: #4facfe;">{aura_label} Mode</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.session_state.mood = st.select_slider("Current Stress Level", ["Relaxed", "Neutral", "Stressed"])
    
    if st.button("🔔 Test System Alerts"):
        st.toast("System ready. Desktop notifications active.")

# --- 5. MAIN UI LAYOUT ---
c1, c2 = st.columns([2, 1])
with c1:
    st.title("Adaptive Intelligence Dashboard")
with c2:
    st.write("### Achievements")
    for b in st.session_state.badges:
        st.markdown(f'<span class="badge">🏆 {b}</span>', unsafe_allow_html=True)

tabs = st.tabs(["🎯 Focus Hub", "📊 Data Storytelling", "🤖 AI Coach"])

# --- TAB 1: FOCUS HUB (With Anti-Procrastination) ---
with tabs[0]:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("New Intent")
        with st.form("add_task"):
            name = st.text_input("Task/Meeting Name")
            category = st.selectbox("Type", ["Work", "Meeting", "Hydration"])
            if st.form_submit_button("Add to Engine"):
                st.session_state.tasks.append({"name": name, "cat": category, "status": "Pending", "snoozes": 0})
                st.rerun()

    with col_b:
        st.subheader("Smart Queue")
        for i, t in enumerate(st.session_state.tasks):
            if t['status'] == "Pending":
                priority = get_adaptive_priority(t['cat'], t['snoozes'])
                st.info(f"**{priority}**\n\n{t['name']}")
                
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                if btn_col1.button("Done", key=f"d{i}"):
                    st.session_state.tasks[i]['status'] = "Done"
                    st.session_state.stats["completed"] += 1
                    if t['cat'] == "Hydration": st.session_state.stats["water"] += 1
                    if st.session_state.stats["completed"] >= 5: st.session_state.badges.append("Task Master")
                    st.balloons()
                    st.rerun()
                
                if btn_col2.button("Snooze", key=f"s{i}"):
                    st.session_state.tasks[i]['snoozes'] += 1
                    st.session_state.stats["ignore_count"] += 1
                    st.rerun()
                
                # FEATURE: Anti-Procrastination/Briefing Bridge
                if t['cat'] == "Meeting":
                    if btn_col3.button("Briefing", key=f"b{i}"):
                        brief = get_ai_response(f"I have a meeting called {t['name']}. Give me 2 prep tips.")
                        st.write(f"📝 {brief}")
                elif t['snoozes'] >= 2:
                    if btn_col3.button("Help Me Start", key=f"h{i}"):
                        nudge = get_ai_response(f"The user is procrastinating on '{t['name']}'. Give a 1-sentence micro-step to start.")
                        st.warning(f"💡 {nudge}")

# --- TAB 2: DATA STORYTELLING ---
with tabs[1]:
    st.subheader("Behavioral Analysis")
    m1, m2 = st.columns(2)
    m1.metric("Efficiency Score", f"{score}%")
    m2.metric("Hydration", f"{st.session_state.stats['water']} Cups")
    
    # Data Insight Engine
    if st.session_state.stats["ignore_count"] > st.session_state.stats["completed"]:
        st.error("📊 **Insight:** You're snoozing more than doing. Try the 'Help Me Start' button in the Focus Hub.")
    elif st.session_state.stats["water"] < 3:
        st.warning("📊 **Insight:** Hydration is low. Scientific data suggests this increases fatigue by 20%.")

    if total > 0:
        fig = px.bar(x=["Completed", "Snoozed"], y=[st.session_state.stats["completed"], st.session_state.stats["ignore_count"]], 
                     title="Task Velocity", color_discrete_sequence=['#4facfe'])
        st.plotly_chart(fig)

# --- TAB 3: AI COACH ---
with tabs[2]:
    st.subheader("Adaptive Feedback")
    if st.button("Run Full Session Review"):
        prompt = f"Data: Score {score}%, Mood {st.session_state.mood}, Water {st.session_state.stats['water']}. Give a smart 2-sentence feedback."
        st.success(get_ai_response(prompt))
