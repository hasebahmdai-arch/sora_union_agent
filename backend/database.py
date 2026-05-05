import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "chat_history.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tools_used TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(messages)").fetchall()
        }
        if "session_id" not in cols:
            conn.execute("ALTER TABLE messages ADD COLUMN session_id TEXT")
            conn.execute(
                "UPDATE messages SET session_id = 'chat-legacy' WHERE session_id IS NULL OR session_id = ''"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON messages (user_id, session_id, created_at)"
        )
        _seed_demo_users(conn)


def _seed_demo_users(conn):
    from backend.auth import hash_password
    from backend.mock_data import DEMO_PASSWORD, DEMO_USER_EMAILS

    ph = hash_password(DEMO_PASSWORD)
    for email in DEMO_USER_EMAILS:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, password_hash) VALUES (?, ?)",
            (email, ph),
        )


def create_user(email: str, password_hash: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.lower().strip(), password_hash),
        )
        return int(cur.lastrowid)


def get_user_by_email(email: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def save_message(
    user_id: int,
    session_id: str,
    role: str,
    content: str,
    tools_used: list[str] | None = None,
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages (user_id, session_id, role, content, tools_used) VALUES (?, ?, ?, ?, ?)",
            (user_id, session_id, role, content, ",".join(tools_used or [])),
        )


def get_messages(user_id: int, session_id: str, limit: int = 20) -> list[tuple[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM messages
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, session_id, limit),
        ).fetchall()
    return [(role, content) for role, content in reversed(rows)]


def get_history(user_id: int, session_id: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT role, content, tools_used, created_at FROM messages
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at ASC
            """,
            (user_id, session_id),
        ).fetchall()
    return [
        {
            "role": row[0],
            "content": row[1],
            "tools_used": [t for t in row[2].split(",") if t],
            "created_at": row[3],
        }
        for row in rows
    ]


def clear_user_history(user_id: int, session_id: str | None = None):
    with sqlite3.connect(DB_PATH) as conn:
        if session_id is None:
            conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        else:
            conn.execute(
                "DELETE FROM messages WHERE user_id = ? AND session_id = ?",
                (user_id, session_id),
            )


def list_sessions(user_id: int) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT
                m.session_id,
                MAX(m.created_at) AS last_message_at,
                (
                    SELECT content
                    FROM messages m2
                    WHERE m2.user_id = m.user_id
                      AND m2.session_id = m.session_id
                      AND m2.role = 'human'
                    ORDER BY m2.created_at ASC
                    LIMIT 1
                ) AS title
            FROM messages m
            WHERE m.user_id = ?
            GROUP BY m.session_id
            ORDER BY last_message_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [
        {
            "session_id": row[0],
            "title": (row[2] or "New chat")[:60],
            "last_message_at": row[1],
        }
        for row in rows
    ]
