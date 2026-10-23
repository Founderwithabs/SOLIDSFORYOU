---
name: master
description: SOLIDS FOR YOU Master Skill: routes each task to only the SOLIDS FOR YOU tools it needs and runs the full video workflow. Use to make or edit any video (reel, ad, explainer, animation, product video, GIF), for tasks that combine several SOLIDS FOR YOU tools, or when asked for the Master Skill.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. If the toolbox is not already in your context, read `SKILL_DIR/toolbox.md`
   now. Keep it in mind for the rest of the conversation; don't re-read it for
   each task. (In Claude Code's default always-on mode it is loaded at session
   start; see `SKILL_DIR/master.md` section 2.)
2. For a video task, go straight to `SKILL_DIR/workflows/video.md` and
   follow it from start to finish; you don't need `master.md` for it. Its
   build tools are in `SKILL_DIR/templates/` and `SKILL_DIR/scripts/`.
3. For anything else (a task that combines several tools, or a question
   about how the Master Skill works or how to change its mode), read
   `SKILL_DIR/master.md` and follow it.
4. The other tools are separate SOLIDS FOR YOU skills: economy-mode,
   careful-mode, harsh-buyer-review, motion-design-taste, audio-review,
   social-media and competitor-research.
   When a task needs one, invoke it. If it is missing, tell the user once how
   to add it (`/plugin install <name>@solidsforyou` in Claude Code), then do
   the closest thing you can.
5. Work in a scratch directory or the user's project folder, never inside
   the plugin folder.
