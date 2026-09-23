from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Channel(str, Enum):
    whatsapp = "whatsapp"
    email = "email"
    web = "web"
    voice = "voice"


class LeadStatus(str, Enum):
    new = "new"
    qualifying = "qualifying"
    qualified = "qualified"
    nurture = "nurture"
    human_handoff = "human_handoff"
    closed = "closed"


class Lead(BaseModel):
    id: str
    name: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    channel: Channel = Channel.web
    requirements: list[str] = Field(default_factory=list)
    budget: str | None = None
    location: str | None = None
    team_size: int | None = None
    score: int = 0
    status: LeadStatus = LeadStatus.new
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Message(BaseModel):
    lead_id: str
    role: str
    content: str
    channel: Channel = Channel.web
    created_at: datetime = Field(default_factory=now_utc)


class AgentRequest(BaseModel):
    lead_id: str | None = None
    name: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    channel: Channel = Channel.web
    message: str


class AgentResponse(BaseModel):
    lead_id: str
    reply: str
    lead: Lead
    actions: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str


class EvaluationScenario(BaseModel):
    id: str
    name: str
    messages: list[str]
    required_behaviors: list[str] = Field(default_factory=list)
    forbidden_behaviors: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    scenario_id: str
    passed: bool
    score: float
    checks: dict[str, bool]
    transcript: list[dict[str, str]]
    notes: list[str] = Field(default_factory=list)
