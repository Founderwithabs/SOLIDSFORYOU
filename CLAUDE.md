# Everything a Founder Needs

A toolkit of Claude skills and prompts for founders. See `README.md` for the
full list.

## Layout

- `prompts/`: paste-ready prompts that work in any Claude chat.
- `.claude/skills/`: Claude Code skills (slash commands).
- `.claude/agents/`: helper agents used by economy mode.
- `taste/motion/`: taste notes learned from real videos.
- Root image files: Solids for You product page images. Do not move or rename
  them without asking; they may be linked from outside this repo.

When adding a tool, add both a skill and (where it can work outside Claude
Code) a paste-ready prompt, and list it in the README table.

## Economy mode (cheaper models for less important tasks)

- Turn it on with `/economy-mode` (or say "economy mode on"); turn it off by
  saying "economy mode off".
- It routes low-importance tasks to the `quick-task` subagent (Haiku) and
  routine tasks to the `standard-task` subagent (Sonnet), and keeps the main
  model for decisions, debugging, and final review.
- The `quick-task` and `standard-task` subagents may be used for clearly
  simple work even when economy mode is off.

Definitions: `.claude/skills/economy-mode/SKILL.md` and `.claude/agents/`.

## Careful mode (triple review before submitting)

- Turn it on with `/careful-mode` (or say "careful mode on"); turn it off by
  saying "careful mode off".
- Claude reviews every piece of work three times before submitting it:
  correctness, completeness, then an adversarial "how could this go wrong"
  pass, restarting the reviews after any fix.
- Can be combined with economy mode: cheaper models may do the work, but the
  reviews are always done by the main model.

Definitions: `.claude/skills/careful-mode/SKILL.md` (Claude Code) and
`prompts/careful-mode.md` (paste version). Keep the two in step.

## Harsh buyer review (consumer persona)

- Turn it on with `/harsh-buyer-review` (or say "review this like a harsh buyer").
- Claude acts as a real buyer: researches competitors, compares one-on-one,
  and gives harsh, specific feedback on listings, images, video and copy.
- The full prompt is in `prompts/harsh-buyer-reviewer.md`; the skill loads it.

## Motion design taste (video review, ranking and fixing)

- Turn it on with `/motion-design-taste`, and use it before delivering any
  video you made.
- Inspects the rendered video with `scripts/inspect_video.py`, scores it out
  of 100, compares and ranks it against other videos, lists exact fixes, and
  applies and re-checks them when the source is available.
- Learns the user's taste in `taste/motion/taste-notes.md`.
- The full prompt is in `prompts/motion-design-taste.md`; the skill loads it.
