# PHASE 2: Daily Operations (Days 6–9)

**Goal**: Standups, blockers, and demo readiness all working.

## Day 6 — Standup Command
- [ ] Build `/standup` in `standups.py` (modal: "What did you work on?", "What's your focus today?", "Any blockers or risks?"; save to `standups` table; post summary to `#standup` channel).
- [ ] Build `/standup-missed` (admin, lists who hasn't submitted today).
- [ ] Build `/standup-view @person` (last 5 standups as embeds).

## Day 7 — Standup Scheduler
- [ ] Set up `APScheduler` in `scheduler.py`.
- [ ] 10am IST weekday job: DM everyone in `team_members` who hasn't submitted today's standup.
- [ ] Test by temporarily setting it to 1 minute from now.

## Day 8 — Blocker System
- [ ] Build `/blocker` in `blockers.py` (modal: describe, which task (optional), who's blocking (optional); insert to `blockers`, update task if `task_id` given; DM blocking person if set).
- [ ] Build `/blocker-resolve [id]` (modal: how was it resolved?; update blocker record, calculate `hours_open`).
- [ ] Build `/blockers-open` and `/blockers-mine`.

## Day 9 — Demo Readiness
- [ ] Build `/demo-add` in `demo.py` (modal: feature name, description, link to module; insert to `demo_features`).
- [ ] Build `/demo-update [feature]` (select: ready / partial / not_ready; text input: status note).
- [ ] Build `/demo-ready` (query all `demo_features`; calculate %: (ready * 1 + partial * 0.5) / total * 100; show traffic light per feature; show overall score; show recommendation).

**Done when**: Standups DM at 10am, blockers tracked with DM notifications, demo readiness is visible with one command.
