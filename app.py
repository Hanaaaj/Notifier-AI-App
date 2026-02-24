import streamlit as st
import google.generativeai as genai
import json
import time
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. INITIALIZATION & UI THEME ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'score' not in st.session_state:
    st.session_state.score = 100

st.set_page_config(page_title="AuraFlow Pro", page_icon="🌊", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px; border-radius: 15px; border: 1px solid #444;
        text-align: center;
    }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00f2fe, #4facfe); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE NOTIFICATION & SMART FEEDBACK ENGINE ---
def notify(title, body):
    js = f"""<script>
    if (Notification.permission === "granted") {{
        new Notification("{title}", {{ body: "{body}" }});
    }} else {{ Notification.requestPermission(); }}
    </script>"""
    st.components.v1.html(js, height=0)

def ai_brain(user_text, mode="parse"):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        if mode == "parse":
            prompt = f"Return ONLY JSON: {{'task': str, 'mins': int, 'type': 'Work'|'Hydration', 'tip': str}}. Input: {user_text}"
        else:
            prompt = f"Give a 1-sentence sarcastic but motivating feedback for someone with a productivity score of {st.session_state.score}%."
        
        response = model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '')) if mode == "parse" else response.text
    except:
        return {"task": "Focus Session", "mins": 25, "type": "Work", "tip": "Just start!"} if mode == "parse" else "Keep pushing!"

# --- 3. SIDEBAR (Professor Control Panel) ---
with st.sidebar:
    st.title("Settings")
    if st.button("🔔 Reset Notification Permissions"):
        st.components.v1.html("<script>Notification.requestPermission();</script>", height=0)
    
    st.markdown("---")
    st.write("### AI Smart Feedback")
    if st.button("Get AI Performance Review"):
        st.info(ai_brain("", mode="feedback"))

# --- 4. MAIN DASHBOARD ---
st.title("🌊 AuraFlow Intelligence")
t1, t2, t3 = st.tabs(["🎯 Focus Room", "📊 Analytics", "📜 Logs"])

with t1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        u_input = st.text_input("What are we doing?", placeholder="e.g. Work on thesis for 40 mins")
        if st.button("🚀 Start Intelligent Timer"):
            data = ai_brain(u_input)
            st.session_state.active_task = data
            st.session_state.start_time = time.time()
            notify("AuraFlow Started", f"Timer set for {data['task']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.metric("Productivity Score", f"{st.session_state.score}%", delta="Live")
        if 'active_task' in st.session_state:
            if st.button("✅ Mark as Complete"):
                st.session_state.history.append({
                    "Task": st.session_state.active_task['task'],
                    "Type": st.session_state.active_task['type'],
                    "Time": datetime.now().strftime("%H:%M"),
                    "Status": "Completed"
                })
                st.session_state.score = min(100, st.session_state.score + 5)
                st.success("Task Logged!")
                del st.session_state.active_task

with t2:
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df, names='Type', title="Task Distribution", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.write("### Activity Density")
            st.bar_chart(df['Type'].value_counts())
    else:
        st.info("No data yet. Complete a task to see analytics!")

with t3:
    st.table(st.session_state.history if st.session_state.history else pd.DataFrame(columns=["Task", "Type", "Time", "Status"]))

# --- 5. BACKGROUND TICKER ---
if 'active_task' in st.session_state:
    st.toast(f"Current Focus: {st.session_state.active_task['task']}")
