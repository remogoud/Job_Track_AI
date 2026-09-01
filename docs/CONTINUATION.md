# Continuation & Resuming — Job_Track_AI

The project is designed so a lost session or exhausted quota never loses work.

## How to resume in another Arena AI account
1. Run `python scripts/continue_handoff.py --out continue_prompt.txt`.
2. Open `continue_prompt.txt` (or copy the output). It contains:
   - the milestone,
   - completed modules,
   - next steps,
   - a ready-to-paste **`CONTINUE`** prompt.
3. Paste that prompt into a fresh Arena AI account. The new session reads
   `PROMPTS.md` (the preserved full spec) and `data/continuation.json` (the build
   status) to pick up exactly where things left off — no need to re-write the
   specification.

## The `CONTINUE` keyword
`core/agentic/orchestrator.py` implements the handoff:
- `continuation()` returns a `ContinuationPacket`.
- `save_continuation()` writes `data/continuation.json`.

## If the whole repo/spec is lost
`PROMPTS.md` at the repo root is the complete archive of:
- the detailed prompt,
- the workflow,
- the database schema,
- the git strategy,
- the consolidated constraints,
- the feasibility clarifications,
- and the build trigger.

Restart from it verbatim and you will regenerate the same application.

## Safe restart checklist
- `data/continuation.json` — build status (auto-written).
- `PROMPTS.md` — full spec.
- `docs/*` — architecture, features, security, dependencies, rebuild.
- Git history on `dev`/`main` is the source of truth for what's committed.
