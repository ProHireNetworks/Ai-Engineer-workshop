chat_sessions = {
    "session_101": [
        {"role": "user", "content": "My name is Ravi."}
    ],
    "session_202": [
        {"role": "user", "content": "My name is Sita."}
    ]
}


def add_message(session_id, role, message):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_sessions[session_id].append({
        "role": role,
        "content": message
    })


add_message("session_101", "user", "What is my name?")
add_message("session_101", "assistant", "Your name is Ravi.")

add_message("session_202", "user", "What is my name?")
add_message("session_202", "assistant", "Your name is Sita.")


for session_id, history in chat_sessions.items():
    print(f"\n{session_id}:")

    for message in history:
        print(message["role"], ":", message["content"])