# AI Support-Ticket Triage Workflow

**Problem:** Support teams drown in a shared inbox. Urgent issues (outages, security) wait behind
"how do I export a CSV?", agents re-read every ticket to route it, and customers wait hours for a first reply.

**Solution:** An LLM-in-the-loop pipeline that classifies, prioritizes, routes and drafts replies,
with deterministic guardrails and a human-review queue so automation never becomes a liability.

```
ticket -> PII redaction -> Claude (tool-use, structured) -> guardrails -> per-team queues
                                  |                              |-> human_review.jsonl
                          offline heuristic fallback             '-> audit_log.json
```

## Design decisions (the forward-deployed part)

| Decision | Why |
|---|---|
| Structured output via forced tool-use + enums | No JSON parsing failures; model can't invent teams or priorities |
| PII redacted before the model call | Customer data minimization; works for regulated clients |
| LLM proposes, rules decide | Security => always urgent; enterprise SLA bump capped at "high"; business policy stays in code, not prompts |
| Confidence threshold (0.7) -> human review | Vague tickets never get auto-handled |
| Never auto-reply on security/billing/outage | A wrong automated reply there is costly |
| Fallback classifier on API failure | A ticket is never dropped; degraded results are forced to human review |
| Ticket text treated as untrusted | Prompt-injection resistant prompt + guardrails that the model cannot override |
| Audit log of every decision + flags | Explainability for support leads and compliance |
| Eval harness incl. **urgent recall** | Measure the miss that matters most; rerun on every prompt/model change |

## Run it

```bash
python main.py --offline --eval        # no API key needed (keyword heuristic)

pip install anthropic
export ANTHROPIC_API_KEY=...           # optional: TRIAGE_MODEL to override the model
python main.py --eval                  # uses Claude
python -m pytest -q
```

Outputs land in `out/`: `queue_<team>.jsonl`, `human_review.jsonl`, `audit_log.json`.

## Extending to production

1. **Ingest:** replace `load_tickets` with a Zendesk/Freshdesk/Gmail webhook (idempotent on ticket id).
2. **Deliver:** replace the JSONL queues with API calls (assign team, set priority, post the draft as an internal note).
3. **Scale:** run `triage_one` via a task queue; use the Message Batches API for backlogs; cache the system prompt.
4. **Learn:** log agent corrections to the draft/labels, grow `data/` into a real eval set, track
   auto-reply acceptance rate, human-review rate and urgent recall weekly.
5. **Rollout:** shadow mode first (suggest only), then auto-route low-risk categories, then auto-reply for low priority only.
