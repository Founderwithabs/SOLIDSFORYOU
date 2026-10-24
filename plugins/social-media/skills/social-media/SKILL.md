---
name: social-media
description: Head of social media for founders: strategy, content calendars, posts, captions, carousels, hooks, reel and short scripts, repurposing, pre-publish review, trends, analytics and comment replies on Instagram, TikTok, YouTube, LinkedIn, X and more. Use for any social media task, "make this go viral" or "grow our account".
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Follow `SKILL_DIR/social-media.md` exactly. It is long, so with a
   terminal print only what the job needs, in ONE command that always starts
   with sections 1, 2 and 3 (ground rules, brand memory, the job table; never
   skip them, they hold the rules every job must follow):
   `python3 "SKILL_DIR/scripts/read_sections.py" "SKILL_DIR/social-media.md" 1 2 3 <job sections> 14`
   Job sections, from the table in section 3: strategy 4, calendar 5,
   create 6 7, repurpose 8, review 7, analyse 9, trends 10, engage 11. Add 12
   when a platform's specs matter and 13 before anything is published.
   Example for a comment reply: `... social-media.md 1 2 3 11 13 14`.
   Without a terminal, read the whole file.
2. Load the founder's brand memory first (section 2 of that file): a
   `social/` folder in the current project, then
   `${CLAUDE_PLUGIN_DATA}/`, then anything pasted into the chat. Save new
   or updated memory to the project's `social/` folder if the founder works
   in a project, otherwise to `${CLAUDE_PLUGIN_DATA}/`. Never save inside the
   plugin folder.
3. Analyse results with the bundled script instead of doing maths by hand:

   ```
   python3 "SKILL_DIR/scripts/content_log.py" template > social/posts.csv
   python3 "SKILL_DIR/scripts/content_log.py" analyze social/posts.csv \
     --by pillar,format,hook_type --out social/report.md
   ```

   It needs only Python 3. `read_sections.py` (same folder, `--list` shows
   the sections) prints parts of the prompt.
4. Other SOLIDS FOR YOU tools make this stronger when installed:
   `harsh-buyer-review` for posts and ads that sell, the `master` skill's
   video workflow to produce reels and shorts, `motion-design-taste` to
   review videos, and `careful-mode` for anything high-stakes. Use them where
   the prompt says to; if they are missing, follow the prompt's built-in
   checks.
