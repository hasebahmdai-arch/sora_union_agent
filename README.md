# Shopify Order Assist

An AI-powered customer support agent for an e-commerce store. Built with LangChain, Gemma 4 (Gemini API), FastAPI, SQLite, and plain HTML/JS.

## What It Does

The assistant handles common tier-1 customer support queries autonomously:

- **Order tracking** — list orders, filter by status, look up details by order ID
- **Refund eligibility** — checks if an order is within the 30-day return window
- **FAQ answers** — returns, shipping times, payment methods, account issues
- **Support tickets** — creates a ticket when human follow-up is needed
- **User context** — fetches authenticated user info from the real users table

## Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| LLM      | Gemma 4 (`gemma-4-31b-it`) via Gemini API |
| Agent    | LangChain + LangGraph (ReAct agent) |
| Backend  | FastAPI + SQLite + JWT auth         |
| Frontend | HTML + CSS + JavaScript             |

## Setup

### 1. Clone and navigate
```bash
cd sora_union
```

### 2. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```

Edit `.env`: set `GOOGLE_API_KEY`, `JWT_SECRET` (use a long random string in production).

Get an API key at: https://aistudio.google.com/app/apikey

### 4. Run the backend
```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 5. Open the frontend

Open `frontend/index.html` in your browser, or use a local server:
```bash
python -m http.server 3000 --directory frontend
```

Register or sign in. The app includes:
- login/register screen
- chat sidebar with conversation list
- markdown rendering for assistant replies

## Project Structure

```
sora_union/
├── backend/
│   ├── main.py        # FastAPI — auth, chat, sessions, history
│   ├── agent.py       # LangGraph ReAct agent
│   ├── auth.py        # JWT + password hashing
│   ├── database.py    # SQLite users + messages + session grouping
│   ├── tools.py       # LangChain tools
│   ├── mock_data.py   # In-memory orders and FAQs
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   └── app.js
├── .env.example
└── README.md
```

## API

Sign in with `POST /auth/login` or `POST /auth/register` (JSON body: `email`, `password`). Use `Authorization: Bearer <token>` on protected routes.

### `GET /auth/me`
Returns authenticated user identity.

### `GET /sessions`
Returns the current user's chat sessions for sidebar display.

### `POST /chat`
```json
{ "message": "What orders do I have?", "session_id": "chat-optional-id" }
```

`session_id` is optional. If omitted, backend creates a new chat session.

### `GET /history?session_id=...`
Returns messages for one authenticated user session.

### `DELETE /history?session_id=...`
Deletes one session history. If `session_id` is omitted, deletes all history for the current user.

### `GET /health`
```json
{ "status": "ok" }
```

## Sample Queries

| Query | Tool |
|-------|------|
| "What orders do I have?" | `list_orders` |
| "Where is order ORD-1001?" | `lookup_order` |
| "Who am I logged in as?" | `get_current_user_info` |
| "What is your return policy?" | `search_faq` |
| "I need human help" | `create_support_ticket` |

## Problem Framing

### What problem?
E-commerce support teams are overloaded with repetitive tier-1 queries such as order status, refund eligibility, and return policy questions. These requests are structured and tool-friendly, but they still consume human support capacity.

### Why it matters
For teams processing high ticket volume, automating a meaningful share of tier-1 requests can reduce support costs and improve response latency from hours to near-instant replies.

### Who are the users?
- **End customers** who need fast, accurate answers at any time.
- **Support teams/business operators** who want lower operational load and faster escalations for complex cases.

## Solution Overview

The assistant receives a free-text message, chooses tool calls through a ReAct loop, executes those tools, and returns a natural-language response.  
For example: "Can I get a refund on ORD-1002?" triggers `lookup_order`, which checks delivery timing and returns refund eligibility details in one tool call.

## How It Is Structured

- LangGraph `create_react_agent` runs the ReAct loop (reason -> act -> observe -> respond).
- LLM is Gemma 4 (`gemma-4-31b-it`) via Gemini API.
- Tools are defined with LangChain `@tool`:
  - `list_orders`
  - `lookup_order`
  - `search_faq`
  - `create_support_ticket`
  - `get_current_user_info` (real authenticated user data from DB, not mock data)
- FastAPI provides auth, chat, sessions, and history endpoints.
- Frontend is plain HTML/CSS/JS with session sidebar and markdown-rendered assistant output.

## Tradeoffs and Limitations

- Order/FAQ domain data is still mock data; production should wire tools to real OMS/support APIs.
- Responses are not token-streamed (no SSE/WebSocket streaming yet), so users wait for full completion.
- FAQ retrieval uses keyword matching; semantic retrieval (embeddings + vector index) would improve paraphrase handling.
- Session memory is persisted per user/session in SQLite and suited for local/demo usage; production should use managed storage and stronger observability.

## Iteration Notes

- Earlier designs often split refund checks into separate tool calls, increasing round trips.
- Consolidating refund logic into `lookup_order` reduced tool hops and improved response speed/consistency.

## Next Improvements

1. Add streaming responses or websockets for better perceived latency.
2. Replace keyword FAQ lookup with embedding-based semantic search.
3. Integrate real order and ticketing backends instead of mock datasets.
4. Add production-grade monitoring/rate limiting and deployment hardening.
