---
name: economy-mode
description: Turn on economy mode, which routes low-importance work to cheaper, faster models (Haiku, Sonnet) through subagents and keeps the most capable model for tasks that need judgment. Use when the user says "economy mode", "save tokens", "use cheaper models", "/economy-mode", or asks to cut cost.
---

This lets the tool work in sessions opened inside this repository. The real
skill ships as a plugin. Read `plugins/economy-mode/skills/economy-mode/SKILL.md` and follow it.
Wherever that file refers to `SKILL_DIR` or to the skill's own folder, use
`plugins/economy-mode/skills/economy-mode` (relative to the repository root).
