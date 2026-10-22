# SOLIDSFORYOU

## Economy mode (cheaper models for less important tasks)

This repo ships an **economy mode** for Claude Code agents:

- Turn it on with `/economy-mode` (or say "economy mode on").
- It routes low-importance tasks to the `quick-task` subagent (Haiku) and
  routine tasks to the `standard-task` subagent (Sonnet), and keeps the main
  model for decisions, debugging, and final review.
- Turn it off by saying "economy mode off".

Definitions: `.claude/skills/economy-mode/SKILL.md` and `.claude/agents/`.

Even when economy mode is off, the `quick-task` and `standard-task` subagents
are available and may be used for clearly simple work.
