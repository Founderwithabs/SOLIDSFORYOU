---
name: linkedin
description: Founder's LinkedIn ghostwriter: posts that only the founder could write, hooks that work before "see more", profiles, comments, DMs and a posting plan, every draft edited through the humanizer and checked against LinkedIn's limits. Never invents a story. Use for anything on LinkedIn.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Print the rules, the founder's memory and the job table, then only the
   job's sections from the table:
   `python3 "SKILL_DIR/scripts/read_sections.py" "SKILL_DIR/linkedin.md" 1 2 3`
   (for a post: `4 5 6 7 10 14`; a draft to fix: `6 7 10 14`; a profile:
   `8 10`; comments and messages: `9 10`; a plan: `4 11`).
2. Check every draft with `python3 "SKILL_DIR/scripts/linkedin_check.py" post.txt`
   (`--headline`, `--about`, `--note`, `--comment` for the others): the fold
   preview, limits, hook, format, bait.
3. The humanizer skill is part of every job: `check --channel linkedin`
   before and after rewriting, `compare` so no fact changed, and `voice`
   against the founder's own posts. If it isn't installed, follow section 10
   by eye and tell the user once: `/plugin install humanizer@solidsforyou`.
4. Never invent a story, number, client or feeling: ask the founder.
