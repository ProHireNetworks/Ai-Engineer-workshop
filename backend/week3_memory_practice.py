chat_history = [
    {"role": "user", "content": "My name is Ravi."},
    {"role": "assistant", "content": "Hello Ravi!"},
]

chat_history.append({
    "role": "user",
    "content": "What is my name?"
})

# Simulate the AI response
chat_history.append({
    "role": "assistant",
    "content": "Your name is Ravi."
})

for message in chat_history:
    print(message["role"], ":", message["content"])