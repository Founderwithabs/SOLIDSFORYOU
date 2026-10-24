---
name: clipper
description: Clipping editor: turns long videos into vertical Shorts, Reels and TikToks for paid clipping campaigns or your own channel. Finds moments that stand alone, cuts them with word-by-word captions and a hook, follows the campaign brief, and tracks earnings. Use for "clip this", clipping campaigns, or Shorts from a long video.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Follow `SKILL_DIR/clipper.md`: the rules, the campaign brief, finding the
   moments, hook and words, cutting and checking, hand-back and tracking.
2. Transcribe with the `transcriber` skill, then use
   `SKILL_DIR/scripts/clip.py`:
   - `find transcript.json --min 20 --max 55`: ranked candidate spans to judge
   - `render video.mp4 transcript.json --spans 12.4-48.9,95-131 --hook "First|Second" --out-dir clips/`:
     vertical clips with captions, a hook line per clip and -14 LUFS sound
   It needs Python 3 and ffmpeg.
3. Words around each clip go through the `humanizer` skill, hooks through
   `social-media`'s `hookscore.py`, and the clip check through
   `motion-design-taste`'s `inspect_video.py` (all SOLIDS FOR YOU, if
   installed).
4. Only clip with permission, follow the campaign brief word for word, and
   never post, submit or log in for the founder.
