# SOLIDSFORYOU

## Economy mode (cheaper models for less important tasks)

This repo ships an **economy mode** for Claude Code agents:

- Turn it on with `/economy-mode` (or say "economy mode on").
- It routes low-importance tasks to the `quick-task` subagent (Haiku) and
  routine tasks to the `standard-task` subagent (Sonnet), and keeps the main
  model for decisions, debugging, and final review.
- Turn it off by saying "economy mode off".

Definitions: `.claude/skills/economy-mode/SKILL.md` and `.claude/agents/`.

Even when economy mode is off, the `quick-task` and `standard-task` subagents
are available and may be used for clearly simple work.

## Careful mode (triple review before submitting)

- Turn it on with `/careful-mode` (or say "careful mode on"); turn it off by
  saying "careful mode off".
- Claude reviews every piece of work three times before submitting it:
  correctness, completeness, then an adversarial "how could this go wrong"
  pass, restarting the reviews after any fix.
- Can be combined with economy mode: cheaper models may do the work, but the
  reviews are always done by the main model.

Definition: `.claude/skills/careful-mode/SKILL.md`.

## Audio review (Claude listening as an audio designer)

- Share an audio file and ask how it sounds, or run `/audio-review`.
- The tool ships as the `audio-review` plugin in this repo's marketplace
  (`.claude-plugin/marketplace.json`). Its files live in
  `plugins/audio-review/skills/audio-review/`: `analyze.py` measures the file,
  `designer_rubric.md` is how Claude judges it, `review.py` runs it through
  the Claude API, and `initiation_prompt.md` is a paste-in prompt.
- After changing the skill, rebuild the claude.ai upload with
  `python3 scripts/build_skill_zip.py`.
