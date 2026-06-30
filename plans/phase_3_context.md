# PHASE 3: Context Accumulation (Days 10–11)

**Goal**: Every meaningful event in the system writes to `context_log`. Nothing falls through.

## Day 10 — Wire Up All Events
Go through every cog and add `jarvis_ai.log_event()` after every state change:

### clock.py (tracking.py):
- [ ] After `WorkDescriptionModal` saves: `log_event("session_end", content=f"{name} worked Xh: [first 80 chars of description]")`

### tasks.py:
- [ ] `/task-create` → `log_event("task_create", ...)`
- [ ] `/task-assign` → `log_event("task_assign", ...)`
- [ ] `/task-start` → `log_event("task_start", ...)`
- [ ] `/task-done` → `log_event("task_complete", ...)`
- [ ] `/task-done` (slipped) → `log_event("task_slip", ...)`
- [ ] `/pickup` → `log_event("task_pickup", ...)`
- [ ] `/task-block` → `log_event("task_block", ...)`

### standups.py:
- [ ] After `/standup` saves → `log_event("standup", content=one-line summary of all 3 answers)`

### blockers.py:
- [ ] `/blocker` → `log_event("blocker_open", ...)`
- [ ] `/blocker-resolve` → `log_event("blocker_resolve", content=f"[name] resolved blocker '{description}' after {hours:.1f}h. Resolution: [note]")`

### demo.py:
- [ ] `/demo-update` → `log_event("demo_update", content=f"[name] updated '{feature}' to {status}: [note]")`

## Day 11 — Handoff Commands + Manual Context
- [ ] Build `/context-add` in `admin.py` (modal: content, type (client/decision/risk/general); insert to `manual_context`; log to `context_log` as well).
- [ ] Build `/context @person` in `intelligence.py` (query: active tasks, recent sessions, open blockers, completed task titles (skills proxy); format as rich embed).
- [ ] Build `/context-task [task-id]` (all task_updates, status history, who's worked on it, blockers linked to it).

**Done when**: Every event in the system is in `context_log`. Query the table and it should read like a team activity log.
