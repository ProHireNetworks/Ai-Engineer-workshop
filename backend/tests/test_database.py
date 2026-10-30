
from uuid import uuid4
from unittest.mock import patch

import pytest

from app.services import database_service as db


def test_messages_are_saved_and_returned_in_order():
    session_id = str(uuid4())

    with patch.object(db, "_connect") as connect:
        conn = connect.return_value.__enter__.return_value

        db.add_chat_message(session_id, "user", "Where is my order?")
        db.add_chat_message(
            session_id, "assistant", "Let me explain how to track it."
        )

        assert conn.execute.call_count == 6


def test_history_is_limited_to_most_recent_messages():
    session_id = str(uuid4())

    with patch.object(db, "_connect") as connect:
        conn = connect.return_value.__enter__.return_value
        conn.execute.return_value.fetchall.return_value = [
            {"role": "user", "content": "message 1"},
            {"role": "assistant", "content": "message 2"},
        ]

        history = db.get_chat_history(session_id)

        assert len(history) == 2
        assert history[-1]["content"] == "message 2"


def test_conversation_title_comes_from_first_user_message():
    session_id = str(uuid4())

    with patch.object(db, "_connect") as connect:
        conn = connect.return_value.__enter__.return_value
        db.ensure_conversation(session_id, "My payment issue")

        conn.execute.assert_called_once()
        assert "INSERT INTO conversations" in conn.execute.call_args[0][0]


def test_invalid_role_is_rejected():
    with pytest.raises(ValueError):
        db.add_chat_message(str(uuid4()), "system", "not allowed")
