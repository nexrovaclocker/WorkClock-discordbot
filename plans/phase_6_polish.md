# PHASE 6: Polish (Days 20–25)

**Goal**: Production-ready, robust, documented.

## Polish Tasks
- [ ] Add error handling everywhere — every DB call in a `try/except`.
- [ ] Handle Discord edge cases: user not found, channel deleted, DM failed (user has DMs closed).
- [ ] Add `/jarvis-status` health check command (scheduler running? last briefing? DB row counts?).
- [ ] Tune AI prompts based on 1–2 weeks of real output.
- [ ] Add rate limiting to the `#ops-brain` listener (max 1 query per 30 seconds).
- [ ] Write a `README.md` for the next person who touches this codebase.
