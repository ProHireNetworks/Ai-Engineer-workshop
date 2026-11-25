"""
TripMate AI - Security Prompt Guard
Screens incoming user requests to prevent prompt injection, system override attempts,
data exfiltration, and malicious execution.
"""

import re
from typing import List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)",
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)",
    r"system\s*prompt",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"dan\s+mode",
    r"jailbreak",
    r"drop\s+table",
    r"union\s+select",
    r"<script[\s>]",
    r"javascript:",
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


class PromptGuardService:
    """Security sentinel detecting prompt injection and malicious override attempts."""

    @classmethod
    def scan_text(cls, text: str) -> Optional[str]:
        """
        Scans a text string for prompt injection patterns.
        Returns the matched threat description if malicious, else None.
        """
        if not text:
            return None

        for pattern in _COMPILED_PATTERNS:
            if pattern.search(text):
                matched = pattern.pattern
                logger.warning("Prompt injection detected by sentinel: matched '%s' in '%s'", matched, text[:80])
                return f"Prohibited pattern detected: '{matched}'"
        return None

    @classmethod
    def validate_request_content(cls, texts: List[Optional[str]]) -> None:
        """
        Validates multiple user input fields.
        Raises ValueError if any input violates security guardrails.
        """
        for t in texts:
            if t:
                violation = cls.scan_text(t)
                if violation:
                    raise ValueError(
                        f"Security policy violation: User input rejected by Prompt Guard sentinel ({violation})."
                    )

