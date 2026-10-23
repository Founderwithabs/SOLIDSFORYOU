# SOLIDS FOR YOU: Everything a Founder Needs

A public toolkit of Claude tools for founders. `README.md` is the founder-facing
guide; keep it accurate whenever anything here changes.

## How the repo is built

- Every tool is a Claude Code plugin in `plugins/<tool>/`, listed in
  `.claude-plugin/marketplace.json`. Founders install with
  `/plugin marketplace add Founderwithabs/SOLIDSFORYOU` and then
  `/plugin install <tool>@solidsforyou`.
- `plugins/<tool>/skills/<tool>/` is the single source of truth: `SKILL.md`,
  the full prompt (which doubles as the paste-in version), and any scripts.
  Don't copy these files elsewhere.
- `.claude/skills/<tool>/SKILL.md` are short pointers so the tools also work in
  sessions opened inside this repo. Keep their frontmatter in step with the
  plugin's SKILL.md.
- `dist/<tool>-skill.zip` are the claude.ai uploads, built by
  `python3 scripts/build_skill_zip.py`.
- `taste/motion/taste-notes.md` holds SOLIDS FOR YOU's own motion taste. It's
  used when working in this repo; it isn't shipped to other founders.

## Adding or changing a tool

1. Create `plugins/<tool>/.claude-plugin/plugin.json` with `name`,
   `displayName` ("<Tool> by SOLIDS FOR YOU"), `description` (starting
   "SOLIDS FOR YOU <Tool>:"), `author` `{"name": "SOLIDS FOR YOU"}`,
   `homepage` and `keywords`. Leave out `version`, so founders get every
   update.
2. Put the skill in `plugins/<tool>/skills/<tool>/SKILL.md`. Its frontmatter
   may only use `name` and `description`, so the claude.ai upload works.
   Refer to bundled files as being "next to this SKILL.md" and give the
   Claude Code path as `${CLAUDE_SKILL_DIR}/...`; never use repo-root paths.
   Store anything a tool learns over time in the user's project or in
   `${CLAUDE_PLUGIN_DATA}`, never inside the plugin folder (it is replaced on
   update).
3. Where the tool can work outside Claude Code, include a self-contained
   prompt in the same folder and list it in `prompts/README.md`.
4. Add an entry to `.claude-plugin/marketplace.json`, a pointer in
   `.claude/skills/<tool>/`, a row in the README's tools table, and an
   install line in its set-up section.
5. Add the tool to `SKILLS` in `scripts/build_skill_zip.py` if it works on
   claude.ai, then run the script.
6. Run `claude plugin validate .` (the only expected warnings are the missing
   versions) and test-install the plugin before pushing.

## Tool notes

- **Economy mode:** routes low-importance work to the `quick-task` (Haiku) and
  `standard-task` (Sonnet) helpers in `plugins/economy-mode/agents/`. Once
  installed as a plugin they're named `economy-mode:quick-task` and
  `economy-mode:standard-task`. Turn it on with `/economy-mode`, off with
  "economy mode off".
- **Careful mode:** three reviews (correctness, completeness, adversarial)
  before anything is submitted. Turn it on with `/careful-mode`, off with
  "careful mode off". The plugin's `SKILL.md` and `careful-mode.md` (the
  paste version) must stay in step. It can be combined with economy mode: the
  reviews are always done by the main model.
- **Audio review:** `analyze.py` measures; `designer_rubric.md` judges;
  `review.py` runs it through the Claude API.
- **Motion design taste:** `scripts/inspect_video.py` inspects; the prompt
  holds the rubric. Use it before delivering any video Claude made.
- **Harsh buyer review:** needs web search for its competitor research.
