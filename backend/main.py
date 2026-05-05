import sqlite3
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import agent
from backend.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.callbacks import ToolLogger
from backend import database as db
from backend.tools import current_user_email, current_user_id

app = FastAPI(title="Shopify Order Assist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


class AuthBody(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    email: str


class MeResponse(BaseModel):
    id: int
    email: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    tools_used: list[str]
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=TokenResponse)
def auth_register(body: AuthBody):
    ph = hash_password(body.password)
    try:
        uid = db.create_user(body.email, ph)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered") from None
    token = create_access_token(uid, body.email.lower().strip())
    return TokenResponse(token=token, email=body.email.lower().strip())


@app.post("/auth/login", response_model=TokenResponse)
def auth_login(body: AuthBody):
    user = db.get_user_by_email(body.email)
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], user["email"])
    return TokenResponse(token=token, email=user["email"])


@app.get("/auth/me", response_model=MeResponse)
def auth_me(user: dict = Depends(get_current_user)):
    return MeResponse(id=user["id"], email=user["email"])


@app.get("/sessions")
def get_sessions(user: dict = Depends(get_current_user)):
    return {"sessions": db.list_sessions(user["id"])}


@app.get("/history")
def get_history(session_id: str, user: dict = Depends(get_current_user)):
    return {"messages": db.get_history(user["id"], session_id)}


@app.delete("/history")
def delete_history(session_id: str | None = None, user: dict = Depends(get_current_user)):
    db.clear_user_history(user["id"], session_id=session_id)
    return {"ok": True}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    uid = user["id"]
    session_id = (req.session_id or "").strip() or f"chat-{uuid4().hex}"
    history = db.get_messages(uid, session_id=session_id, limit=20)
    messages = history + [("human", req.message)]
    db.save_message(uid, session_id, "human", req.message)

    callback = ToolLogger()
    email_token = current_user_email.set(user["email"])
    id_token = current_user_id.set(uid)
    try:
        try:
            result = await agent.ainvoke(
                {"messages": messages},
                config={"callbacks": [callback]},
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        current_user_id.reset(id_token)
        current_user_email.reset(email_token)

    raw = result["messages"][-1].content
    if isinstance(raw, list):
        response_text = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw
        ).strip()
    else:
        response_text = raw

    db.save_message(uid, session_id, "ai", response_text, tools_used=callback.tools_used)

    return ChatResponse(
        response=response_text,
        tools_used=callback.tools_used,
        session_id=session_id,
    )
