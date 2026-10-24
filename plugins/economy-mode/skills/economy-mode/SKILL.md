---
name: economy-mode
description: Economy mode: send low-importance work to cheaper models (Haiku, Sonnet) through helpers, keep the main model for judgment, and keep a memory sheet so Claude remembers decisions across sessions without carrying them. Use for "economy mode", "save tokens", "use cheaper models", "remember this", or cutting cost.
---

# Economy mode

Economy mode is now ON for the rest of this session (until the user says to
turn it off). Your job becomes: plan, decide, and review. Hand off work that
does not need your level of reasoning to a cheaper model.

## Step 1: classify every task before doing it

| Tier | Send to | Typical tasks |
|------|---------|---------------|
| **Low** | `quick-task` helper (Haiku) | Find/list/rename files, grep for text, check if something exists, summarize one file or log, reformat text or data, short boilerplate, trivial one-line edits |
| **Medium** | `standard-task` helper (Sonnet) | Product copy and descriptions, clearly specified changes across a few files, writing tests, routine refactors, summarizing several sources |
| **High** | Do it yourself (current model) | Architecture and design decisions, ambiguous requirements, hard debugging, security, payments, anything irreversible or customer-facing that needs judgment, final review |

If you are unsure between two tiers, pick the higher one. Saving a little cost
is never worth a wrong result on something that matters.

## Step 2: delegate

- Call the Agent tool with the helper's name. Installed as a plugin they are
  `economy-mode:quick-task` and `economy-mode:standard-task`; in a project
  that defines them itself they are `quick-task` and `standard-task`. Use
  whichever your agent list shows. If neither exists, use the general-purpose
  agent with the Agent tool's `model` set to `"haiku"` or `"sonnet"`, and put
  the helper's rules in the prompt: do only what was asked, report briefly,
  and reply `ESCALATE:` plus a reason instead of guessing.
- Give the subagent a complete, self-contained prompt: the goal, the exact files
  or paths, and what to return. It does not see this conversation. If the
  project has a memory sheet, start the prompt with
  `Run python3 "<memory.py>" --file "<sheet>" brief --task "<key words>" first.`
  (full paths, as the session-start line gives them) instead of explaining
  the project again; see "Helper section" below.
- Batch several small low-tier jobs into one subagent call when they are related,
  so you do not pay the start-up cost repeatedly.
- Do not delegate tasks that take you a single tool call (one `ls`, one small
  read). Spawning a subagent costs more than that.
- For a one-off that does not fit either agent, you may use the general-purpose
  agent with the Agent tool's `model` parameter set to `"haiku"` or `"sonnet"`.

## Step 3: check and escalate

- Skim every subagent result before using it.
- If a subagent replies with `ESCALATE:`, or its result looks wrong, move the
  task up one tier (quick-task -> standard-task -> yourself). Do not retry the
  same tier with the same prompt.

## Memory sheet: remember without carrying

Economy mode keeps a memory sheet outside the conversation, so nothing the
founder told you is lost after `/clear`, `/compact` or a new session, and the
conversation never has to carry the whole history. It is
`memory/memory.csv` in the project; Excel and Google Sheets open it
directly. The script is next to this SKILL.md (in Claude Code:
`${CLAUDE_SKILL_DIR}/scripts/memory.py`; below, `SKILL_DIR/scripts/memory.py`).

- **Look up, don't reload.** Before asking the founder something they may
  have told you (prices, decisions, suppliers, preferences, deadlines), run
  `python3 "SKILL_DIR/scripts/memory.py" search "a few key words"`. It
  returns the best 5 rows. Never print or read the whole sheet.
- **Write as you go.** When the founder states a fact, makes a decision,
  sets a preference or gives you a task to remember, add one row:
  `python3 "SKILL_DIR/scripts/memory.py" add --type decision --topic pricing --text "..." --source "founder, <date>"`.
  Types: fact, decision, preference, task, contact, number, note. One memory
  per row, in plain words, with the real numbers. Pin (`--pin`) only rules
  that apply to almost every task, such as brand voice; pinned rows are
  shown at the start of every session.
- **Keep it true.** When something changes, `update <id> --text "..."`;
  when it no longer applies, `forget <id>` (the row stays in the sheet,
  hidden from searches). Never store passwords, card numbers or other
  secrets.
- **Helper section.** Rows added with `--helpers` (or marked later with
  `update <id> --helpers`) are the standing brief every helper reads: what
  the business is and sells, where things live in the project, conventions,
  brand voice, current prices. Pinned rows are included too. `brief --task
  "key words"` prints that section plus the rows matching the task, capped
  at about 1,000 tokens, so helpers always work from the latest facts and
  you never re-explain the project. Keep the section to what almost every
  helper needs; everything else they get through the task match. Helpers
  only read the sheet: when a helper's report ends with
  `REMEMBER: <type>/<topic>: <text>` lines, check them and add the true
  ones yourself.
- **Before `/compact` or a long break,** add any decision from this session
  that isn't in the sheet yet.
- Saving and searching are quick tool calls; do them yourself rather than
  through a helper.

## Reporting

At the end of your reply, add one short line listing what was delegated, for
example: `Economy mode: 3 tasks on Haiku, 1 on Sonnet, 1 handled directly.`

## Turning it off

When the user says "economy mode off" (or similar), stop delegating by tier
and go back to normal behavior.
