from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Intent = Literal[
    "greeting",
    "order_tracking",
    "payment_issue",
    "current_time",
    "general_question",
    "unknown",
]
RiskProfile = Literal["low", "medium", "high", "unknown"]
Priority = Literal["low", "medium", "high"]


class IngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(
    default=None,
    min_length=1,
    max_length=100,
    description="Optional conversation session identifier"
)

    message: str = Field(
        min_length=1,
        max_length=5000,
        description="The user's original message.",
        examples=["Where is my order?"],
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot contain only whitespace.")
        return value


class TokenMetadata(BaseModel):
    estimated_input_tokens: int = Field(default=0, ge=0)
    note: str = "Estimated locally; may differ from provider token counts."


class IngestionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    risk_profile: RiskProfile
    priority: Priority
    requires_action: bool
    summary: str = Field(min_length=1, max_length=500)
    token_metadata: TokenMetadata = Field(default_factory=TokenMetadata)
