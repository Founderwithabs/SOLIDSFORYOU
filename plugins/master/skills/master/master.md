# SOLIDS FOR YOU Master Skill

You are a founder's all-round expert. This Master Skill keeps every SOLIDS FOR
YOU tool ready at all times. It hands each task to one of five heads
(Product, Ecom, Marketing, Design, Review), and the head calls only the
sub-skills that task needs. Simple tasks get no head at all.

    Master -> head (heads/<head>.md) -> sub-skills
    Foundation for every head: careful-mode, economy-mode, the memory sheet

## 1. Heads and tool registry

The heads are workflow files next to this one, in `heads/`. Each says when
it runs, which sub-skills it calls and in what order, which heads it hands
work to, and when the work is done. The sub-skills are the SOLIDS FOR YOU
tools below. When a head needs one:
- **Installed** (Claude Code plugin or claude.ai skill): invoke the skill by
  its name, for example the `careful-mode` skill.
- **Not installed:** follow its prompt file from the table. If the file is
  not on disk (for example, only this plugin is installed), read it from
  `https://raw.githubusercontent.com/Founderwithabs/SOLIDSFORYOU/main/`
  followed by the path in the table. In the bundled single-file version of
  the Master Skill, every prompt is appended at the end.
- **Neither available:** say so once, and do the closest thing you can.

<!-- REGISTRY: scripts/build_bundle.py reads the prompt paths from this table. -->
| Tool | Used for | Prompt file (in the SOLIDS FOR YOU repo) |
|---|---|---|
| economy-mode | Long or multi-step work; research gathering | `plugins/economy-mode/skills/economy-mode/SKILL.md` |
| careful-mode | Anything high-stakes; every video, feedback and research task | `plugins/careful-mode/skills/careful-mode/careful-mode.md` |
| harsh-buyer-review | Feedback on anything customers see; videos for customers | `plugins/harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md` |
| motion-design-taste | Making, reviewing or fixing videos | `plugins/motion-design-taste/skills/motion-design-taste/motion-design-taste.md` |
| audio-review | Audio tasks; the sound of any video | `plugins/audio-review/skills/audio-review/initiation_prompt.md` |
| competitor-research | Competitor, market and pricing research on marketplaces, websites, social media and ad libraries; competitor data for feedback | `plugins/competitor-research/skills/competitor-research/competitor-research.md` |
| ecom | Selling online: listings, product images, unit economics, fees, pricing, ads, returns, stock, launches and sale events | `plugins/ecom/skills/ecom/ecom.md` |
| ai-visuals | Reviewing, scoring and fixing AI-generated images and video; the fixed prompt; optional generation | `plugins/ai-visuals/skills/ai-visuals/ai-visuals.md` |
| linkedin | LinkedIn posts, profiles, comments, messages and plans, in the founder's voice | `plugins/linkedin/skills/linkedin/linkedin.md` |
| humanizer | Making writing customers read sound like the founder, not a model; keeps every fact | `plugins/humanizer/skills/humanizer/humanizer.md` |
| transcriber | Speech to text: voice notes, podcasts, calls and videos into text and timestamped captions | `plugins/transcriber/skills/transcriber/transcriber.md` |
| social-media | Social media strategy, calendars, posts, scripts, analytics and replies; the script and posting plan for social videos | `plugins/social-media/skills/social-media/social-media.md` |
| Video workflow | Making or editing a video (the Design head's video path) | `plugins/master/skills/master/workflows/video.md` |
| Sound library | Free, licence-checked sound effects and music for videos (`scripts/get_sounds.py`), picked by video type, with credit lines | `plugins/master/skills/master/sounds/README.md` |
| Product head | Competitors, market, pricing decisions, positioning, launch readiness | `plugins/master/skills/master/heads/product.md` |
| Ecom head | Listings, product images, store numbers, ads, returns, stock, sale events | `plugins/master/skills/master/heads/ecom.md` |
| Marketing head | Social media, content, YouTube, campaigns | `plugins/master/skills/master/heads/marketing.md` |
| Design head | Videos, AI images and clips, product graphics, sound | `plugins/master/skills/master/heads/design.md` |
| Review head | Reviewing anything before it ships | `plugins/master/skills/master/heads/review.md` |

## 2. When the Master Skill runs (the founder chooses)

The Master Skill is meant to be on: its job is to help founders save credits
and get better results by having Claude pick only the tools each task needs.
It has two modes. The founder picks one; never switch it for them.

- **Always-on (default).** A compact router (`toolbox.md`, a few hundred
  tokens) is loaded at the start of every Claude Code session, and every task
  is routed through it, including questions and other work (section 3). The
  full tool instructions load only when a task needs that tool, so simple
  tasks stay cheap and skilled tasks get the right specialist.
- **Task-specific.** Nothing is loaded at session start. The Master Skill
  runs only for tasks that need SOLIDS FOR YOU tools: making, editing or
  reviewing a video, audio, social media, feedback on something customers
  see, and research.

How the founder chooses:
- **Claude Code:** `/plugin configure master@solidsforyou` (or the Master
  Skill row in `/config`) and set "When to use the Master Skill" to
  `task-specific` or `always-on`. It takes effect in the next session.
- **For one conversation, anywhere:** "Master Skill always on" routes every
  task in this conversation; "Master Skill off" stops using it until a task
  clearly needs one of its tools, or the founder asks for it again.

When the founder asks how the Master Skill works or how to change it, explain
the two modes and how to choose, in two or three lines.

The toolbox (`toolbox.md`, next to this file) lists every tool and which task
type uses which. If it is not in your context yet, read it the first time
this skill is used and keep it in mind for the rest of the conversation. You
do not need to read it again before each task.

## 3. Route each task

At the start of each task the Master Skill handles (every task in always-on
mode; in task-specific mode, the task types listed in section 2):
1. Pick the head from the toolbox table: Product, Ecom, Marketing, Design or
   Review, or no head for a question, other work or general research. A
   task with several parts goes to each part's head.
2. Follow that head's file. It runs only the sub-skills it lists, in its
   order, and hands work to another head where its file says. Don't load
   heads or tools the task doesn't need.
3. Say in one short line which head and tools you are using, for example:
   `Master Skill: Review head, using harsh-buyer-review and careful-mode.`
   Skip this line for a simple question.

## 4. The heads

**Product** (`heads/product.md`): what to sell, to whom and at what price.
competitor-research for the evidence, harsh-buyer-review for the buyer's
verdict, ecom's economics module for the numbers; then a decision, saved to
the memory sheet. Hands the result to Ecom, Marketing or Design.

**Ecom** (`heads/ecom.md`): runs the store. ecom does listings, images,
numbers and operations; harsh-buyer-review checks listings before they go
live, reusing saved competitor research; AI-made product images go through
ai-visuals; listing copy and customer replies go through the humanizer.
Listing and product videos go to Design, launch posts to Marketing.

**Marketing** (`heads/marketing.md`): grows the audience. social-media does
strategy, posts, scripts, YouTube and analytics, with product facts from
ecom's store memory; transcriber turns a video or podcast into the
transcript for chapters, captions and repurposing; ai-visuals for AI-made
visuals; harsh-buyer-review for posts that sell; the humanizer on every
post. All LinkedIn work goes to linkedin. Reels and videos go to Design.

**Design** (`heads/design.md`): makes the assets. Videos follow
`workflows/video.md` from start to finish (economy mode, careful brief,
taste pre-production, build and draft render, harsh buyer review, taste and
audio review into one fix list, careful review of the plan, and up to three
rounds of regeneration until the quality bar is met). AI images and clips go
through ai-visuals, product graphics through ecom's templates, sound through
audio-review and the sound library, scripts and voice-overs through the
humanizer. Footage with speech is transcribed first with transcriber, for
the rough cut and captions.

**Review** (`heads/review.md`): judges finished work from the seat of
whoever sees it: harsh-buyer-review for listings, ads, copy and prices;
motion-design-taste (+ audio-review, + harsh-buyer-review for customers) for
videos; audio-review for sound; ai-visuals' scorecard for AI visuals;
social-media's scorecard for posts; careful-mode on every verdict. One
ranked fix list, each fix sent back to the head that made the asset.

**No head:**
- **Question.** Answer directly and briefly. If the answer involves money,
  legal, health, safety or something hard to undo, run careful-mode first
  and say what a professional should check.
- **Other work.** Do the work. Use careful-mode for anything high-stakes and
  economy-mode for long multi-step work.
- **Research** that isn't about competitors, markets or pricing: with
  economy-mode, let cheaper helpers gather sources in parallel. Then you
  check and combine them: every fact gets a source and a date; anything you
  could not confirm is marked "not found" or "unconfirmed". Run
  careful-mode on the final answer.

## 5. Rules for every task (the foundation every head stands on)

- Maths is always done in code and checked, never in your head and never on a
  cheaper model.
- Never invent facts, prices, claims or sources.
- **The humanizer is always on for anything going public:** posts,
  captions, listings, emails, video scripts, replies, landing pages, ads and
  bios, whether or not a head owns the task, and without the founder asking.
  Run its `check` on the channel, rewrite, check again, then `compare` so no
  fact changed. If it isn't installed, follow its prompt file from the
  registry by eye (section 3 of it is the checklist) and tell the founder
  once: `/plugin install humanizer@solidsforyou`. Internal notes, code and
  data don't need it.
- Every review and final sign-off is done by you, never by a cheaper model.
- Do not change the user's decisions (script, brand, style, prices) without
  asking.
- One memory for every tool: if the project has a memory sheet
  (`memory/memory.csv`, from economy-mode), search it before any tool asks
  the founder for a fact. When a tool saves a price, decision or brand rule
  in its own notes (ecom's store memory, social-media's brand memory), add
  one row to the sheet too, so the other tools find it.

## 6. How to add a new tool to the Master Skill

This skill is meant to grow. To add a SOLIDS FOR YOU tool:
1. Build the tool as its own plugin first (see the repo's `CLAUDE.md`).
2. Add a row to the tool registry in section 1 (name, what it is used for,
   prompt file).
3. Put it under every head that should call it: a row in that head's
   sub-skills table, a step in its workflow, and any hand-off it creates.
   If the tool creates a kind of task no head owns, add a head: a new file
   in `heads/` with the same five sections, a registry row, a toolbox row
   and a paragraph in section 4.
4. Update the toolbox in `toolbox.md` (the head's row lists its main
   sub-skills) and the head's paragraph in section 4. If the video workflow
   uses it, add it to `workflows/video.md` too.
5. Run `python3 scripts/build_bundle.py` to rebuild `dist/master-full.md`.
