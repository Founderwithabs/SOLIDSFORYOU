---
name: economy-mode
description: Economy mode: send low-importance work to cheaper models (Haiku, Sonnet) through helpers, keep the main model for judgment, and keep a memory sheet so Claude remembers decisions across sessions without carrying them. Use for "economy mode", "save tokens", "use cheaper models", "remember this", or cutting cost.
---

This lets the tool work in sessions opened inside this repository. The real
skill ships as a plugin. Read `plugins/economy-mode/skills/economy-mode/SKILL.md` and follow it.
Wherever that file refers to `SKILL_DIR` or to the skill's own folder, use
`plugins/economy-mode/skills/economy-mode` (relative to the repository root).
