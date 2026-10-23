# SOLIDS FOR YOU: Everything a Founder Needs

**Make your Claude solid.**

Free, open-source Claude tools for starting and running a business (MIT
licensed, see [License](#license)). Each one turns Claude
into a specialist you'd otherwise have to hire: an audio designer, a motion
design director, a harsh customer, a meticulous reviewer.

Every tool works wherever you use Claude: **Claude Code**, **claude.ai** (web,
desktop, mobile), or **any Claude chat** as a paste-in prompt.

## The tools

| Tool | What you get | Use it when |
|---|---|---|
| 🎧 **Audio Review** | A senior audio designer's review of any audio: a score out of 10, how it sounds, ranked problems with timestamps, a fix list, and loudness checks for Spotify, YouTube, podcasts, broadcast and ads | Before you publish a podcast, ad, song, voice-over or product sound |
| 🏆 **Master Skill** | Keeps every tool below ready and uses only what each task needs. Making a video runs the full video workflow: it plans, builds, reviews as your buyer and as a motion designer, checks the sound, then fixes and re-renders until the video scores 85 out of 100 or more. Social media, feedback and research get their specialists, and simple tasks get none, so you save credits and get better work | Always on. Install it with the other tools and Claude picks the right ones for each task |
| 📱 **Social Media** | Your head of social media: strategy, content calendars, posts, hooks, carousels and reel scripts for Instagram, TikTok, YouTube, LinkedIn, X and more. Every post passes a 100-point scorecard before you see it, growth stays honest, and it learns from your own results | Planning, writing, reviewing or analysing anything for social media |
| 🎬 **Motion Design Taste** | A senior motion designer's review of a video: a score out of 100, ranking against references, and exact fixes (and Claude applies them when it has the source). It learns your taste over time | Before you ship an explainer, reel, ad or product video |
| 🔎 **Competitor Research** | Deep competitor analysis on Amazon, Flipkart, Meesho, Myntra and any other marketplace, plus competitor websites, social media and ads. Every fact is sourced and dated, a separate pass double-checks it, and you get price, review and listing comparisons with ranked actions. Runs on Claude's cheapest model (Haiku) to save credits | Before you price, launch, change a listing, or ask for harsh buyer feedback |
| 🛒 **Harsh Buyer Review** | A real buyer tears into your listing: researches 3 to 5 competitors, compares one-on-one, and tells you exactly why they would or wouldn't buy | Before you launch or change a product listing, images, video, copy or price |
| ✅ **Careful Mode** | Claude checks every piece of work three times (is it right, is it complete, how could it go wrong) before handing it over | Anything high-stakes: prices, contracts, customer emails, launches |
| 💰 **Economy Mode** | Claude sends simple tasks to cheaper models and keeps the strongest one for decisions, to cut cost | Long Claude Code sessions where cost adds up (Claude Code only) |

## Set it up

### Option 1: Claude Code (recommended; every tool works fully)

In a Claude Code session, add the SOLIDS FOR YOU catalog once:

```
/plugin marketplace add Founderwithabs/SOLIDSFORYOU
```

Then install the tools you want:

```
/plugin install audio-review@solidsforyou
/plugin install motion-design-taste@solidsforyou
/plugin install harsh-buyer-review@solidsforyou
/plugin install careful-mode@solidsforyou
/plugin install economy-mode@solidsforyou
/plugin install master@solidsforyou
/plugin install social-media@solidsforyou
/plugin install competitor-research@solidsforyou
```

Or just run `/plugin` and pick them from the list. After that, ask naturally
("how does this audio sound?", "review this listing like a harsh buyer",
"careful mode on"). You can also run a tool by name, for example
`/careful-mode:careful-mode`.

To get updates, run `/plugin marketplace update solidsforyou`, or turn on
auto-update for the catalog under **Marketplaces** in `/plugin`.

**Master is on in every session (recommended).** It loads a compact router
of a few hundred tokens, so Claude uses only the tools each task needs: a
quick question gets a quick answer with no tools, while a video, a listing or
a social post gets the right specialist. The full instructions for a tool
load only when a task needs it. If you'd rather Master only stepped in for
video, audio, social media, feedback and research, switch it to
**task-specific** with `/plugin configure master@solidsforyou` (or its row in
`/config`). For a single conversation, say "Master Skill off" or "Master Skill
always on".

**Requirements:** Audio Review and Motion Design Taste need
[ffmpeg](https://ffmpeg.org/download.html) and Python 3. Audio Review also
needs `numpy` (`pip install numpy`). The Master Skill needs
[Node.js](https://nodejs.org) with Playwright and Chromium to render videos
(`npm install -g playwright` then `npx playwright install chromium`), and
works best with all the other tools installed. Competitor Research needs web
search and works best with Node.js and Playwright for reading marketplace
pages. Harsh Buyer Review needs web search, which Claude Code has built in.

### Option 2: claude.ai, Claude Desktop or Claude Mobile

1. Download the tool's skill file from [`dist/`](dist):
   [Audio Review](dist/audio-review-skill.zip) ·
   [Motion Design Taste](dist/motion-design-taste-skill.zip) ·
   [Harsh Buyer Review](dist/harsh-buyer-review-skill.zip) ·
   [Careful Mode](dist/careful-mode-skill.zip) ·
   [Social Media](dist/social-media-skill.zip) ·
   [Competitor Research](dist/competitor-research-skill.zip) ·
   [Master Skill](dist/master-skill.zip) (upload the others too: it uses
   them)
2. In Claude's settings, turn on code execution, then upload the zip as a
   custom skill.
3. Start a chat and ask for the tool, for example by uploading a video and
   asking Claude to review it.

### Option 3: Any Claude chat (no setup)

Open the tool's prompt, copy all of it, and paste it as your first message,
or into a Claude Project's instructions so every chat in that project has it.
All prompts are listed in [`prompts/`](prompts/README.md).

## What happens to your files

- **Claude Code:** the audio and video tools measure your files on your own
  computer with ffmpeg. Claude then sees the measurements and still images,
  not the raw file.
- **claude.ai and chats:** files you upload are handled by Claude under your
  plan's normal terms.
- Nothing is sent to SOLIDS FOR YOU.

## Repository layout

```
.claude-plugin/marketplace.json   The catalog Claude Code reads
plugins/<tool>/                   One installable plugin per tool
  skills/<tool>/SKILL.md          What Claude follows
  skills/<tool>/*.md              The full prompt (also the paste-in version)
dist/                             Skill zips for claude.ai, and
                                  master-full.md (the Master Skill with
                                  every tool, in one paste-in file)
prompts/README.md                 Links to every paste-in prompt
taste/motion/                     SOLIDS FOR YOU's own motion taste notes
.claude/skills/                   Lets the tools work inside this repo too
scripts/build_skill_zip.py        Rebuilds the zips in dist/
scripts/build_bundle.py           Rebuilds dist/master-full.md
tests/run_tests.py                Tests every tool (runs on each push)
```

## License

Copyright (c) 2026 Solids for You Private Limited. Released under the
[MIT License](LICENSE.md).

- **Free for everyone, including businesses.** Use the tools for your own
  company or your clients, change them, and build on them.
- If you share the tools, or copies of substantial parts of them, keep the
  copyright notice and the license text from [`LICENSE.md`](LICENSE.md)
  with them. Every plugin folder and skill zip already includes it.
- The tools come with no warranty: check what Claude produces before you
  rely on it.

## Add or change a tool

See [`CLAUDE.md`](CLAUDE.md): it has the checklist, and Claude Code follows
it when you ask it to add a tool.
