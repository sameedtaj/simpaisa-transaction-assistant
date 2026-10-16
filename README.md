# SIMPAISA Transaction Assistant

Ask transaction-related questions in natural language. The assistant converts your question into **read-only PostgreSQL**, runs it through an **MCP server**, and shows the result in a **Streamlit** chat interface.

Example: *"Give me successful transaction count for June 2026"* → returns `successful_transactions: 4674` along with the generated SQL.

---

## How it works

```
User (Streamlit UI)
      │  question
      ▼
FastAPI backend  ──►  OpenAI agent (writes SQL)
      │                     │
      │◄── guardrails check (read-only, safe SQL)
      ▼
MCP client  ──►  MCP server  ──►  PostgreSQL
      │
      ▼
Result + generated SQL shown in the UI
```

---

## Project structure

```
MCP Project database/
│
├── backend/                 # FastAPI backend
│   ├── __init__.py
│   ├── app.py               # API entry point (/health, /chat)
│   ├── guardrails.py        # Blocks unsafe / non read-only SQL
│   ├── mcp_client.py        # Talks to the MCP server
│   ├── openai_agent.py      # Converts questions into SQL using OpenAI
│   ├── prompts.py           # System prompts for the agent
│   └── schema.py            # Database schema description given to the agent
│
├── frontend/                # Streamlit chat UI
│   ├── __init__.py
│   └── streamlit_app.py
│
├── mcp_server/              # MCP server that executes queries
│   ├── __init__.py
│   ├── db.py                # PostgreSQL connection
│   └── server.py            # MCP tools exposed to the client
│
├── .env.example             # Template for environment variables (no real secrets)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

Copy `.env.example` to `.env` and fill in your own values:

```bash
copy .env.example .env
```

The `.env` file is **not** stored in this repository because it contains secrets.

---

## Running the app

Open **two** terminals in the project folder.

**Terminal 1 — backend (FastAPI):**

```bash
python -m uvicorn backend.app:app --reload
```

Runs at `http://127.0.0.1:8000` (health check: `/health`).

**Terminal 2 — frontend (Streamlit):**

```bash
python -m streamlit run frontend/streamlit_app.py
```

Opens at `http://localhost:8501`.

---

## Safety

- Only **read-only** SQL is allowed; `guardrails.py` rejects `INSERT`, `UPDATE`, `DELETE`, `DROP` and similar statements.
- Credentials live only in `.env`, which is excluded from Git.

---

## Tech stack

Python · FastAPI · Streamlit · OpenAI API · MCP (Model Context Protocol) · PostgreSQL
