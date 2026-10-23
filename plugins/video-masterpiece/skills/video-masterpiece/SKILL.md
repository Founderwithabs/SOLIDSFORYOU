---
name: video-masterpiece
description: The master video workflow by SOLIDS FOR YOU. Use it EVERY time the output is a video of any kind (MP4, reel, short, ad, explainer, animation, motion graphic, title card, slideshow video, product video, footage edit, animated GIF), even if the user did not ask for it, and when the user says "make a video", "edit this video" or "/video-masterpiece". It chains economy mode, careful mode, motion design taste, audio review, motion-graphics building, harsh buyer review, a merged fix list and up to three rounds of regeneration until the video meets the quality bar.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Read `SKILL_DIR/video-masterpiece.md` and follow it exactly, stage by
   stage, until delivery.
2. It works best with the other SOLIDS FOR YOU skills installed:
   economy-mode, careful-mode, motion-design-taste, audio-review and
   harsh-buyer-review. When a stage names one, invoke that skill. If one is
   missing, tell the user once which one and how to add it
   (`/plugin install <name>@solidsforyou` in Claude Code), then follow that
   stage's own instructions.
3. Tools next to this file:
   - `SKILL_DIR/templates/scene-template.html`: copy it to start an HTML scene.
   - `SKILL_DIR/scripts/render_html_video.cjs`: render a scene page to video
     (needs Node.js, Playwright with Chromium, and ffmpeg).
   - `SKILL_DIR/scripts/sfx_mix.py`: build the sound-effects mix under the
     voiceover (needs ffmpeg and Python 3).
4. Work in a scratch directory or the user's project folder, never inside
   the plugin folder.
