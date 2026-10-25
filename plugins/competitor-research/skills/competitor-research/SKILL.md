---
name: competitor-research
description: Evidence-based competitor research on marketplaces (Amazon, Flipkart, Meesho and more), competitor websites, social media and ad libraries: every fact sourced, verified and computed by script, run by cheap Haiku helpers. Use for competitors, market or pricing research, benchmarking, or competitor data before feedback. Analysis only, no copy.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. If the files came as text with no folder (for example from a
skill marketplace), save the ones a task needs to a temporary folder, never
the founder's project, and use that. Below, `SKILL_DIR` means that folder. When you pass it to a
helper, pass the full absolute path.

The method is in `SKILL_DIR/competitor-research.md`. This skill is analysis
only: never write copy, listings or ads here.

## With helpers (Claude Code, plugin installed): you only coordinate

Keep the main conversation cheap. Don't fetch pages or read raw data
yourself; the helpers do that on Haiku and send back short summaries.

1. Print only what you need from the method:
   `python3 "SKILL_DIR/scripts/read_sections.py" "SKILL_DIR/competitor-research.md" 1 2 3 step1 11`. Write
   `brief.md` (step 1) in `research/<short-name>-<YYYY-MM-DD>/` in the
   user's project, asking the user only for what you can't find (search the
   project's memory sheet first, if it has one). Then run
   `python3 "SKILL_DIR/scripts/ledger.py" init <folder>`.
2. Start the `research-scout` helper (installed as
   `competitor-research:research-scout`) with SKILL_DIR, the folder and the
   depth level. Show the user its competitor list and let them change it if
   they want before you go on. If the project has a memory sheet, give the
   scout and the analyst its `brief --task "<product>"` command too.
3. Start one `research-collector` helper per competitor, including `us`,
   up to five at a time in parallel. Give each: SKILL_DIR, the folder, its
   competitor id, its id prefix (`<id>-`), and the depth level.
4. Run `python3 "SKILL_DIR/scripts/ledger.py" merge <folder>`, then start the
   `research-verifier` helper. Re-run the collector for any competitor it
   reports above 1 in 10 mismatches, then verify again.
5. Start the `research-analyst` helper. Send the user its reply (section
   12 of the method) and the folder path. If the user asked for feedback,
   hand `report.md` and `tables.md` to the `harsh-buyer-review` skill.

If a helper isn't available under either name, do its steps yourself, one
competitor at a time.

## Without helpers (claude.ai or any chat)

Follow `SKILL_DIR/competitor-research.md` from step 1 to step 10 yourself,
in order, one competitor at a time. Choosing Haiku as the model keeps it
cheap; the method is built for it.

## Tools

- `SKILL_DIR/scripts/fetch_page.cjs`: opens a page in a real browser and
  saves text, structured data, hints and a screenshot (needs Node.js and
  Playwright with Chromium).
- `SKILL_DIR/scripts/ledger.py`: init, check, merge, sample and tables
  (needs only Python 3).
- `SKILL_DIR/scripts/read_sections.py`: prints only the sections of the
  method a step needs, so nobody reads the whole file (`--list` shows them).
