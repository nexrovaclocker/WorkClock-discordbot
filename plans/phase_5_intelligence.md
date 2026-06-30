# PHASE 5: Weekly Intelligence (Days 17–19)

**Goal**: Friday narrative, weekly snapshots, session flags.

## Day 17 — Weekly Narrative
- [ ] Write `prompts/weekly_narrative.txt`.
- [ ] Implement `weekly_narrative(channel)` in `JarvisAI` (pull tasks completed this week, velocity vs last week, blockers opened/resolved, demo status; send to AI; post result to `#ops-brain`).
- [ ] Add to scheduler: Friday 6pm IST.
- [ ] Test manually first.

## Day 18 — Weekly Snapshots
- [ ] Implement `generate_weekly_snapshot()` in `JarvisAI` (for each team member compute week's stats; compress into a structured summary, save to `jarvis_snapshots`; for each module save status snapshot; add Sunday midnight IST job to scheduler).
- [ ] Update `compile_context()` to use these snapshots for weeks older than 7 days.

## Day 19 — Session Intelligence Flags
- [ ] In `clock.py` (or `tracking.py`), after `WorkDescriptionModal.on_submit` saves the session: run `is_quietly_struggling(description)` check; if True post publicly to `#ops-brain` with the flag message.
- [ ] Test with a session description containing "stuck" or "can't figure it out".

**Done when**: Jarvis posts Friday narratives, snapshots keep context manageable, session flags catch quiet struggles.
