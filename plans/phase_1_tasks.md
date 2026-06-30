# PHASE 1: Task System (Days 2–5)

**Goal**: Full task lifecycle works end to end.

## Day 2 — Registration + Modules
- [ ] Build `/register @person [role]` in `admin.py` (upsert into `team_members`, confirm with embed).
- [ ] Build `/module-create` in `modules.py` (modal: name, client name, deadline; insert into `modules`).
- [ ] Build `/module-list`.

## Day 3 — Core Task Commands
- [ ] Build `/task-create` in `tasks.py` (modal: title, description (optional), module (select), due date, estimate hours; insert into `tasks`).
- [ ] Build `/task-assign @person [task-id]`.
- [ ] Build `/task-list` with filter options.

## Day 4 — Task Lifecycle
- [ ] Build `/task-start [task-id]` (check caller is the assignee; update status to 'in_progress', set `started_at`).
- [ ] Build `/task-done [task-id]` (check if past `due_date` → if yes, open slip reason modal; update task, log event).
- [ ] Build `/pickup` (query unassigned tasks; show paginated list with select menu; assign selected task to caller).

## Day 5 — Supporting Commands
- [ ] `/task-update [task-id]` — progress note modal.
- [ ] `/task-view [task-id]` — full task embed.
- [ ] `/task-block [task-id]` — mark blocked, prompt to file blocker.
- [ ] `/my-tasks` — list caller's in-progress tasks.
- [ ] `/module-status [module]` — tasks in module by status.

**Done when**: Founders can create tasks, assign to interns, interns can start/update/complete them, slippage is tracked.
