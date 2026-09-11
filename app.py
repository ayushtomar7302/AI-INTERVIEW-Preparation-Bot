import streamlit as st
import requests

st.set_page_config(page_title="AI Interview Preparation Bot", page_icon="🎯", layout="wide")


# --- V5 modern UI ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(circle at 10% 0%, rgba(99,102,241,.12), transparent 28%), radial-gradient(circle at 90% 10%, rgba(16,185,129,.10), transparent 25%), #f8fafc; }
.block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 3rem; }
.hero { padding: 2.2rem; border-radius: 24px; background: linear-gradient(135deg,#111827,#312e81 55%,#0f766e); color:white; box-shadow: 0 18px 45px rgba(15,23,42,.18); margin-bottom:1.5rem; }
.hero h1 { margin:0; font-size:2.35rem; font-weight:800; letter-spacing:-.04em; }
.hero p { margin:.6rem 0 0; opacity:.86; font-size:1rem; }
.card { background:rgba(255,255,255,.88); border:1px solid rgba(148,163,184,.22); border-radius:18px; padding:1.1rem 1.25rem; box-shadow:0 8px 28px rgba(15,23,42,.06); margin:.5rem 0; }
.metric { font-size:1.7rem; font-weight:800; }
.label { color:#64748b; font-size:.82rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; }
.question { background:white; border-left:5px solid #6366f1; border-radius:16px; padding:1.15rem 1.25rem; box-shadow:0 8px 25px rgba(15,23,42,.06); margin:1rem 0; }
.badge { display:inline-block; padding:.28rem .65rem; border-radius:999px; background:#eef2ff; color:#4338ca; font-size:.78rem; font-weight:700; margin-right:.4rem; }
.stButton > button { border-radius:12px; font-weight:700; min-height:2.65rem; }
div[data-testid="stSidebar"] { background:linear-gradient(180deg,#111827,#1e1b4b); }
div[data-testid="stSidebar"] * { color:#f8fafc !important; }
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea { border-radius:12px; }
div[data-testid="stMetric"] { background:white; border:1px solid #e2e8f0; padding:12px; border-radius:14px; }
</style>
""", unsafe_allow_html=True)

import os
from dotenv import load_dotenv

load_dotenv()

try:
    API_URL = st.secrets.get(
        "API_URL",
        os.getenv("API_URL", "http://127.0.0.1:8000")
    )
except Exception:
    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
if "user" not in st.session_state:
    st.session_state.user = None

def api_post(path, payload):
    try:
        r = requests.post(f"{API_URL}{path}", json=payload, timeout=90)
        if r.ok:
            return r.json()
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        st.error(f"API error ({r.status_code}): {detail}")
    except requests.RequestException as e:
        st.error(f"Backend connection failed: {e}")
    return None

def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}", timeout=30)
        if r.ok:
            return r.json()
        st.error(r.text)
    except requests.RequestException as e:
        st.error(f"Backend connection failed: {e}")
    return None

if st.session_state.user is None:
    st.title("🎯 AI Interview Preparation & Simulation Bot")
    st.caption("Create an account to save your profile and interview history.")

    login_tab, create_tab = st.tabs(["🔐 Login", "📝 Create Account"])

    with login_tab:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary", use_container_width=True):
            if not username or not password:
                st.warning("Enter username and password.")
            else:
                data = api_post("/users/login", {"username": username, "password": password})
                if data:
                    st.session_state.user = data["user"]
                    st.rerun()

    with create_tab:
        st.subheader("Create Account")
        name = st.text_input("Full Name", key="reg_name")
        username = st.text_input("Username", key="reg_username")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        target_role = st.text_input("Target Role", placeholder="e.g. Full Stack Developer")
        skills = st.text_area("Skills", placeholder="Python, Java, SQL, React...")
        if st.button("Create Account", type="primary", use_container_width=True):
            if not all([name, username, password, confirm]):
                st.warning("Please fill all required fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                data = api_post("/users/register", {
                    "name": name, "username": username, "password": password,
                    "target_role": target_role, "skills": skills
                })
                if data:
                    st.success("Account created. You can now log in.")
    st.stop()

user = st.session_state.user

with st.sidebar:
    st.header("👤 My Profile")
    st.write(f"**Name:** {user['name']}")
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Target Role:** {user.get('target_role') or 'Not set'}")
    st.write(f"**Skills:** {user.get('skills') or 'Not set'}")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        for k in ["session_id", "current_question", "last_feedback", "report"]:
            st.session_state.pop(k, None)
        st.rerun()

st.title("🎯 AI Interview Preparation & Simulation Bot")

new_tab, history_tab = st.tabs(["🆕 New Interview", "📊 My History"])

with new_tab:
    st.subheader("Start a New Interview")
    col1, col2 = st.columns(2)
    with col1:
        interview_type = st.selectbox("Interview Type", ["Technical", "HR", "Mixed"])
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    with col2:
        num_questions = st.slider("Number of Questions", 3, 10, 5)

    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        with st.spinner("Creating your personalized interview..."):
            data = api_post("/interviews/start", {
                "user_id": user["id"],
                "name": user["name"],
                "target_role": user.get("target_role", ""),
                "skills": user.get("skills", ""),
                "interview_type": interview_type,
                "difficulty": difficulty,
                "num_questions": num_questions
            })
        if data and data.get("session_id") and data.get("question"):
            st.session_state.session_id = data["session_id"]
            st.session_state.current_question = data["question"]
            st.session_state.question_number = data.get("question_number", 1)
            st.session_state.total_questions = num_questions
            st.session_state.last_feedback = None
            st.session_state.report = None
            st.session_state.interview_started = True
            st.rerun()
        elif data:
            st.error("Interview started, but no question was returned by the backend. Click Start Interview again.")

    # Recover the current question if Streamlit reruns/reset the question state.
    if st.session_state.get("session_id") and not st.session_state.get("current_question"):
        current = api_get(f"/interviews/{st.session_state.session_id}/current")
        if current and not current.get("completed") and current.get("question"):
            st.session_state.current_question = current["question"]
            st.session_state.question_number = current.get("question_number", 1)
            st.session_state.total_questions = current.get("total_questions", num_questions)
        elif current and current.get("completed"):
            st.session_state.pop("session_id", None)
            st.session_state.pop("current_question", None)

    if "session_id" in st.session_state and st.session_state.get("current_question"):
        st.divider()
        qno = st.session_state.get("question_number", 1)
        total = st.session_state.get("total_questions", num_questions)
        st.markdown(f"""
        <div class="question">
          <span class="badge">QUESTION {qno} OF {total}</span>
          <span class="badge">LIVE INTERVIEW</span>
          <h3 style="margin-top:.8rem">{st.session_state.get("current_question", "Loading question...")}</h3>
        </div>
        """, unsafe_allow_html=True)

        progress = min(max((qno - 1) / max(total, 1), 0), 1)
        st.progress(progress, text=f"Progress: {qno-1}/{total} completed")
        answer = st.text_area("✍️ Your Answer", height=180, key=f"answer_{qno}",
                              placeholder="Type your answer here. Try to explain the concept clearly and add an example.")
        if st.button("Submit Answer", type="primary"):
            if not answer.strip():
                st.warning("Please write an answer first.")
            else:
                data = api_post(
                    f"/interviews/{st.session_state.session_id}/answer",
                    {"answer": answer}
                )
                if data:
                    st.session_state.last_feedback = data["feedback"]
                    if data["completed"]:
                        st.session_state.report = data["report"]
                        st.session_state.pop("current_question", None)
                        st.session_state.pop("session_id", None)
                    else:
                        st.session_state.question_number = data["question_number"]
                        st.session_state.current_question = data["question"]
                    st.rerun()

        if st.session_state.get("last_feedback"):
            fb = st.session_state.last_feedback
            st.divider()
            st.subheader("🤖 AI Feedback")
            st.metric("Score", f"{fb.get('score', 0)}/10")
            st.write("**Strengths:**", fb.get("strengths", ""))
            st.write("**Missing Points:**", fb.get("missing_points", ""))
            st.write("**Mistake Analysis:**", fb.get("mistake_analysis", ""))
            st.write("**How to Improve:**", fb.get("improvement", ""))
            with st.expander("✅ Correct / Expected Answer"):
                st.write(fb.get("correct_answer", ""))
            with st.expander("🎯 Interview-Ready Model Answer"):
                st.write(fb.get("model_answer", ""))

    if st.session_state.get("report"):
        report = st.session_state.report
        st.divider()
        st.header("📋 Final Interview Report")
        st.metric("Overall Score", f"{report.get('overall_score', 0)}/10")
        st.write("**Summary:**", report.get("summary", ""))
        st.write("**Strong Areas:**", report.get("strong_areas", ""))
        st.write("**Weak Areas:**", report.get("weak_areas", ""))
        st.write("**Personalized Improvement Plan:**", report.get("personalized_plan", ""))

        st.subheader("Question-wise Review")
        for item in report.get("questions", []):
            with st.expander(f"Q{item['number']}: {item['question']} — {item['score']}/10"):
                st.markdown("**Your Answer**")
                st.write(item.get("user_answer", ""))
                st.markdown("**Correct / Expected Answer**")
                st.write(item.get("correct_answer", ""))
                st.markdown("**Your Mistake / Missing Points**")
                st.write(item.get("mistake_analysis", ""))
                st.markdown("**How to Improve**")
                st.write(item.get("improvement", ""))
                st.markdown("**Interview-Ready Model Answer**")
                st.write(item.get("model_answer", ""))

with history_tab:
    st.subheader("📊 My Previous Interviews")
    if st.button("🔄 Refresh History"):
        st.rerun()
    history = api_get(f"/users/{user['id']}/history")
    if history and history.get("interviews"):
        for item in history["interviews"]:
            with st.expander(
                f"{item['interview_type']} • {item['difficulty']} • "
                f"Score: {item['overall_score']}/10 • {item['created_at']}"
            ):
                st.write("Questions:", item["num_questions"])
                st.write("Summary:", item.get("summary", ""))
                st.write("Strong Areas:", item.get("strong_areas", ""))
                st.write("Weak Areas:", item.get("weak_areas", ""))
    else:
        st.info("No previous interviews found. Complete your first interview to build your history.")

st.markdown("""
<div style="text-align:center;color:#64748b;padding:2rem 0 1rem;font-size:.85rem">
  Built with Python • FastAPI • Streamlit • OpenAI
</div>
""", unsafe_allow_html=True)
