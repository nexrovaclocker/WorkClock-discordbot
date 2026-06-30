# PHASE 0: Setup & Migration (Day 1)

**Goal**: The existing bot works from the new structure. Nothing breaks.

## Tasks
- [x] Create the full folder structure (`main.py`, `config.py`, `utils.py`, `server.py`, `cogs/`).
- [x] Copy existing `main.py` content into the new structure.
- [x] Move clock-in/out commands into `cogs/clock.py` as a Cog class (Note: we used `tracking.py`).
- [x] Move stats commands into `cogs/stats.py` (Note: we used `reporting.py`).
- [x] Create `config.py` and replace all `os.environ.get()` calls to use it.
- [x] Create empty `cogs/__init__.py`.
- [ ] Run the full DB schema SQL in Supabase (all new tables: `team_members`, `modules`, `tasks`, `task_updates`, `standups`, `blockers`, `slip_reasons`, `context_log`, `jarvis_snapshots`, `demo_features`, `manual_context`).
- [ ] Set up `.env` with all variables.
- [ ] Test: `/clockin`, `/clockout`, `/teamstatus`, `/serverreport` all work.

**Done when**: Bot is online and all migrated commands work identically to before.
