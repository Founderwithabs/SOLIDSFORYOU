---
name: master
description: The SOLIDS FOR YOU Master Skill. Use it at the start of EVERY task. It keeps all SOLIDS FOR YOU tools ready (economy mode, careful mode, harsh buyer review, motion design taste, audio review, video build tools) and picks only the ones a task needs: the full video workflow for making or editing any video (MP4, reel, ad, explainer, animation, motion graphic, product video, footage edit, GIF), harsh buyer review for feedback, careful research for research, and a direct answer for questions.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. If the toolbox is not already in your context (in Claude Code it is loaded
   at session start), read `SKILL_DIR/toolbox.md` now. Keep it in mind for
   the rest of the conversation; don't re-read it for each task.
2. Read `SKILL_DIR/master.md` and follow it: decide the task type, then use
   only the tools that type needs.
3. For a video task, read `SKILL_DIR/workflows/video.md` and follow it from
   start to finish. Its build tools are in `SKILL_DIR/templates/` and
   `SKILL_DIR/scripts/`.
4. The other tools are separate SOLIDS FOR YOU skills: economy-mode,
   careful-mode, harsh-buyer-review, motion-design-taste and audio-review.
   When a task needs one, invoke it. If it is missing, tell the user once how
   to add it (`/plugin install <name>@solidsforyou` in Claude Code), then do
   the closest thing you can.
5. Work in a scratch directory or the user's project folder, never inside
   the plugin folder.
