---
name: master
description: SOLIDS FOR YOU Master Skill: hands each task to one of five heads (Product, Ecom, Marketing, Design, Review) that use only the tools it needs, and runs the full video workflow. Use to make or edit any video (reel, ad, explainer, animation, product video, GIF), for multi-tool tasks, or when asked for the Master Skill.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. If the toolbox is not already in your context, read `SKILL_DIR/toolbox.md`
   now. Keep it in mind for the rest of the conversation; don't re-read it for
   each task. (In Claude Code's default always-on mode it is loaded at session
   start; see `SKILL_DIR/master.md` section 2.)
2. Pick the head for the task from the toolbox and follow its file:
   `SKILL_DIR/heads/product.md`, `ecom.md`, `marketing.md`, `design.md` or
   `review.md`. Each head calls only the sub-skills it needs and hands work
   to the other heads. A task with several parts uses each part's head.
3. To make a video, go straight to `SKILL_DIR/workflows/video.md` (the
   Design head's video path) and follow it from start to finish. Its build
   tools are in `SKILL_DIR/templates/` and `SKILL_DIR/scripts/`.
4. For the rules every head shares, or a question about how the Master
   Skill works or how to change its mode, read `SKILL_DIR/master.md`.
5. The sub-skills are separate SOLIDS FOR YOU skills: economy-mode,
   careful-mode, harsh-buyer-review, motion-design-taste, audio-review,
   social-media, competitor-research, ecom, ai-visuals and transcriber.
   When a head needs one, invoke it. If it is missing, tell the user once how
   to add it (`/plugin install <name>@solidsforyou` in Claude Code), then do
   the closest thing you can.
6. Work in a scratch directory or the user's project folder, never inside
   the plugin folder.
