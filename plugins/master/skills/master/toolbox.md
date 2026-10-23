# SOLIDS FOR YOU toolbox (always loaded)

You have the SOLIDS FOR YOU Master Skill. It keeps these tools ready for
every task, so you never have to go looking for them. Before starting any
task, pick the task type below and use only the tools it lists. Do not load
tools a task doesn't need.

## The tools

| Tool | What it does |
|---|---|
| `economy-mode` | Sends simple, low-judgment work (finding, fetching, running commands, reformatting) to cheaper models; keeps decisions and reviews on the main model |
| `careful-mode` | Three reviews before anything is handed over: is it right, is it complete, how could it go wrong |
| `harsh-buyer-review` | A real buyer researches competitors, compares one-on-one, and gives harsh, specific feedback |
| `motion-design-taste` | Inspects a video, scores it out of 100, ranks it against references, lists and applies exact fixes |
| `audio-review` | Measures and judges audio like a senior audio designer, with a score and a fix list |
| Video build tools | Scene template, frame-by-frame renderer and sound-effects mixer, in the `master` skill's folder |

## Pick the task type, then use only its tools

| Task type | Looks like | Use | Don't use |
|---|---|---|---|
| **Video** | Make or edit any video: reel, ad, explainer, animation, motion graphic, product video, footage edit, animated GIF | The full video workflow (`workflows/video.md` in the `master` skill): economy-mode, careful-mode, motion-design-taste, video build tools, audio-review for the sound, harsh-buyer-review | Nothing is skipped |
| **Video review** | "Is this video good?", compare or rank videos, without making one | motion-design-taste, harsh-buyer-review if it's for customers, audio-review if the sound matters, careful-mode | Video build tools (unless asked to fix it) |
| **Audio** | Review, check or fix audio, voiceover, podcast, music, mix | audio-review, careful-mode | Video and design tools |
| **Feedback** | Feedback on a product, listing, image, copy, packaging, price or offer | harsh-buyer-review, careful-mode | Video and audio tools |
| **Research** | Markets, competitors, suppliers, prices, facts, trends | economy-mode (helpers gather sources), careful-mode (check every fact and cite it); harsh-buyer-review's competitor method for product comparisons | Video and audio tools |
| **Question** | A direct question or quick answer | Answer directly; careful-mode if money, legal, health or anything hard to undo is involved | Every other tool |
| **Other work** | Writing, planning, code, documents | careful-mode for anything high-stakes, economy-mode for long multi-step work | Video and audio tools |

If a task mixes types, use the tools of each type it contains. If you are
unsure of the type, pick the one with more checks.

## Rules for every task

- Maths is always done in code and checked, never in your head and never on
  a cheaper model.
- Never invent facts, prices, claims or sources. Say "not found" instead.
- Every review and final sign-off is done by you, never by a cheaper model.
- Full instructions for any tool: use that tool's skill. Full rules for the
  Master Skill: `master.md` in the `master` skill's folder.
