"""Eval harness: compare pipeline output to labeled tickets. Run it on every
prompt/model change; this is what makes the system shippable."""
from __future__ import annotations

from .schema import Ticket, TriageResult


def evaluate(tickets: list[Ticket], results: list[TriageResult]) -> str:
    labeled = [(t, r) for t, r in zip(tickets, results) if t.label]
    if not labeled:
        return "No labeled tickets."
    n = len(labeled)
    cat = sum(r.classification.category == t.label["category"] for t, r in labeled)
    pri = sum(r.final_priority == t.label["priority"] for t, r in labeled)
    team = sum(r.final_team == t.label["team"] for t, r in labeled)

    # Safety metric: urgent tickets that were NOT routed as urgent are the costly misses.
    urgent = [(t, r) for t, r in labeled if t.label["priority"] == "urgent"]
    missed = [t.id for t, r in urgent if r.final_priority != "urgent"]

    lines = [
        f"Eval on {n} labeled tickets",
        f"  category accuracy: {cat}/{n} ({cat / n:.0%})",
        f"  priority accuracy: {pri}/{n} ({pri / n:.0%})",
        f"  team accuracy:     {team}/{n} ({team / n:.0%})",
        f"  urgent recall:     {len(urgent) - len(missed)}/{len(urgent)}"
        + (f"  MISSED: {missed}" if missed else ""),
    ]
    for t, r in labeled:
        if r.classification.category != t.label["category"] or r.final_priority != t.label["priority"]:
            lines.append(
                f"  mismatch {t.id}: got {r.classification.category}/{r.final_priority}, "
                f"expected {t.label['category']}/{t.label['priority']}"
            )
    return "\n".join(lines)
