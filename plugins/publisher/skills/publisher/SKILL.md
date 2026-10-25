---
name: publisher
description: Posts your finished Reels to your own Instagram account through Instagram's official API and reads back views, reach, likes and audience countries. Checks captions against Instagram's limits; never uses your password. Use for "post this to Instagram", Reel stats, or audience countries for a campaign.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Follow `SKILL_DIR/publisher.md`: the rules, the one-time setup, publishing,
   reading results, keeping the token alive and the hand-back. Walk the
   founder through `SKILL_DIR/instagram-setup.md` one step at a time.
2. Use `SKILL_DIR/scripts/ig.py` (Python 3 only): `whoami`, `publish --video
   <public link> --caption-file caption.txt [--dry-run]`, `media`, `insights
   <media_id>`, `audience`, `refresh`. It reads the token from
   `IG_ACCESS_TOKEN` and never prints it.
3. Captions go through the `humanizer` skill (channel `instagram`) if installed.
4. The founder approves every post first, and the token never goes into a chat.
