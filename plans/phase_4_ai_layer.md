# PHASE 4: AI Layer (Days 12–16)

**Goal**: All AI features working. Morning briefing DMs Subrat at 9am.

## Day 12 — AI Engine Setup
- [ ] Install `openai` library and configure the Azure OpenAI client (key/endpoint/deployment from Stuti).
- [ ] Build `JarvisAI` class skeleton in `ai_engine.py`.
- [ ] Implement `compile_context()` function (run it manually and print the output — check it's readable and under 6,000 tokens; tune truncation logic until it's good).
- [ ] Implement `log_event()` function.

## Day 13 — Morning Briefing
- [ ] Write `prompts/morning_briefing.txt`.
- [ ] Implement `morning_briefing()` function (compile live state; call Claude/Azure API with the prompt; return formatted text).
- [ ] Add to scheduler at 9am IST.
- [ ] Test by calling it manually.
- [ ] Fix and tune prompt until output matches expectations.

## Day 14 — #ops-brain Listener
- [ ] In `intelligence.py`, add `@commands.Cog.listener()` for `on_message` (check: `channel == OPS_BRAIN_CHANNEL_ID` AND `bot.user` in `message.mentions`; extract query; show typing; call `jarvis_ai.respond_to_query(query)`; public reply visible to whole team).
- [ ] Write `prompts/ops_brain.txt`.
- [ ] Test with: "@jarvis who's had the best week?".

## Day 15 — Profile + Growth
- [ ] Write `prompts/person_profile.txt`.
- [ ] Implement `generate_profile(user_id)` in `JarvisAI` (pull all tasks by this person, completion rate, estimate accuracy, session patterns, blockers; focus context on this person; call AI).
- [ ] Build `/profile @person` command in `intelligence.py`.
- [ ] Implement `generate_growth(user_id)` — same but sliced by week.
- [ ] Build `/growth @person` command.

## Day 16 — Delivery Check + Bottlenecks
- [ ] Write `prompts/delivery_prediction.txt`.
- [ ] Implement `delivery_check(module_id, target_date)` (pull open tasks, completed tasks (velocity), available assignees, open blockers; calculate tasks/week, working days until `target_date`, projected completion; send to AI with the math pre-computed).
- [ ] Build `/delivery-check` command.
- [ ] Build `/bottlenecks` — query `slip_reasons` categories + blocker `reporter_ids`, send to ops_brain prompt.

**Done when**: All AI commands work. Morning briefing posts to Subrat's DMs at 9am.
