"""Shared data types and taxonomy for the triage pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

CATEGORIES = [
    "outage", "security", "billing", "bug", "account_access",
    "how_to", "feature_request", "other",
]
PRIORITIES = ["urgent", "high", "medium", "low"]
TEAMS = ["sre", "security", "billing", "engineering", "product", "support_l1"]

# Default owning team per category; the classifier may override but must stay in TEAMS.
CATEGORY_TEAM = {
    "outage": "sre",
    "security": "security",
    "billing": "billing",
    "bug": "engineering",
    "account_access": "support_l1",
    "how_to": "support_l1",
    "feature_request": "product",
    "other": "support_l1",
}


@dataclass
class Ticket:
    id: str
    customer: str
    tier: str
    subject: str
    body: str
    label: Optional[dict] = None  # ground truth, only used by the eval harness


@dataclass
class Classification:
    category: str
    priority: str
    team: str
    confidence: float
    summary: str
    draft_reply: str
    reasoning: str = ""
    source: str = "claude"  # "claude" or "heuristic"


@dataclass
class TriageResult:
    ticket_id: str
    classification: Classification
    final_priority: str
    final_team: str
    needs_human_review: bool
    flags: list = field(default_factory=list)
    auto_reply_allowed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
