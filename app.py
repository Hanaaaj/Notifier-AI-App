import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. CONFIG & MODERN STYLING ---
st.set_page_config(page_title="MindFlow | Adaptive Intelligence", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #F8F9FB; }
    
    /* MindFlow Card Design */
    .metric-card {
        background-color: white;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        border: 1px solid #F0F2F6;
        margin-bottom: 20px;
    }
    .metric-title { color: #5F6368; font-size: 14px; font-weight: 500; }
    .metric-value { color: #1A1C1E; font-size: 32px; font-weight: 700; margin-top: 8px; }
    
    /* Smart Suggestion Styling */
    .suggestion-card {
        background-color: #FDF4FF;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #FAE8FF;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Priority Badges */
    .badge-high { background: #FEE2E2; color: #EF4444; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    .badge-ai { background: #F3E8FF; color: #7E22CE; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'water' not in st.session_state:
    st.session_state.water = 0 # in ml
if 'history' not in st.session_state:
    # Mock history for the weekly dashboard
    st.session_state.history = pd.DataFrame({
        'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'Completed': [5, 3, 6, 2, 4, 7, 0]
    })

# --- 3. SMART SUGGESTION ENGINE ---
def get_smart_suggestions():
    suggestions = []
    now = datetime.now()
    
    # 1. Screen Time Logic
    suggestions.append({"title": "Eye Rest (20/20/20)", "desc": "Look 20 feet away for 20 seconds", "type": "Health", "ai": True})
    
    # 2. Dehydration Logic
    if st.session_state.water < 1500:
        suggestions.append({"title": "Hydration Hit", "desc": "You are 500ml behind your daily goal", "type": "Health", "ai": True})
        
    # 3. Work/Study Balance
    work_tasks = [t for t in st.session_state.tasks if t['cat'] in ['Work', 'Study'] and t['status'] == 'Pending']
    if len(work_tasks) > 3:
        suggestions.append({"title": "Brief Stretch", "desc": "High workload detected. Stretch for 2 mins", "type": "Personal", "ai": True})
        
    return suggestions

# --- 4. MAIN LAYOUT: TOP BAR ---
col_head, col_btn = st.columns([4, 1])
with col_head:
    st.title("Good afternoon! 👋")
    st.caption("Here's your productivity overview")
with col_btn:
    if st.button("➕ New Reminder", use_container_width=True):
        st.toast("Feature coming soon!")

# --- 5. METRIC GRID ---
m1, m2, m3, m4 = st.columns(4)

completed_count = len([t for t in st.session_state.tasks if t['status'] == 'Done'])
with m1:
    st.markdown(f'<div class="metric-card"><span class="metric-title">✅ Tasks Done</span><div class="metric-value">{completed_count}</div></div>', unsafe_allow_html=True)
with m2:
    water_pct = min(int((st.session_state.water / 2000) * 100), 100)
    st.markdown(f'<div class="metric-card"><span class="metric-title">💧 Water Intake</span><div class="metric-value">{st.session_state.water}ml</div><small>{water_pct}% of goal</small></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><span class="metric-title">⏱️ Focus Time</span><div class="metric-value">2h 15m</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><span class="metric-title">🔥 Streak</span><div class="metric-value">12 Days</div></div>', unsafe_allow_html=True)

# --- 6. SMART SUGGESTIONS AREA ---
st.markdown("### ✨ Smart Suggestions")
for sugg in get_smart_suggestions():
    with st.container():
        c_a, c_b = st.columns([4, 1])
        with c_a:
            st.markdown(f"""
                <div class="suggestion-card">
                    <div>
                        <strong>{sugg['title']}</strong> <span class="badge-ai">✨ AI</span><br>
                        <small>{sugg['desc']}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with c_b:
            if st.button("Add", key=sugg['title']):
                st.session_state.tasks.append({"name": sugg['title'], "cat": sugg['type'], "status": "Pending", "time": "Now"})
                st.rerun()

# --- 7. TASK MANAGER ---
st.markdown("### 📋 Daily Tasks")
cat_filter = st.tabs(["All", "💼 Work", "📚 Study", "🏥 Health", "👤 Personal"])

# Mock input for demo
with st.expander("➕ Quick Add Task"):
    t_name = st.text_input("Task name")
    t_cat = st.selectbox("Category", ["Work", "Study", "Health", "Personal"])
    if st.button("Create Task"):
        st.session_state.tasks.append({"name": t_name, "cat": t_cat, "status": "Pending", "time": "Today"})
        st.rerun()

# Task List Display
if not st.session_state.tasks:
    st.info("No tasks yet. Use the Smart Suggestions or Quick Add!")
else:
    for i, task in enumerate(st.session_state.tasks):
        with st.container():
            t_col1, t_col2 = st.columns([5, 1])
            t_col1.write(f"**{task['name']}** ({task['cat']})")
            if task['status'] == 'Pending':
                if t_col2.button("Done", key=f"btn_{i}"):
                    st.session_state.tasks[i]['status'] = 'Done'
                    st.rerun()
            else:
                t_col2.write("✅")

# --- 8. ANALYSIS DASHBOARD ---
st.markdown("---")
st.markdown("### 📈 Analytics Dashboard")
tab_week, tab_month = st.tabs(["Weekly Progress", "Monthly Analysis"])

with tab_week:
    fig = px.bar(st.session_state.history, x='Day', y='Completed', 
                 title="Tasks Completed this Week",
                 color_discrete_sequence=['#A7F3D0'])
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis_showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

with tab_month:
    st.write("#### AI Monthly Insights")
    st.info("AI Analysis: You are 15% more productive on Tuesday mornings. Consider scheduling your deep work then.")
    
# --- 9. HYDRATION QUICK ACTION ---
st.sidebar.markdown("### 💧 Hydration Tracker")
add_water = st.sidebar.select_slider("Add water (ml)", options=[250, 500, 750])
if st.sidebar.button("Log Water"):
    st.session_state.water += add_water
    st.sidebar.success(f"Added {add_water}ml!")
    st.rerun()
