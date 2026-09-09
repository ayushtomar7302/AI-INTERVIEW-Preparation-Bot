import os
import json
import random
import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()

app = FastAPI(title="AI Interview Preparation Bot API")
DB_PATH = os.getenv("DATABASE_PATH", "interviews.db")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

TECH_QUESTIONS = {
    "What is the difference between a stack and a queue?": "A stack follows LIFO (Last In, First Out), while a queue follows FIFO (First In, First Out). A stack commonly uses push and pop operations; a queue commonly uses enqueue and dequeue operations.",
    "Explain OOP concepts with a practical example.": "Object-Oriented Programming is based on objects that combine data and behavior. Its main principles are encapsulation, abstraction, inheritance, and polymorphism. For example, a BankAccount class can encapsulate balance and expose deposit and withdraw methods.",
    "What is the difference between SQL INNER JOIN and LEFT JOIN?": "INNER JOIN returns only rows with matching values in both tables. LEFT JOIN returns all rows from the left table and matching rows from the right table; unmatched right-side values are NULL.",
    "Explain REST API and the meaning of GET, POST, PUT and DELETE.": "A REST API lets applications communicate over HTTP using resources and standard methods. GET retrieves data, POST creates or submits data, PUT updates or replaces a resource, and DELETE removes a resource.",
    "What is normalization in a relational database?": "Normalization organizes relational data to reduce redundancy and prevent update, insert, and delete anomalies. Common normal forms include 1NF, 2NF, and 3NF.",
    "Explain time complexity and give the complexity of binary search.": "Time complexity describes how an algorithm's running time grows with input size. Binary search repeatedly halves a sorted search space, so its time complexity is O(log n).",
    "What is the difference between a process and a thread?": "A process is an independent program in execution with its own address space, while a thread is a smaller execution unit within a process and shares the process's memory. Threads are generally cheaper to create and communicate between than processes.",
    "Explain inheritance and polymorphism.": "Inheritance allows a child class to acquire properties and methods from a parent class. Polymorphism allows the same interface or method call to produce different behavior, such as method overriding at runtime.",
    "What is a primary key and a foreign key?": "A primary key uniquely identifies each row in a table and cannot contain NULL values. A foreign key references a key in another table to establish and enforce a relationship between tables.",
    "What is the difference between authentication and authorization?": "Authentication verifies who a user is, while authorization determines what an authenticated user is allowed to access or do."
}

HR_QUESTIONS = {
    "Tell me about yourself.": "A strong answer should briefly cover your current education or role, relevant skills, important projects or experience, key strengths, and the role you are seeking. Keep it concise and job-focused.",
    "Why should we hire you?": "A strong answer should connect your relevant skills, projects, problem-solving ability, willingness to learn, and potential contribution to the requirements of the role.",
    "What are your strengths and weaknesses?": "State two or three job-relevant strengths with brief examples. For a weakness, choose a genuine but manageable area and explain the concrete steps you are taking to improve it.",
    "Why do you want to join our company?": "Connect the company's work, products, culture, or learning opportunities with your skills and career goals, and explain how you can contribute.",
    "Where do you see yourself in five years?": "Describe realistic professional growth, deeper expertise, increased responsibility, and meaningful contribution to the organization while continuing to learn.",
    "Tell me about a difficult problem you solved.": "Use a specific example and explain the situation, your responsibility, the challenge, the actions you took, and the result or learning.",
    "How do you handle pressure and deadlines?": "Explain how you prioritize tasks, break work into smaller steps, communicate risks early, and focus on high-impact work to meet deadlines.",
    "Describe a time when you worked in a team.": "Give a specific teamwork example, describe your role, how you communicated or resolved issues, and the final result.",
    "What motivates you to learn new technologies?": "Explain that curiosity, solving real problems, career growth, and improving your ability to build useful solutions motivate you, and give a brief example if possible.",
    "Do you have any questions for the interviewer?": "A strong response asks thoughtful job-related questions, such as expectations for the role, team collaboration, learning opportunities, or how success is measured."
}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        target_role TEXT,
        skills TEXT,
        created_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        name TEXT,
        target_role TEXT,
        skills TEXT,
        interview_type TEXT,
        difficulty TEXT,
        num_questions INTEGER,
        current_index INTEGER DEFAULT 0,
        questions_json TEXT,
        overall_score REAL,
        summary TEXT,
        strong_areas TEXT,
        weak_areas TEXT,
        personalized_plan TEXT,
        created_at TEXT NOT NULL
    )""")
    # Migration for databases created by v2.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(interviews)").fetchall()}
    if "user_id" not in cols:
        conn.execute("ALTER TABLE interviews ADD COLUMN user_id INTEGER")

    conn.execute("""CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        question_number INTEGER,
        question TEXT,
        user_answer TEXT,
        score REAL,
        correct_answer TEXT,
        mistake_analysis TEXT,
        strengths TEXT,
        missing_points TEXT,
        improvement TEXT,
        model_answer TEXT
    )""")
    conn.commit()
    return conn

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return digest.hex(), salt.hex()

def verify_password(password, stored_hash, stored_salt):
    digest, _ = hash_password(password, bytes.fromhex(stored_salt))
    return secrets.compare_digest(digest, stored_hash)

def fallback_feedback(question, answer, correct_answer=""):
    words = len(answer.split())
    score = 2 if words < 8 else 5 if words < 20 else 7 if words < 40 else 8
    return {
        "score": score,
        "strengths": "The answer attempts to address the question." if words else "No answer provided.",
        "missing_points": "Add definitions, key concepts, and a concrete example where relevant.",
        "improvement": "Structure the response as definition → explanation → example → conclusion.",
        "correct_answer": correct_answer or "A strong answer should directly address the key concept in the question and explain it accurately with an example.",
        "mistake_analysis": "The response may be too brief or may not cover the important concepts expected by an interviewer.",
        "model_answer": correct_answer or "Start with a clear definition, explain the main idea in 2–4 points, and finish with a practical example."
    }

def ai_feedback(question, answer, profile, correct_answer=""):
    fallback = fallback_feedback(question, answer, correct_answer)
    if not client:
        return fallback
    prompt = f"""
You are an expert technical and HR interview evaluator.
Candidate profile:
Name: {profile.get('name')}
Target role: {profile.get('target_role')}
Skills: {profile.get('skills')}

Question: {question}
Candidate answer: {answer}

Reference / correct answer: {correct_answer}

Evaluate the answer fairly and compare the candidate response primarily against the reference answer. Return ONLY valid JSON with exactly these keys:
score (number 0-10),
strengths (string),
missing_points (string),
improvement (string),
correct_answer (string),
mistake_analysis (string),
model_answer (string).

correct_answer must state the expected factual/content answer.
mistake_analysis must explicitly identify what the candidate got wrong, omitted, or explained unclearly.
model_answer must be concise and interview-ready.
"""
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a strict but constructive interview evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        data = json.loads(response.choices[0].message.content)
        for key, value in fallback.items():
            data.setdefault(key, value)
        return data
    except Exception:
        return fallback

def build_report(conn, session_id):
    row = conn.execute("SELECT * FROM interviews WHERE session_id=?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Interview session not found")
    answers = conn.execute(
        "SELECT * FROM answers WHERE session_id=? ORDER BY question_number", (session_id,)
    ).fetchall()
    scores = [a["score"] for a in answers]
    overall = round(sum(scores) / len(scores), 2) if scores else 0
    strong = "Good performance" if overall >= 7 else "Basic understanding shown"
    weak = "Focus on clarity, accuracy, examples, and missing concepts" if overall < 8 else "Minor refinements in communication"
    plan = "Review weak topics, practice 5 questions daily, and compare answers with model answers."

    conn.execute("""UPDATE interviews
        SET overall_score=?, summary=?, strong_areas=?, weak_areas=?, personalized_plan=?
        WHERE session_id=?""",
        (overall, f"Completed {len(answers)} questions with an average score of {overall}/10.",
         strong, weak, plan, session_id))
    conn.commit()

    questions = []
    for a in answers:
        questions.append({
            "number": a["question_number"],
            "question": a["question"],
            "user_answer": a["user_answer"],
            "score": a["score"],
            "correct_answer": a["correct_answer"],
            "mistake_analysis": a["mistake_analysis"],
            "strengths": a["strengths"],
            "missing_points": a["missing_points"],
            "improvement": a["improvement"],
            "model_answer": a["model_answer"]
        })
    return {
        "overall_score": overall,
        "summary": f"Completed {len(answers)} questions with an average score of {overall}/10.",
        "strong_areas": strong,
        "weak_areas": weak,
        "personalized_plan": plan,
        "questions": questions
    }

class RegisterRequest(BaseModel):
    name: str
    username: str
    password: str
    target_role: str = ""
    skills: str = ""

class LoginRequest(BaseModel):
    username: str
    password: str

class StartInterviewRequest(BaseModel):
    user_id: int
    name: str
    target_role: str = ""
    skills: str = ""
    interview_type: str = "Technical"
    difficulty: str = "Medium"
    num_questions: int = 5

class AnswerRequest(BaseModel):
    answer: str

@app.get("/")
def root():
    return {"message": "AI Interview Preparation Bot API is running"}

@app.post("/users/register")
def register(req: RegisterRequest):
    conn = db()
    try:
        password_hash, salt = hash_password(req.password)
        cur = conn.execute(
            """INSERT INTO users
            (name, username, password_hash, password_salt, target_role, skills, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (req.name.strip(), req.username.strip(), password_hash, salt,
             req.target_role.strip(), req.skills.strip(), datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()
        return {"message": "Account created", "user_id": cur.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username already exists. Choose another username.")
    finally:
        conn.close()

@app.post("/users/login")
def login(req: LoginRequest):
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (req.username.strip(),)).fetchone()
    conn.close()
    if not user or not verify_password(req.password, user["password_hash"], user["password_salt"]):
        raise HTTPException(401, "Invalid username or password")
    return {"user": {
        "id": user["id"], "name": user["name"], "username": user["username"],
        "target_role": user["target_role"], "skills": user["skills"]
    }}

@app.get("/users/{user_id}/history")
def history(user_id: int):
    conn = db()
    rows = conn.execute(
        """SELECT session_id, interview_type, difficulty, num_questions,
                  overall_score, summary, strong_areas, weak_areas, created_at
           FROM interviews WHERE user_id=? ORDER BY id DESC""", (user_id,)
    ).fetchall()
    conn.close()
    return {"interviews": [dict(r) for r in rows]}

@app.post("/interviews/start")
def start_interview(req: StartInterviewRequest):
    if req.num_questions < 3 or req.num_questions > 10:
        raise HTTPException(400, "Number of questions must be between 3 and 10.")

    conn = db()
    if not conn.execute("SELECT id FROM users WHERE id=?", (req.user_id,)).fetchone():
        conn.close()
        raise HTTPException(404, "User not found")

    if req.interview_type == "Technical":
        pool = TECH_QUESTIONS
    elif req.interview_type == "HR":
        pool = HR_QUESTIONS
    else:
        mixed = list(TECH_QUESTIONS.items())[:5] + list(HR_QUESTIONS.items())[:5]
        pool = dict(mixed)

    questions = random.sample(list(pool.keys()), min(req.num_questions, len(pool)))
    session_id = secrets.token_urlsafe(12)

    conn.execute("""INSERT INTO interviews
        (session_id, user_id, name, target_role, skills, interview_type, difficulty,
         num_questions, current_index, questions_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (session_id, req.user_id, req.name, req.target_role, req.skills,
         req.interview_type, req.difficulty, req.num_questions,
         json.dumps({"questions": questions, "correct_answers": {q: pool[q] for q in questions}}), datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()
    return {"session_id": session_id, "question": questions[0], "question_number": 1}

@app.post("/interviews/{session_id}/answer")
def submit_answer(session_id: str, req: AnswerRequest):
    conn = db()
    interview = conn.execute("SELECT * FROM interviews WHERE session_id=?", (session_id,)).fetchone()
    if not interview:
        conn.close()
        raise HTTPException(404, "Interview session not found")

    stored = json.loads(interview["questions_json"])
    if isinstance(stored, dict):
        questions = stored.get("questions", [])
        correct_answers = stored.get("correct_answers", {})
    else:
        questions = stored
        correct_answers = {}
    index = interview["current_index"]
    question = questions[index]
    predefined_answer = correct_answers.get(question, "")
    profile = {"name": interview["name"], "target_role": interview["target_role"], "skills": interview["skills"]}
    feedback = ai_feedback(question, req.answer, profile, predefined_answer)

    conn.execute("""INSERT INTO answers
        (session_id, question_number, question, user_answer, score, correct_answer,
         mistake_analysis, strengths, missing_points, improvement, model_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, index + 1, question, req.answer, float(feedback["score"]),
         feedback["correct_answer"], feedback["mistake_analysis"], feedback["strengths"],
         feedback["missing_points"], feedback["improvement"], feedback["model_answer"]))

    next_index = index + 1
    conn.execute("UPDATE interviews SET current_index=? WHERE session_id=?", (next_index, session_id))
    conn.commit()

    completed = next_index >= len(questions)
    if completed:
        report = build_report(conn, session_id)
        conn.close()
        return {"completed": True, "feedback": feedback, "report": report}

    next_question = questions[next_index]
    conn.commit()
    conn.close()
    return {
        "completed": False,
        "feedback": feedback,
        "question": next_question,
        "question_number": next_index + 1
    }

@app.get("/interviews/{session_id}/current")
def current_question(session_id: str):
    conn = db()
    interview = conn.execute("SELECT * FROM interviews WHERE session_id=?", (session_id,)).fetchone()
    if not interview:
        conn.close()
        raise HTTPException(404, "Interview session not found")
    stored = json.loads(interview["questions_json"] or "{}")
    questions = stored.get("questions", []) if isinstance(stored, dict) else stored
    idx = int(interview["current_index"] or 0)
    if idx >= len(questions):
        conn.close()
        return {"completed": True, "question": "", "question_number": len(questions)}
    q = questions[idx]
    conn.close()
    return {"completed": False, "question": q, "question_number": idx + 1, "total_questions": len(questions)}

@app.get("/interviews/{session_id}/report")
def report(session_id: str):
    conn = db()
    result = build_report(conn, session_id)
    conn.close()
    return result
