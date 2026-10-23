---
name: careful-mode
description: Turn on careful mode, where Claude works as an extremely careful person and reviews every piece of work at least three times, in three separate passes, before submitting it. Use when the user says "careful mode", "be extremely careful", "triple check", "review everything", "/careful-mode", or when the work is high-stakes (customer-facing, money, prices, legal, production, anything hard to undo).
---

This lets the tool work in sessions opened inside this repository. The real
skill ships as a plugin. Read `plugins/careful-mode/skills/careful-mode/SKILL.md` and follow it.
Wherever that file refers to `SKILL_DIR` or to the skill's own folder, use
`plugins/careful-mode/skills/careful-mode` (relative to the repository root).
