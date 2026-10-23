---
name: economy-mode
description: Economy mode: send low-importance work to cheaper models (Haiku, Sonnet) through helpers and keep the main model for judgment. Use for "economy mode", "save tokens", "use cheaper models", or when the user wants to cut cost.
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
  or paths, and what to return. It does not see this conversation.
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

## Reporting

At the end of your reply, add one short line listing what was delegated, for
example: `Economy mode: 3 tasks on Haiku, 1 on Sonnet, 1 handled directly.`

## Turning it off

When the user says "economy mode off" (or similar), stop delegating by tier
and go back to normal behavior.
