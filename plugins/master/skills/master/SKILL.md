---
name: master
description: The SOLIDS FOR YOU Master Skill. Use it for tasks that need SOLIDS FOR YOU tools: making, editing or reviewing a video, checking audio, social media work, feedback on a product, listing or ad, and research; or when the user asks for the Master Skill or "/master". It keeps all SOLIDS FOR YOU tools ready (economy mode, careful mode, harsh buyer review, motion design taste, audio review, social media, video build tools) and picks only the ones a task needs: the full video workflow for making or editing any video (MP4, reel, ad, explainer, animation, motion graphic, product video, footage edit, GIF), social media for posts, calendars and growth, harsh buyer review for feedback, careful research for research, and a direct answer for questions.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. If the toolbox is not already in your context, read `SKILL_DIR/toolbox.md`
   now. Keep it in mind for the rest of the conversation; don't re-read it for
   each task. (It is only in context from the start when the founder chose
   "always-on" mode; see `SKILL_DIR/master.md` section 2.)
2. Read `SKILL_DIR/master.md` and follow it: decide the task type, then use
   only the tools that type needs.
3. For a video task, read `SKILL_DIR/workflows/video.md` and follow it from
   start to finish. Its build tools are in `SKILL_DIR/templates/` and
   `SKILL_DIR/scripts/`.
4. The other tools are separate SOLIDS FOR YOU skills: economy-mode,
   careful-mode, harsh-buyer-review, motion-design-taste, audio-review and
   social-media.
   When a task needs one, invoke it. If it is missing, tell the user once how
   to add it (`/plugin install <name>@solidsforyou` in Claude Code), then do
   the closest thing you can.
5. Work in a scratch directory or the user's project folder, never inside
   the plugin folder.
