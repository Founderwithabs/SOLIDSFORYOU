---
name: social-media
description: SOLIDS FOR YOU Social Media: a head of social media for founders. Use for any social media task: strategy, which platforms, content pillars, content calendars, writing posts, captions, carousels, threads, hooks, titles, thumbnails and reel, short or TikTok scripts, repurposing one piece across platforms, reviewing a post or account before publishing, finding trends, analysing post performance or analytics exports, and replying to comments. Covers Instagram, TikTok, YouTube, LinkedIn, X, Facebook, Pinterest, WhatsApp, Reddit and Threads. Also use when the user says "make this go viral", "social media post", "grow our account" or "/social-media".
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Read `SKILL_DIR/social-media.md` and follow it exactly. It holds the
   ground rules, brand memory, the job table, strategy, calendars, content
   creation, the pre-publish scorecard, repurposing, analytics, trends,
   community, the platform playbook and the compliance check.
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

   It needs only Python 3.
4. Other SOLIDS FOR YOU tools make this stronger when installed:
   `harsh-buyer-review` for posts and ads that sell, the `master` skill's
   video workflow to produce reels and shorts, `motion-design-taste` to
   review videos, and `careful-mode` for anything high-stakes. Use them where
   the prompt says to; if they are missing, follow the prompt's built-in
   checks.
