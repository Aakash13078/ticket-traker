"""Deterministic business rules applied AFTER the model. The LLM proposes,
the rules decide: anything risky is escalated or sent to a human."""
from __future__ import annotations

from .schema import PRIORITIES, TEAMS, Classification, Ticket, TriageResult

CONFIDENCE_THRESHOLD = 0.7
# Categories where a wrong automated reply is costly: never auto-send.
NO_AUTO_REPLY = {"security", "billing", "outage"}


def _bump(priority: str) -> str:
    i = PRIORITIES.index(priority)
    return PRIORITIES[max(i - 1, 0)]


def apply_guardrails(ticket: Ticket, c: Classification, pii_found: list[str]) -> TriageResult:
    flags: list[str] = []
    priority, team = c.priority, c.team

    # Validate model output against the closed vocabularies.
    if priority not in PRIORITIES:
        flags.append("invalid_priority")
        priority = "medium"
    if team not in TEAMS:
        flags.append("invalid_team")
        team = "support_l1"

    # Enterprise customers get one priority level up (SLA), capped at "high":
    # "urgent" is reserved for outages/security so the on-call page stays meaningful.
    if ticket.tier == "enterprise" and priority in ("medium", "low"):
        priority = _bump(priority)
        flags.append("enterprise_sla_bump")

    # Security is always urgent and always owned by security, regardless of model output.
    if c.category == "security":
        priority, team = "urgent", "security"
        flags.append("security_override")

    if pii_found:
        flags.append("pii_redacted:" + ",".join(pii_found))

    needs_review = c.confidence < CONFIDENCE_THRESHOLD
    if needs_review:
        flags.append("low_confidence")
    if c.source == "heuristic":
        flags.append("offline_classifier")

    auto_reply = (
        not needs_review
        and c.category not in NO_AUTO_REPLY
        and priority in ("low", "medium")
        and c.source == "claude"
    )

    return TriageResult(
        ticket_id=ticket.id,
        classification=c,
        final_priority=priority,
        final_team=team,
        needs_human_review=needs_review or c.category in NO_AUTO_REPLY,
        flags=flags,
        auto_reply_allowed=auto_reply,
    )
