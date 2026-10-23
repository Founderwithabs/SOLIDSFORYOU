# Everything a Founder Needs

A growing toolkit of Claude skills and prompts for starting and running a
business. Every tool works two ways:

- **In Claude Code** on this repo: type the slash command, e.g. `/careful-mode`.
- **In any Claude chat**: copy the matching file from `prompts/` and paste it
  as your first message.

## Tools

| Tool | What it does | Claude Code | Paste anywhere |
|---|---|---|---|
| Careful mode | Reviews every piece of work three times (correctness, completeness, "how could this go wrong") before submitting | `/careful-mode` | [`prompts/careful-mode.md`](prompts/careful-mode.md) |
| Harsh buyer review | Acts as a real buyer: researches competitors, compares one-on-one, and gives harsh, specific feedback on listings, images, video and copy | `/harsh-buyer-review` | [`prompts/harsh-buyer-reviewer.md`](prompts/harsh-buyer-reviewer.md) |
| Economy mode | Sends low-importance work to cheaper models (Haiku, Sonnet) and keeps the strongest model for decisions and review | `/economy-mode` | Claude Code only (needs subagents) |

## Repository layout

```
prompts/              Paste-ready prompts for any Claude chat
.claude/skills/       Claude Code skills (slash commands)
.claude/agents/       Claude Code helper agents used by economy mode
CLAUDE.md             Instructions Claude Code reads automatically
*.webp, *.png         Solids for You product page images (Solid Joggers)
```
