"""Orchestration: load -> redact -> classify -> guardrails -> route -> persist."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .classifier import classify
from .guardrails import apply_guardrails
from .pii import redact
from .schema import Ticket, TriageResult


def load_tickets(path: str) -> list[Ticket]:
    return [Ticket(**t) for t in json.loads(Path(path).read_text())]


def triage_one(ticket: Ticket, offline: bool = False) -> TriageResult:
    clean_body, pii = redact(ticket.body)
    classification = classify(ticket, clean_body, force_offline=offline)
    return apply_guardrails(ticket, classification, pii)


def run(tickets: list[Ticket], out_dir: str, offline: bool = False) -> list[TriageResult]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = [triage_one(t, offline=offline) for t in tickets]

    # One JSONL queue per destination team + a human review queue + an audit log.
    queues: dict[str, list[dict]] = {}
    for r in results:
        queues.setdefault(r.final_team, []).append(r.to_dict())
    for team, items in queues.items():
        (out / f"queue_{team}.jsonl").write_text("\n".join(json.dumps(i) for i in items) + "\n")

    review = [r.to_dict() for r in results if r.needs_human_review]
    (out / "human_review.jsonl").write_text("\n".join(json.dumps(i) for i in review) + ("\n" if review else ""))
    (out / "audit_log.json").write_text(json.dumps([r.to_dict() for r in results], indent=2))
    return results


def summarize(results: list[TriageResult]) -> str:
    n = len(results)
    by_team = Counter(r.final_team for r in results)
    by_pri = Counter(r.final_priority for r in results)
    review = sum(r.needs_human_review for r in results)
    auto = sum(r.auto_reply_allowed for r in results)
    lines = [
        f"Processed {n} tickets",
        f"  by priority: {dict(by_pri)}",
        f"  by team:     {dict(by_team)}",
        f"  human review: {review}/{n}   auto-reply eligible: {auto}/{n}",
    ]
    return "\n".join(lines)
