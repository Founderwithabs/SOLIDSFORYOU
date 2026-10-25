---
name: humanizer
description: Make writing sound like the founder, not a model: posts, captions, listings, emails, scripts and replies, in English, Hindi or Hinglish. Flags machine phrasing line by line, rewrites by channel, checks every fact survived, matches the founder's voice. Use for "humanize this", "sounds like AI", "make it sound like me", or before customers read anything.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. If the files came as text with no folder (for example from a
skill marketplace), save the ones a task needs to a temporary folder, never
the founder's project, and use that. Below, `SKILL_DIR` means that folder.

1. Print only what you need from the method:
   `python3 "SKILL_DIR/scripts/read_sections.py" "SKILL_DIR/humanizer.md" 1 2 4 5`
   (add 3 for the full pattern list, 6 for Hindi or Hinglish, 7 when matching
   the founder's voice, 8 for examples, 9 for the hand-back format).
2. Check, rewrite, check again, then confirm the facts, with
   `SKILL_DIR/scripts/humanize.py`:
   - `check draft.txt --channel <linkedin|instagram|x|email|listing|script|landing|reply>`
   - `compare draft.txt final.txt` (fails if a number, price, link or claim changed)
   - `voice samples.txt --draft final.txt` (when the founder's own writing is available)
   The patterns live in `SKILL_DIR/patterns.json`; edit it to add the
   founder's own pet phrases.
3. It needs only Python 3. Without a terminal, follow section 3 of the method
   by eye.
4. Never change a fact, never invent a story, and never promise text will
   pass an AI detector.
