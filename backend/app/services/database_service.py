
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL

MAX_HISTORY_MESSAGES = 12


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured in backend/.env")

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=8,
        row_factory=dict_row,
    )


def initialize_database() -> None:
    """Create the required tables if they do not already exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                conversation_id UUID NOT NULL
                    REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
            ON messages(conversation_id, created_at)
        """)


def ensure_conversation(
    session_id: str,
    title: str = "New Chat",
) -> None:
    now = _now()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (session_id, title[:100] or "New Chat", now, now),
        )


def add_chat_message(
    session_id: str,
    role: str,
    content: str,
) -> None:
    if role not in ("user", "assistant"):
        raise ValueError("Conversation role must be user or assistant")

    ensure_conversation(
        session_id,
        content[:70] if role == "user" else "New Chat",
    )

    now = _now()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, role, content, now),
        )
        conn.execute(
            """
            UPDATE conversations
            SET updated_at = %s,
                title = CASE
                    WHEN title = 'New Chat' AND %s = 'user'
                    THEN %s
                    ELSE title
                END
            WHERE id = %s
            """,
            (now, role, content[:70] or "New Chat", session_id),
        )


def get_chat_history(session_id: str) -> list[dict[str, str]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM (
                SELECT id, role, content, created_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
            ) AS recent
            ORDER BY created_at ASC, id ASC
            """,
            (session_id, MAX_HISTORY_MESSAGES),
        ).fetchall()

    return [{"role": row["role"], "content": row["content"]} for row in rows]


def list_conversations(limit: int = 30) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.title, c.updated_at,
                (
                    SELECT m.content
                    FROM messages AS m
                    WHERE m.conversation_id = c.id AND m.role = 'user'
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS preview
            FROM conversations AS c
            ORDER BY c.updated_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "session_id": str(row["id"]),
            "title": row["title"],
            "updated_at": row["updated_at"].isoformat(),
            "preview": row["preview"] or "Start a conversation",
        }
        for row in rows
    ]


def get_conversation_messages(
    session_id: str,
) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at, id
            """,
            (session_id,),
        ).fetchall()

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]


def clear_session(session_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM conversations WHERE id = %s",
            (session_id,),
        )
