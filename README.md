# AI Interview Preparation & Simulation Bot — V3

A resume-ready interview simulator built with **Streamlit + FastAPI + SQLite + OpenAI API**.

## V3 features

- Login page
- Create Account page
- Secure password hashing with PBKDF2-HMAC-SHA256 + per-user salt
- Persistent user profile stored in SQLite
- Profile automatically loaded after login
- Target role and skills saved for future sessions
- Technical, HR, and Mixed interviews
- Easy / Medium / Hard difficulty selection
- AI answer evaluation
- Correct / expected answer
- Explicit mistake analysis
- Missing points
- Improvement suggestions
- Interview-ready model answer
- Final interview report
- Question-wise review
- User-specific interview history
- Automatic database migration from the V2 `interviews` table

## Project structure

```text
AI_Interview_Preparation_Bot_v3/
├── app.py
├── api_server.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 1. Open the project

Extract the ZIP and open the folder in VS Code.

## 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 3. Install packages

```bash
pip install -r requirements.txt
```

## 4. Add your OpenAI API key

Open `.env` and add:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
API_URL=http://127.0.0.1:8000
DATABASE_PATH=interviews.db
```

Do not share or commit your API key.

If no API key is configured, the application still runs using a basic fallback evaluator.

## 5. Start the backend

Open Terminal 1:

```bash
.venv\Scripts\activate
uvicorn api_server:app --reload --port 8000
```

Backend:
`http://127.0.0.1:8000`

## 6. Start the frontend

Open Terminal 2:

```bash
.venv\Scripts\activate
streamlit run app.py
```

Streamlit normally opens:
`http://localhost:8501`

## 7. Use the application

### First time

1. Open the Streamlit page.
2. Select **Create Account**.
3. Enter name, username, password, target role, and skills.
4. Click **Create Account**.
5. Login with the same username and password.

### Next time

Your account information is already stored in `interviews.db`. Login again and the saved name, target role, and skills will load automatically.

### Interview flow

1. Select Technical, HR, or Mixed.
2. Select difficulty.
3. Select number of questions.
4. Start the interview.
5. Submit each answer.
6. Review:
   - Score
   - Correct / expected answer
   - Mistake analysis
   - Missing points
   - Improvement suggestions
   - Interview-ready model answer
7. After the final question, view the complete report.
8. Open **My History** to see previous interview attempts.

## Database

SQLite creates `interviews.db` automatically.

Tables:

- `users` — account/profile information
- `interviews` — interview sessions and final scores
- `answers` — question-wise answers and AI feedback

Passwords are **not stored as plain text**.

## Important

For a real production deployment, add stronger authentication/session management, HTTPS, rate limiting, CSRF protection, and a production database. This version is designed as a college/resume project and local demo.

## Resume description

**AI Interview Preparation & Simulation Bot | Python, Streamlit, FastAPI, OpenAI API, SQLite**

- Developed an AI-powered interview simulator with login, persistent user profiles, technical/HR interview modes, and personalized question evaluation.
- Built a FastAPI backend and Streamlit frontend with SQLite-based user accounts and interview history.
- Integrated an LLM to evaluate answers, identify mistakes and missing concepts, provide correct answers, and generate interview-ready responses.
- Implemented question-wise scoring, final performance reports, and personalized improvement recommendations.


## V5 UI upgrade
Modern responsive Streamlit interface with gradient hero, dashboard metrics, polished cards, badges, improved spacing, sidebar styling, and progress-oriented presentation. Core V4 predefined-answer evaluation and V3 login/history remain intact.
