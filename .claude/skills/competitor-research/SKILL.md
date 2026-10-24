---
name: competitor-research
description: Evidence-based competitor research on marketplaces (Amazon, Flipkart, Meesho and more), competitor websites, social media and ad libraries: every fact sourced, verified and computed by script, run by cheap Haiku helpers. Use for competitors, market or pricing research, benchmarking, or competitor data before feedback. Analysis only, no copy.
---

This lets the tool work in sessions opened inside this repository. The real
skill ships as a plugin. Read `plugins/competitor-research/skills/competitor-research/SKILL.md` and follow it.
Wherever that file refers to `SKILL_DIR` or to the skill's own folder, use
`plugins/competitor-research/skills/competitor-research` (relative to the repository root).
Its helpers are defined in `plugins/competitor-research/agents/`; when they
aren't loaded as agents, give a general-purpose helper with model `haiku`
the helper file's instructions instead.
