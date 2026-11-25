# TripMate AI Security & Prompt Injection Defense

## Principles of AI Defense-in-Depth
1. **Instruction / Data Separation**: User inputs and retrieved external documents are strictly demarcated as untrusted payload rather than system instructions.
2. **Prompt Guard**: Dedicated filtering layer (`app/security/prompt_guard.py`) inspecting incoming payloads for jailbreak tokens, system override attempts, and delimiters.
3. **Tool Isolation**: Strict argument schema validation via Pydantic; LLM outputs never directly invoke shell commands or arbitrary code.
4. **Credential Safeguarding**: Environment variables and database secrets are never exposed to agents or returned in API error responses.
5. **Human Approval Gateway**: Financial actions or external bookings require explicit human confirmation.

