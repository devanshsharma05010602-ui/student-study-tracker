"""
app.py
------
Main entry point for the Student Study & Progress Tracker.
Run with:  streamlit run app.py

Concepts demonstrated:
  - Streamlit web framework
  - Session state management
  - Functions and OOP (via models.py)
  - Data persistence (JSON, CSV)
  - Matplotlib charts
  - Pandas DataFrames
"""

# NOTE: If your IDE flags 'streamlit' as unresolved, select the correct
#       Python interpreter (the one where you ran 'pip install -r requirements.txt').
#       In VS Code: Ctrl+Shift+P → "Python: Select Interpreter"
import streamlit as st           # type: ignore[import]
import matplotlib.pyplot as plt  # type: ignore[import]
import matplotlib.patches as mpatches  # type: ignore[import]
import pandas as pd              # type: ignore[import]

from models    import StudyTask
from functions import (
    load_data, save_data,
    load_settings, save_settings,
    add_subject, remove_subject,
    add_task, update_task_status, delete_task,
    clear_completed_tasks, mark_all_tasks,
    search_tasks, filter_tasks,
    get_summary_stats, get_all_subject_progress,
    export_tasks_csv, export_data_json,
    get_priority_summary,
)
from auth import register_user, login_user

# ================================================================== #
#  Page Configuration                                                  #
# ================================================================== #

st.set_page_config(
    page_title = "Student Study & Progress Tracker",
    page_icon  = "📚",
    layout     = "wide",
    initial_sidebar_state = "collapsed",
)

# ================================================================== #
#  Custom CSS                                                          #
# ================================================================== #

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
.block-container { padding-top: 1rem !important; }

/* ---- App header ---- */
.app-header {
    background: linear-gradient(135deg, #0d0d1a 0%, #12122b 40%, #1a1050 100%);
    padding: 1.8rem 2.5rem 1.6rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    text-align: center;
    border: 1px solid rgba(138, 92, 246, 0.4);
    box-shadow: 0 8px 32px rgba(138, 92, 246, 0.15);
}
.app-header .tagline-badge {
    display: inline-block;
    background: rgba(138,92,246,0.2);
    border: 1px solid rgba(138,92,246,0.4);
    color: #c4b5fd;
    font-size: 0.73rem;
    font-weight: 600;
    padding: 0.2rem 0.8rem;
    border-radius: 999px;
    margin-bottom: 0.6rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.app-header h1 {
    color: #ffffff;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
    text-shadow: 0 0 30px rgba(138,92,246,0.5);
}
.app-header .sub-info {
    color: #94a3b8;
    font-size: 0.88rem;
    margin: 0;
}
.app-header .sub-info span { color: #c4b5fd; font-weight: 600; }

/* ---- Metric cards ---- */
.metric-card {
    background: linear-gradient(145deg, #1e1b4b, #1a1a3e);
    border: 1px solid rgba(138,92,246,0.25);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: default;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(138,92,246,0.2); }
.metric-card .metric-icon { font-size: 1.5rem; margin-bottom: 0.35rem; }
.metric-card .metric-value {
    font-size: 2.3rem; font-weight: 800; line-height: 1; margin-bottom: 0.25rem;
    background: linear-gradient(135deg,#a78bfa,#818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-card .metric-value.green  { background: linear-gradient(135deg,#4ade80,#22c55e);  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.metric-card .metric-value.amber  { background: linear-gradient(135deg,#fbbf24,#f59e0b);  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.metric-card .metric-value.blue   { background: linear-gradient(135deg,#60a5fa,#3b82f6);  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.metric-card .metric-value.rose   { background: linear-gradient(135deg,#f472b6,#ec4899);  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.metric-card .metric-label { font-size: 0.78rem; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.4px; }

/* ---- Section title ---- */
.section-title {
    font-size: 0.82rem; font-weight: 700; color: #a78bfa;
    border-bottom: 1px solid rgba(138,92,246,0.3);
    padding-bottom: 0.4rem; margin-bottom: 0.9rem;
    letter-spacing: 0.8px; text-transform: uppercase;
}

/* ---- Task row ---- */
.task-row {
    background: linear-gradient(145deg,#1e1b4b,#1a1a3e);
    border: 1px solid rgba(138,92,246,0.2);
    border-radius: 10px;
    padding: 0.65rem 1.1rem;
    margin-bottom: 0.45rem;
    display: flex; align-items: center; gap: 0.8rem;
    color: #e2e8f0; transition: background 0.15s;
}
.task-row:hover { background: linear-gradient(145deg,#252257,#211e50); }
.task-done    { border-left: 4px solid #22c55e; }
.task-pending { border-left: 4px solid #f59e0b; }

/* ---- Priority badges ---- */
.badge { font-size:0.67rem; padding:0.18rem 0.55rem; border-radius:999px; font-weight:700; letter-spacing:0.4px; text-transform:uppercase; }
.badge-high   { background:rgba(239,68,68,0.15);  color:#f87171; border:1px solid rgba(239,68,68,0.4); }
.badge-medium { background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.4); }
.badge-low    { background:rgba(34,197,94,0.15);  color:#4ade80; border:1px solid rgba(34,197,94,0.4); }

/* ---- Subject card ---- */
.subject-card {
    background: linear-gradient(145deg,#1e1b4b,#1a1a3e);
    border: 1px solid rgba(138,92,246,0.22);
    border-radius: 12px; padding: 0.9rem 1.2rem; margin-bottom: 0.55rem;
}
.subject-name  { font-weight: 700; color: #e2e8f0; font-size: 0.95rem; }
.subject-stats { color: #94a3b8; font-size: 0.8rem; margin-top: 0.12rem; }

/* ---- Settings card ---- */
.settings-card {
    background: linear-gradient(145deg,#1e1b4b,#1a1a3e);
    border: 1px solid rgba(138,92,246,0.22);
    border-radius: 14px; padding: 1.3rem 1.5rem; margin-bottom: 1rem;
}
.settings-card-title {
    font-size: 0.95rem; font-weight: 700; color: #c4b5fd;
    margin-bottom: 0.15rem;
}
.settings-card-desc {
    font-size: 0.8rem; color: #64748b; margin-bottom: 1rem;
}

/* ---- Info box ---- */
.info-box { background:rgba(96,165,250,0.08); border:1px solid rgba(96,165,250,0.3); border-radius:10px; padding:0.8rem 1rem; color:#93c5fd; font-size:0.87rem; }
.warn-box { background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.3); border-radius:10px; padding:0.8rem 1rem; color:#fbbf24; font-size:0.87rem; }
.danger-box { background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:0.8rem 1rem; color:#f87171; font-size:0.87rem; }
.success-box { background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.3); border-radius:10px; padding:0.8rem 1rem; color:#4ade80; font-size:0.87rem; }

/* ---- Divider ---- */
.divider { border:none; border-top:1px solid rgba(138,92,246,0.13); margin:1.1rem 0; }

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] { gap:0.4rem; background:#0d0d1a; border-radius:10px; padding:0.3rem; }
.stTabs [data-baseweb="tab"] { border-radius:8px; font-weight:600; font-size:0.86rem; color:#94a3b8 !important; padding:0.45rem 1rem; transition:all 0.2s; }
.stTabs [aria-selected="true"] { background:rgba(138,92,246,0.25) !important; color:#c4b5fd !important; border-bottom:none !important; }

/* ---- Buttons ---- */
.stButton > button {
    background: linear-gradient(135deg,#7c3aed,#6d28d9);
    color:white; border:none; border-radius:9px;
    padding:0.45rem 1.4rem; font-weight:600; font-size:0.87rem;
    transition:all 0.2s; box-shadow:0 4px 12px rgba(109,40,217,0.3);
}
.stButton > button:hover { background:linear-gradient(135deg,#6d28d9,#5b21b6); transform:translateY(-1px); color:white; }

/* ---- Logout button override — small red pill ---- */
[data-testid="stBaseButton-secondary"][kind="secondary"]:has-text("Logout"),
div[data-testid="column"]:last-child .stButton > button {
    background: rgba(239,68,68,0.1) !important;
    border: 1px solid rgba(239,68,68,0.35) !important;
    color: #f87171 !important;
    border-radius: 999px !important;
    padding: 0.25rem 0.9rem !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
    background: rgba(239,68,68,0.22) !important;
    border-color: rgba(239,68,68,0.55) !important;
    transform: none !important;
    color: #fca5a5 !important;
}

/* ---- Progress bar ---- */
.stProgress > div > div { background:rgba(138,92,246,0.15) !important; }
.stProgress > div > div > div { background:linear-gradient(90deg,#7c3aed,#818cf8) !important; }

/* ---- Goal indicator ---- */
.goal-chip {
    display:inline-flex; align-items:center; gap:0.4rem;
    background:rgba(138,92,246,0.15); border:1px solid rgba(138,92,246,0.3);
    color:#c4b5fd; font-size:0.8rem; font-weight:600;
    padding:0.3rem 0.8rem; border-radius:999px;
}
.goal-chip.on-track  { background:rgba(34,197,94,0.12);  border-color:rgba(34,197,94,0.3);  color:#4ade80; }
.goal-chip.off-track { background:rgba(251,191,36,0.12); border-color:rgba(251,191,36,0.3); color:#fbbf24; }

/* ---- Hide Streamlit Deploy button & top toolbar ---- */
[data-testid="stDeployButton"]      { display: none !important; }
[data-testid="stToolbar"]           { display: none !important; }
#MainMenu                           { display: none !important; }
header[data-testid="stHeader"]      { display: none !important; }

/* ================================================================ */
/*  Login / Register Page Styles                                     */
/* ================================================================ */

/* Fullscreen auth wrapper */
.auth-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(ellipse at 20% 50%, rgba(109,40,217,0.18) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.15) 0%, transparent 55%),
                linear-gradient(135deg, #050510 0%, #0d0d1a 50%, #0a0a18 100%);
    padding: 2rem 1rem;
}

/* Card */
.auth-card {
    background: linear-gradient(145deg, #13132a, #0f0f22);
    border: 1px solid rgba(138,92,246,0.35);
    border-radius: 24px;
    padding: 2.8rem 3rem;
    width: 100%;
    max-width: 460px;
    margin: 0 auto;
    box-shadow: 0 25px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(138,92,246,0.08), inset 0 1px 0 rgba(255,255,255,0.04);
    position: relative;
    overflow: hidden;
}
.auth-card::before {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(109,40,217,0.18) 0%, transparent 70%);
    pointer-events: none;
}

/* Logo area */
.auth-logo {
    text-align: center;
    margin-bottom: 1.8rem;
}
.auth-logo .logo-icon {
    font-size: 3rem;
    display: block;
    filter: drop-shadow(0 0 20px rgba(138,92,246,0.6));
    margin-bottom: 0.5rem;
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}
.auth-logo h2 {
    color: #ffffff;
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0 0 0.2rem 0;
    letter-spacing: -0.4px;
    background: linear-gradient(135deg, #c4b5fd, #a78bfa, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.auth-logo p {
    color: #64748b;
    font-size: 0.84rem;
    margin: 0;
}

/* Tab switcher */
.auth-tabs {
    display: flex;
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 1.6rem;
    border: 1px solid rgba(138,92,246,0.15);
}
.auth-tab {
    flex: 1;
    text-align: center;
    padding: 0.5rem;
    border-radius: 7px;
    font-weight: 600;
    font-size: 0.87rem;
    cursor: pointer;
    color: #64748b;
    transition: all 0.2s;
}
.auth-tab.active {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(109,40,217,0.35);
}

/* Form labels */
.auth-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    display: block;
}

/* Auth messages */
.auth-error   { background:rgba(239,68,68,0.1);  border:1px solid rgba(239,68,68,0.35);  border-radius:10px; padding:0.7rem 1rem; color:#f87171; font-size:0.86rem; margin-bottom:0.8rem; }
.auth-success { background:rgba(34,197,94,0.1);  border:1px solid rgba(34,197,94,0.35);  border-radius:10px; padding:0.7rem 1rem; color:#4ade80; font-size:0.86rem; margin-bottom:0.8rem; }
.auth-info    { background:rgba(96,165,250,0.08); border:1px solid rgba(96,165,250,0.3);  border-radius:10px; padding:0.7rem 1rem; color:#93c5fd; font-size:0.86rem; margin-bottom:0.8rem; }

/* Divider */
.auth-divider { border:none; border-top:1px solid rgba(138,92,246,0.12); margin:1.2rem 0; }

/* Streamlit input override (inside auth only) */
.auth-card .stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(138,92,246,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 0.9rem !important;
    transition: border 0.2s !important;
}
.auth-card .stTextInput > div > div > input:focus {
    border-color: rgba(138,92,246,0.6) !important;
    box-shadow: 0 0 0 3px rgba(138,92,246,0.12) !important;
}

/* ---- Logged-in user badge in header ---- */
.user-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(138,92,246,0.18); border: 1px solid rgba(138,92,246,0.35);
    color: #c4b5fd; font-size: 0.8rem; font-weight: 600;
    padding: 0.28rem 0.85rem; border-radius: 999px;
    vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

# ================================================================== #
#  Session State Initialisation                                        #
# ================================================================== #

# ---- Auth state ---- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in  = False
if "current_user" not in st.session_state:
    st.session_state.current_user = {}  # {username, full_name}
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode  = "login"  # 'login' | 'register'

# ================================================================== #
#  Login / Register Gate                                               #
# ================================================================== #

if not st.session_state.logged_in:
    # ---- Auth page layout ---- #
    st.markdown('<div class="auth-wrapper">', unsafe_allow_html=True)

    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_mid:
        # --- Logo ---
        st.markdown("""
        <div class="auth-logo">
            <span class="logo-icon">🎓</span>
            <h2>Study &amp; Progress Tracker</h2>
            <p>Your personal academic companion</p>
        </div>
        """, unsafe_allow_html=True)

        # --- Mode toggle ---
        tab_col1, tab_col2 = st.columns(2)
        with tab_col1:
            if st.button("🔑  Sign In", use_container_width=True, key="btn_switch_login"):
                st.session_state.auth_mode = "login"
                st.rerun()
        with tab_col2:
            if st.button("✨  Register", use_container_width=True, key="btn_switch_register"):
                st.session_state.auth_mode = "register"
                st.rerun()

        st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)

        # ============================================================ #
        #  LOGIN FORM                                                    #
        # ============================================================ #
        if st.session_state.auth_mode == "login":
            st.markdown('<p class="auth-label">Username</p>', unsafe_allow_html=True)
            login_username = st.text_input(
                "Username", placeholder="Enter your username",
                label_visibility="collapsed", key="login_username"
            )
            st.markdown('<p class="auth-label">Password</p>', unsafe_allow_html=True)
            login_password = st.text_input(
                "Password", placeholder="Enter your password",
                type="password", label_visibility="collapsed", key="login_password"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀  Sign In", use_container_width=True, key="btn_login"):
                if login_username and login_password:
                    ok, msg, user = login_user(login_username, login_password)
                    if ok:
                        st.session_state.logged_in    = True
                        st.session_state.current_user = user
                        st.rerun()
                    else:
                        st.markdown(f'<div class="auth-error">❌ {msg}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="auth-error">❌ Please fill in all fields.</div>', unsafe_allow_html=True)

            st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
            st.markdown(
                '<div class="auth-info">👋 New here? Click <strong>Register</strong> above to create an account.</div>',
                unsafe_allow_html=True
            )

        # ============================================================ #
        #  REGISTER FORM                                                 #
        # ============================================================ #
        else:
            st.markdown('<p class="auth-label">Full Name</p>', unsafe_allow_html=True)
            reg_fullname = st.text_input(
                "Full Name", placeholder="e.g. Devan Sharma",
                label_visibility="collapsed", key="reg_fullname"
            )
            st.markdown('<p class="auth-label">Username</p>', unsafe_allow_html=True)
            reg_username = st.text_input(
                "Username", placeholder="Choose a username (min 3 chars)",
                label_visibility="collapsed", key="reg_username"
            )
            st.markdown('<p class="auth-label">Password</p>', unsafe_allow_html=True)
            reg_password = st.text_input(
                "Password", placeholder="Choose a password (min 6 chars)",
                type="password", label_visibility="collapsed", key="reg_password"
            )
            st.markdown('<p class="auth-label">Confirm Password</p>', unsafe_allow_html=True)
            reg_confirm = st.text_input(
                "Confirm Password", placeholder="Re-enter your password",
                type="password", label_visibility="collapsed", key="reg_confirm"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎉  Create Account", use_container_width=True, key="btn_register"):
                if not all([reg_fullname, reg_username, reg_password, reg_confirm]):
                    st.markdown('<div class="auth-error">❌ Please fill in all fields.</div>', unsafe_allow_html=True)
                elif reg_password != reg_confirm:
                    st.markdown('<div class="auth-error">❌ Passwords do not match.</div>', unsafe_allow_html=True)
                else:
                    ok, msg = register_user(reg_username, reg_password, reg_fullname)
                    if ok:
                        st.markdown(
                            '<div class="auth-success">✅ Account created! You can now sign in.</div>',
                            unsafe_allow_html=True
                        )
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.markdown(f'<div class="auth-error">❌ {msg}</div>', unsafe_allow_html=True)

            st.markdown('<hr class="auth-divider">', unsafe_allow_html=True)
            st.markdown(
                '<div class="auth-info">🔑 Already have an account? Click <strong>Sign In</strong> above.</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()   # ← Stop rendering anything below until logged in

# ------------------------------------------------------------------ #
#  From here onward the user IS authenticated                          #
# ------------------------------------------------------------------ #

# Each user gets their own isolated data — reload when a new user logs in
_username = st.session_state.current_user.get("username", "")

if "subjects" not in st.session_state or "tasks" not in st.session_state \
        or st.session_state.get("_loaded_for") != _username:
    st.session_state.subjects, st.session_state.tasks = load_data(_username)
    st.session_state._loaded_for = _username

if "settings" not in st.session_state \
        or st.session_state.get("_settings_for") != _username:
    st.session_state.settings = load_settings(_username)
    st.session_state._settings_for = _username

# ---- Convenience aliases ---- #
subjects: list = st.session_state.subjects
tasks   : list = st.session_state.tasks
cfg     : dict = st.session_state.settings   # settings shortcut


# ================================================================== #
#  Helpers                                                             #
# ================================================================== #

def persist():
    """Save task/subject data to disk for the current user."""
    uname = st.session_state.current_user.get("username", "")
    save_data(uname, st.session_state.subjects, st.session_state.tasks)


def persist_settings():
    """Save settings to disk for the current user."""
    uname = st.session_state.current_user.get("username", "")
    save_settings(uname, st.session_state.settings)


# ================================================================== #
#  App Header  (uses student name from settings)                       #
# ================================================================== #

student_name = cfg.get("student_name", "").strip()
course       = cfg.get("course", "MCA")
semester     = cfg.get("semester", "Semester 1")

name_html = (f"<span>{student_name}</span> · " if student_name else "")

# ---- Header with compact inline logout ---- #
st.markdown(f"""
<div class="app-header">
  <h1>🎓 Student Study &amp; Progress Tracker</h1>
  <p class="sub-info">{name_html}Manage subjects · Track topics · Monitor your progress</p>
</div>
""", unsafe_allow_html=True)

# Compact logout button placed right-aligned below header
_, logout_spacer = st.columns([9, 1])
with logout_spacer:
    if st.button("🚪 Logout", key="btn_logout", use_container_width=True):
        for _key in ["subjects", "tasks", "settings", "_loaded_for", "_settings_for"]:
            st.session_state.pop(_key, None)
        st.session_state.logged_in    = False
        st.session_state.current_user = {}
        st.rerun()

# ================================================================== #
#  Navigation Tabs                                                     #
# ================================================================== #

tab_dashboard, tab_subjects, tab_tasks, tab_progress, tab_settings = st.tabs(
    ["🏠  Dashboard", "📂  Subjects", "📝  Study Tasks", "📊  Progress", "⚙️  Settings"]
)


# ================================================================== #
#  TAB 1 — Dashboard                                                   #
# ================================================================== #

with tab_dashboard:
    stats    = get_summary_stats(subjects, tasks)
    target   = cfg.get("target_completion_pct", 80)
    progress = stats["progress"]
    on_track = progress >= target

    # ---- Metric Cards ---- #
    st.markdown('<div class="section-title">📊 Overview</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "📂", stats["total_subjects"], "Total Subjects",  ""),
        (c2, "📝", stats["total_tasks"],    "Total Tasks",     ""),
        (c3, "✅", stats["completed"],      "Completed",       "green"),
        (c4, "⏳", stats["pending"],        "Pending",         "amber"),
        (c5, "🎯", f"{progress}%",          "Overall Progress","blue"),
    ]
    for col, icon, value, label, color_cls in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value {color_cls}">{value}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- Overall Progress + Goal Status ---- #
    st.markdown('<div class="section-title">🎯 Overall Progress</div>', unsafe_allow_html=True)

    if tasks:
        # Show whether student is on track for their goal
        if cfg.get("warn_below_target", True):
            chip_cls  = "on-track"  if on_track else "off-track"
            chip_icon = "✅" if on_track else "⚠️"
            chip_text = f"On track for {target}% goal" if on_track else f"Below {target}% goal"
            st.markdown(
                f'<span class="goal-chip {chip_cls}">{chip_icon} {chip_text}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

        st.progress(
            int(progress),
            text=f"**{progress}%** complete &nbsp;·&nbsp; "
                 f"{stats['completed']}/{stats['total_tasks']} tasks &nbsp;·&nbsp; "
                 f"Target: **{target}%**",
        )
    else:
        st.markdown('<div class="info-box">📌 No tasks yet — add some tasks to track progress!</div>',
                    unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- Per-Subject Progress ---- #
    st.markdown('<div class="section-title">📂 Progress by Subject</div>', unsafe_allow_html=True)
    if subjects:
        for sp in get_all_subject_progress(subjects, tasks):
            ca, cb = st.columns([2, 8])
            with ca:
                st.markdown(f"**{sp['subject']}**")
            with cb:
                pct = int(sp["percentage"])
                st.progress(pct, text=f"{sp['completed']}/{sp['total']} tasks · **{pct}%**")
    else:
        st.markdown('<div class="info-box">📌 No subjects yet.</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- Priority Breakdown ---- #
    st.markdown('<div class="section-title">🔥 Priority Breakdown</div>', unsafe_allow_html=True)
    if tasks:
        pri = get_priority_summary(tasks)
        pc1, pc2, pc3 = st.columns(3)
        for col, level, color_cls, icon in [
            (pc1, "High",   "rose",  "🔴"),
            (pc2, "Medium", "amber", "🟡"),
            (pc3, "Low",    "green", "🟢"),
        ]:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value {color_cls}">{pri[level]}</div>
                    <div class="metric-label">{level} Priority</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">📌 No tasks yet.</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- Recent Tasks ---- #
    st.markdown('<div class="section-title">🕐 Recent Tasks (Last 5)</div>', unsafe_allow_html=True)
    if tasks:
        for t in reversed(tasks[-5:]):
            icon      = "✅" if t.is_completed() else "⏳"
            css_class = "task-done" if t.is_completed() else "task-pending"
            badge_cls = f"badge-{t.priority.lower()}"
            st.markdown(f"""
            <div class="task-row {css_class}">
                <span style="font-size:1.05rem">{icon}</span>
                <span style="flex:1">
                    <strong>{t.topic}</strong>
                    &nbsp;<span style="color:#94a3b8;font-size:0.83rem">— {t.subject}</span>
                </span>
                <span class="badge {badge_cls}">{t.priority}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">📌 No tasks yet.</div>', unsafe_allow_html=True)


# ================================================================== #
#  TAB 2 — Subjects                                                    #
# ================================================================== #

with tab_subjects:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-title">➕ Add Subject</div>', unsafe_allow_html=True)
        with st.form("add_subject_form", clear_on_submit=True):
            new_subject = st.text_input("Subject Name",
                                        placeholder="e.g. Machine Learning, OS, Networks…")
            if st.form_submit_button("➕  Add Subject"):
                updated, msg = add_subject(st.session_state.subjects, new_subject)
                st.session_state.subjects = updated
                persist()
                (st.success if msg.startswith("✅") else st.error)(msg)
                st.rerun()

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            💡 <strong>Tip:</strong> Adding a subject lets you group your study tasks.
            Removing a subject will also delete all its tasks.
        </div>""", unsafe_allow_html=True)

    with col_right:
        st.markdown(
            f'<div class="section-title">📂 Current Subjects ({len(subjects)})</div>',
            unsafe_allow_html=True,
        )
        if not subjects:
            st.markdown('<div class="info-box">📌 No subjects added yet.</div>',
                        unsafe_allow_html=True)
        else:
            for sub in subjects:
                total_t = sum(1 for t in tasks if t.subject == sub)
                done_t  = sum(1 for t in tasks if t.subject == sub and t.is_completed())
                pct     = round((done_t / total_t) * 100) if total_t else 0
                s1, s2 = st.columns([6, 2])
                with s1:
                    st.markdown(f"""
                    <div class="subject-card">
                        <div class="subject-name">📖 {sub}</div>
                        <div class="subject-stats">{done_t}/{total_t} completed &nbsp;·&nbsp; {pct}%</div>
                    </div>""", unsafe_allow_html=True)
                with s2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑 Remove", key=f"remove_sub_{sub}"):
                        us, ut, msg = remove_subject(
                            st.session_state.subjects, st.session_state.tasks, sub)
                        st.session_state.subjects = us
                        st.session_state.tasks    = ut
                        persist()
                        st.success(msg)
                        st.rerun()


# ================================================================== #
#  TAB 3 — Study Tasks                                                 #
# ================================================================== #

with tab_tasks:
    # ---- Add Task ---- #
    st.markdown('<div class="section-title">➕ Add New Task</div>', unsafe_allow_html=True)

    if not subjects:
        st.warning("⚠️ Add at least one subject first (go to the Subjects tab).")
    else:
        default_pri = cfg.get("default_priority", "Medium")
        pri_opts    = ["Medium", "High", "Low"]
        pri_index   = pri_opts.index(default_pri) if default_pri in pri_opts else 0

        with st.form("add_task_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            with f1:
                sel_subject  = st.selectbox("Subject", subjects)
            with f2:
                sel_topic    = st.text_input("Topic / Task Name",
                                             placeholder="e.g. Pandas DataFrame")
            with f3:
                sel_priority = st.selectbox("Priority", pri_opts, index=pri_index)

            sel_notes = st.text_area("Notes (optional)", height=70,
                                     placeholder="Any extra notes about this topic…")

            if st.form_submit_button("➕  Add Task"):
                upd, msg = add_task(st.session_state.tasks,
                                    sel_subject, sel_topic, sel_priority, sel_notes)
                st.session_state.tasks = upd
                persist()
                (st.success if msg.startswith("✅") else st.error)(msg)
                st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- Search & Filter ---- #
    st.markdown('<div class="section-title">🔍 Search &amp; Filter</div>', unsafe_allow_html=True)
    sf1, sf2, sf3 = st.columns(3)
    with sf1:
        search_kw     = st.text_input("🔍 Search by Topic", placeholder="Type a keyword…")
    with sf2:
        filter_sub    = st.selectbox("Filter by Subject",  ["All"] + subjects)
    with sf3:
        filter_status = st.selectbox("Filter by Status",   ["All", "Pending", "Completed"])

    display_tasks = search_tasks(tasks, search_kw)
    display_tasks = filter_tasks(display_tasks, filter_sub, filter_status)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ---- Task Table ---- #
    st.markdown(
        f'<div class="section-title">📋 Tasks '
        f'<span style="color:#64748b;font-size:0.82rem;text-transform:none;letter-spacing:0">'
        f'({len(display_tasks)} shown)</span></div>',
        unsafe_allow_html=True,
    )

    if not display_tasks:
        msg_txt = ("No tasks match your filters — try changing the criteria."
                   if tasks else "No tasks yet. Add your first task above! 👆")
        st.markdown(f'<div class="info-box">📌 {msg_txt}</div>', unsafe_allow_html=True)
    else:
        show_notes = cfg.get("show_notes_col", True)
        task_rows  = []
        for t in display_tasks:
            row = {
                "ID"      : t.task_id,
                "Status"  : t.get_status_icon() + "  " + t.status,
                "Subject" : t.subject,
                "Topic"   : t.topic,
                "Priority": t.priority,
            }
            if show_notes:
                row["Notes"] = t.notes if t.notes else "—"
            task_rows.append(row)

        df = pd.DataFrame(task_rows)
        st.dataframe(df, width="stretch", hide_index=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # ---- Update / Delete ---- #
        st.markdown('<div class="section-title">✏️ Update or Delete a Task</div>',
                    unsafe_allow_html=True)

        task_options = {
            f"[#{t.task_id}]  {t.subject}  —  {t.topic}": t.task_id
            for t in display_tasks
        }

        sel_label    = st.selectbox("Select Task", list(task_options.keys()))
        sel_task_id  = task_options[sel_label]
        current_task = next((t for t in tasks if t.task_id == sel_task_id), None)
        cur_index    = 0 if (current_task and current_task.status == "Pending") else 1

        u1, u2, u3 = st.columns([3, 2, 2])
        with u1:
            new_status = st.selectbox("New Status", ["Pending", "Completed"], index=cur_index)
        with u2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾  Update Status"):
                st.session_state.tasks = update_task_status(
                    st.session_state.tasks, sel_task_id, new_status)
                persist()
                st.success(f"✅ Status updated to **{new_status}**.")
                st.rerun()
        with u3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑  Delete Task"):
                st.session_state.tasks, del_msg = delete_task(
                    st.session_state.tasks, sel_task_id)
                persist()
                st.success(del_msg)
                st.rerun()


# ================================================================== #
#  TAB 4 — Progress Charts                                             #
# ================================================================== #

with tab_progress:
    st.markdown('<div class="section-title">📊 Progress Visualisation</div>',
                unsafe_allow_html=True)

    if not tasks:
        st.markdown('<div class="info-box">📌 Add some tasks to see progress charts.</div>',
                    unsafe_allow_html=True)
    else:
        subject_progress = [sp for sp in get_all_subject_progress(subjects, tasks)
                            if sp["total"] > 0]

        if not subject_progress:
            st.markdown('<div class="info-box">📌 Add tasks to your subjects to see charts.</div>',
                        unsafe_allow_html=True)
        else:
            chart_col1, chart_col2 = st.columns(2, gap="large")

            # ---- Bar Chart ---- #
            with chart_col1:
                st.markdown("##### 📊 Subject-wise Completion")
                subj_names  = [sp["subject"]    for sp in subject_progress]
                percentages = [sp["percentage"] for sp in subject_progress]
                colours = ["#22c55e" if p == 100 else "#a78bfa" if p >= 50 else "#f59e0b"
                           for p in percentages]

                BG = "#0d0d1a"
                fig_bar, ax_bar = plt.subplots(figsize=(6, max(3, len(subj_names) * 0.75)))
                fig_bar.patch.set_facecolor(BG)
                ax_bar.set_facecolor(BG)

                bars = ax_bar.barh(subj_names, percentages,
                                   color=colours, edgecolor="none", height=0.52)
                for bar, pct in zip(bars, percentages):
                    x_pos = pct + 1.5 if pct < 95 else pct - 6
                    ax_bar.text(x_pos, bar.get_y() + bar.get_height() / 2,
                                f"{pct}%", va="center", ha="left",
                                color="#e2e8f0", fontsize=9, fontweight="bold")

                # Draw target line
                target_line = cfg.get("target_completion_pct", 80)
                ax_bar.axvline(target_line, color="#f87171", linestyle="--",
                               linewidth=1.2, alpha=0.7, label=f"Target {target_line}%")

                ax_bar.set_xlim(0, 115)
                ax_bar.set_xlabel("Completion (%)", color="#64748b", fontsize=9)
                ax_bar.tick_params(colors="#94a3b8", labelsize=9)
                ax_bar.set_title("Subject-wise Progress",
                                 color="#e2e8f0", fontsize=11, pad=12, fontweight="bold")
                for spine in ("top", "right"):
                    ax_bar.spines[spine].set_visible(False)
                for spine in ("left", "bottom"):
                    ax_bar.spines[spine].set_color("#1e293b")

                patches = [
                    mpatches.Patch(color="#22c55e", label="100% ✓"),
                    mpatches.Patch(color="#a78bfa", label="≥ 50%"),
                    mpatches.Patch(color="#f59e0b", label="< 50%"),
                ]
                ax_bar.legend(handles=patches, loc="lower right",
                              facecolor="#1e1b4b", labelcolor="#94a3b8",
                              edgecolor="#2d3748", fontsize=8)

                plt.tight_layout(pad=1.0)
                st.pyplot(fig_bar)
                plt.close(fig_bar)

            # ---- Donut Chart ---- #
            with chart_col2:
                st.markdown("##### 🥧 Completed vs Pending")
                stats_p         = get_summary_stats(subjects, tasks)
                completed_count = stats_p["completed"]
                pending_count   = stats_p["pending"]

                BG = "#0d0d1a"
                fig_pie, ax_pie = plt.subplots(figsize=(5, 4))
                fig_pie.patch.set_facecolor(BG)
                ax_pie.set_facecolor(BG)

                if completed_count == 0 and pending_count == 0:
                    ax_pie.text(0, 0, "No tasks", ha="center", va="center",
                                color="#94a3b8", fontsize=12)
                else:
                    pie_labels, pie_values, pie_colors = [], [], []
                    if completed_count > 0:
                        pie_labels.append(f"Completed\n({completed_count})")
                        pie_values.append(completed_count)
                        pie_colors.append("#22c55e")
                    if pending_count > 0:
                        pie_labels.append(f"Pending\n({pending_count})")
                        pie_values.append(pending_count)
                        pie_colors.append("#a78bfa")

                    wedges, texts, autotexts = ax_pie.pie(
                        pie_values, labels=pie_labels, colors=pie_colors,
                        autopct="%1.1f%%", startangle=90, pctdistance=0.78,
                        wedgeprops={"edgecolor": BG, "linewidth": 3, "width": 0.55},
                    )
                    for text in texts:
                        text.set_color("#94a3b8"); text.set_fontsize(9)
                    for at in autotexts:
                        at.set_color("#ffffff"); at.set_fontweight("bold"); at.set_fontsize(9)

                    total = completed_count + pending_count
                    ax_pie.text(0, 0, f"{completed_count}\n/{total}",
                                ha="center", va="center",
                                color="#e2e8f0", fontsize=13, fontweight="bold")

                ax_pie.set_title("Task Completion Split",
                                 color="#e2e8f0", fontsize=11, pad=12, fontweight="bold")
                plt.tight_layout(pad=1.0)
                st.pyplot(fig_pie)
                plt.close(fig_pie)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Detailed Subject Statistics</div>',
                    unsafe_allow_html=True)
        if subject_progress:
            df_prog = pd.DataFrame(subject_progress)
            df_prog.columns = ["Subject", "Total Tasks", "Completed", "Progress (%)"]
            st.dataframe(df_prog, width="stretch", hide_index=True)


# ================================================================== #
#  TAB 5 — Settings                                                    #
# ================================================================== #

with tab_settings:

    st.markdown('<div class="section-title">⚙️ Application Settings</div>',
                unsafe_allow_html=True)

    # ================================================================ #
    #  SECTION 1 — Student Profile                                      #
    # ================================================================ #

    st.markdown("""
    <div class="settings-card">
        <div class="settings-card-title">👤 Student Profile</div>
        <div class="settings-card-desc">Your name and course info — shown in the app header.</div>
    </div>""", unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3)
    with p1:
        new_name = st.text_input(
            "Your Name",
            value = cfg.get("student_name", ""),
            placeholder = "e.g. Devansh Sharma",
            key = "sett_name",
        )
    with p2:
        new_course = st.text_input(
            "Course / Programme",
            value = cfg.get("course", "MCA"),
            placeholder = "e.g. MCA, BCA, B.Tech",
            key = "sett_course",
        )
    with p3:
        semester_opts  = [f"Semester {i}" for i in range(1, 7)]
        current_sem    = cfg.get("semester", "Semester 1")
        sem_index      = semester_opts.index(current_sem) if current_sem in semester_opts else 0
        new_semester   = st.selectbox("Semester", semester_opts, index=sem_index, key="sett_sem")

    if st.button("💾  Save Profile", key="btn_save_profile"):
        st.session_state.settings["student_name"] = new_name.strip()
        st.session_state.settings["course"]       = new_course.strip() or "MCA"
        st.session_state.settings["semester"]     = new_semester
        persist_settings()
        st.success("✅ Profile saved! The header will update on next interaction.")
        st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ================================================================ #
    #  SECTION 2 — Study Goals                                          #
    # ================================================================ #

    st.markdown("""
    <div class="settings-card">
        <div class="settings-card-title">🎯 Study Goals</div>
        <div class="settings-card-desc">Set your targets — used on the Dashboard to show whether you are on track.</div>
    </div>""", unsafe_allow_html=True)

    g1, g2, g3 = st.columns(3)
    with g1:
        new_target_pct = st.number_input(
            "Target Completion (%)",
            min_value = 10, max_value = 100, step = 5,
            value = int(cfg.get("target_completion_pct", 80)),
            help  = "Your goal: reach this % of tasks completed.",
            key   = "sett_target_pct",
        )
    with g2:
        new_daily_hours = st.number_input(
            "Daily Study Goal (hours)",
            min_value = 1, max_value = 16, step = 1,
            value = int(cfg.get("daily_goal_hours", 4)),
            help  = "How many hours you aim to study each day.",
            key   = "sett_daily_hours",
        )
    with g3:
        new_warn = st.toggle(
            "Show goal status on Dashboard",
            value = cfg.get("warn_below_target", True),
            key   = "sett_warn",
            help  = "Displays an On Track / Below Target chip on the Dashboard.",
        )

    # Live preview of goal status
    current_progress = get_summary_stats(subjects, tasks)["progress"]
    if current_progress >= new_target_pct:
        st.markdown(
            f'<div class="success-box">🟢 At your current progress of <strong>{current_progress}%</strong>, '
            f'you are <strong>on track</strong> for your {new_target_pct}% goal!</div>',
            unsafe_allow_html=True,
        )
    else:
        gap = round(new_target_pct - current_progress, 1)
        st.markdown(
            f'<div class="warn-box">🟡 You are at <strong>{current_progress}%</strong>. '
            f'You need <strong>{gap}% more</strong> to reach your {new_target_pct}% goal.</div>',
            unsafe_allow_html=True,
        )

    if st.button("💾  Save Goals", key="btn_save_goals"):
        st.session_state.settings["target_completion_pct"] = int(new_target_pct)
        st.session_state.settings["daily_goal_hours"]      = int(new_daily_hours)
        st.session_state.settings["warn_below_target"]     = new_warn
        persist_settings()
        st.success("✅ Study goals saved!")
        st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ================================================================ #
    #  SECTION 3 — Task Defaults & Display                              #
    # ================================================================ #

    st.markdown("""
    <div class="settings-card">
        <div class="settings-card-title">📝 Task Defaults &amp; Display</div>
        <div class="settings-card-desc">Control how new tasks are created and how the task table looks.</div>
    </div>""", unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        pri_opts   = ["Medium", "High", "Low"]
        cur_def    = cfg.get("default_priority", "Medium")
        new_def_pri = st.selectbox(
            "Default Priority for New Tasks",
            pri_opts,
            index = pri_opts.index(cur_def) if cur_def in pri_opts else 0,
            help  = "This priority will be pre-selected when you open the Add Task form.",
            key   = "sett_def_pri",
        )
    with d2:
        new_show_notes = st.toggle(
            "Show Notes column in Task table",
            value = cfg.get("show_notes_col", True),
            help  = "Toggle whether the Notes column is shown in the Study Tasks tab.",
            key   = "sett_show_notes",
        )

    if st.button("💾  Save Display Settings", key="btn_save_display"):
        st.session_state.settings["default_priority"] = new_def_pri
        st.session_state.settings["show_notes_col"]   = new_show_notes
        persist_settings()
        st.success("✅ Display settings saved!")
        st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ================================================================ #
    #  SECTION 4 — Bulk Task Actions                                    #
    # ================================================================ #

    st.markdown("""
    <div class="settings-card">
        <div class="settings-card-title">⚡ Bulk Task Actions</div>
        <div class="settings-card-desc">Quickly update multiple tasks at once.</div>
    </div>""", unsafe_allow_html=True)

    ba1, ba2 = st.columns(2)

    with ba1:
        st.markdown("**Mark All Tasks by Subject**")
        bulk_subject = st.selectbox(
            "Subject",
            ["All"] + subjects,
            key = "bulk_subject",
            help = "Select a subject or 'All' to apply to every task.",
        )
        bulk_status = st.selectbox(
            "Mark as",
            ["Completed", "Pending"],
            key = "bulk_status",
        )
        if st.button("⚡  Apply to All", key="btn_bulk_mark"):
            if not tasks:
                st.warning("No tasks to update.")
            else:
                st.session_state.tasks, bulk_msg = mark_all_tasks(
                    st.session_state.tasks, bulk_subject, bulk_status
                )
                persist()
                st.success(bulk_msg)
                st.rerun()

    with ba2:
        st.markdown("**Remove Completed Tasks**")
        st.markdown("""
        <div class="info-box" style="margin-bottom:0.75rem">
            🧹 Removes all tasks marked as <strong>Completed</strong>.
            This frees up your task list to show only pending work.
            This action <strong>cannot be undone</strong>.
        </div>""", unsafe_allow_html=True)
        completed_count_ba = sum(1 for t in tasks if t.is_completed())
        st.write(f"Currently **{completed_count_ba}** completed task(s) in your list.")
        if st.button("🧹  Clear Completed Tasks", key="btn_clear_completed"):
            if completed_count_ba == 0:
                st.info("No completed tasks to remove.")
            else:
                st.session_state.tasks, clear_msg = clear_completed_tasks(st.session_state.tasks)
                persist()
                st.success(clear_msg)
                st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ================================================================ #
    #  SECTION 5 — Export Data                                          #
    # ================================================================ #

    st.markdown("""
    <div class="settings-card">
        <div class="settings-card-title">📤 Export Your Data</div>
        <div class="settings-card-desc">Download your study data for backup or submission.</div>
    </div>""", unsafe_allow_html=True)

    ex1, ex2 = st.columns(2)

    with ex1:
        st.markdown("**📄 Export as CSV**")
        st.markdown("""
        <div class="info-box" style="margin-bottom:0.75rem">
            Downloads all your tasks as a <strong>.csv</strong> file.
            Open it in Excel or Google Sheets to view your task list.
        </div>""", unsafe_allow_html=True)
        if tasks:
            csv_data = export_tasks_csv(tasks)
            st.download_button(
                label     = "⬇️  Download tasks.csv",
                data      = csv_data,
                file_name = "study_tasks.csv",
                mime      = "text/csv",
                key       = "btn_export_csv",
            )
        else:
            st.markdown('<div class="warn-box">⚠️ No tasks to export.</div>',
                        unsafe_allow_html=True)

    with ex2:
        st.markdown("**📦 Export as JSON (Full Backup)**")
        st.markdown("""
        <div class="info-box" style="margin-bottom:0.75rem">
            Downloads everything — subjects <strong>and</strong> tasks — as a
            <strong>.json</strong> file. Use this to restore your data later.
        </div>""", unsafe_allow_html=True)
        json_data = export_data_json(subjects, tasks)
        st.download_button(
            label     = "⬇️  Download backup.json",
            data      = json_data,
            file_name = "study_tracker_backup.json",
            mime      = "application/json",
            key       = "btn_export_json",
        )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ================================================================ #
    #  SECTION 6 — Danger Zone                                          #
    # ================================================================ #

    st.markdown("""
    <div class="settings-card" style="border-color:rgba(239,68,68,0.35)">
        <div class="settings-card-title" style="color:#f87171">🚨 Danger Zone</div>
        <div class="settings-card-desc">Irreversible actions. Export your data first!</div>
    </div>""", unsafe_allow_html=True)

    dz1, dz2 = st.columns(2)

    with dz1:
        st.markdown("**Reset All Tasks**")
        st.markdown("""
        <div class="danger-box" style="margin-bottom:0.75rem">
            ⚠️ Deletes <em>all</em> tasks permanently. Subjects are kept.
        </div>""", unsafe_allow_html=True)
        if st.button("🗑  Reset All Tasks", key="btn_reset_tasks"):
            st.session_state.tasks = []
            persist()
            st.success("✅ All tasks deleted. Subjects are unchanged.")
            st.rerun()

    with dz2:
        st.markdown("**Reset Everything**")
        st.markdown("""
        <div class="danger-box" style="margin-bottom:0.75rem">
            ⚠️ Deletes <em>all</em> subjects and tasks. App returns to defaults.
        </div>""", unsafe_allow_html=True)
        if st.button("💥  Reset App to Defaults", key="btn_reset_all"):
            st.session_state.subjects = ["Python", "DBMS", "Linux", "DAA", "AIP"]
            st.session_state.tasks    = []
            persist()
            st.success("✅ App reset to default state.")
            st.rerun()
