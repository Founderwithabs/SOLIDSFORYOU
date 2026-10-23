# SOLIDS FOR YOU: Everything a Founder Needs

Free Claude tools for starting and running a business. Each one turns Claude
into a specialist you'd otherwise have to hire: an audio designer, a motion
design director, a harsh customer, a meticulous reviewer.

Every tool works wherever you use Claude: **Claude Code**, **claude.ai** (web,
desktop, mobile), or **any Claude chat** as a paste-in prompt.

## The tools

| Tool | What you get | Use it when |
|---|---|---|
| 🎧 **Audio Review** | A senior audio designer's review of any audio: a score out of 10, how it sounds, ranked problems with timestamps, a fix list, and loudness checks for Spotify, YouTube, podcasts, broadcast and ads | Before you publish a podcast, ad, song, voice-over or product sound |
| 🎬 **Motion Design Taste** | A senior motion designer's review of a video: a score out of 100, ranking against references, and exact fixes (and Claude applies them when it has the source). It learns your taste over time | Before you ship an explainer, reel, ad or product video |
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
```

Or just run `/plugin` and pick them from the list. After that, ask naturally
("how does this audio sound?", "review this listing like a harsh buyer",
"careful mode on"). You can also run a tool by name, for example
`/careful-mode:careful-mode`.

To get updates, run `/plugin marketplace update solidsforyou`, or turn on
auto-update for the catalog under **Marketplaces** in `/plugin`.

**Requirements:** Audio Review and Motion Design Taste need
[ffmpeg](https://ffmpeg.org/download.html) and Python 3. Audio Review also
needs `numpy` (`pip install numpy`). Harsh Buyer Review needs web search,
which Claude Code has built in.

### Option 2: claude.ai, Claude Desktop or Claude Mobile

1. Download the tool's skill file from [`dist/`](dist):
   [Audio Review](dist/audio-review-skill.zip) ·
   [Motion Design Taste](dist/motion-design-taste-skill.zip) ·
   [Harsh Buyer Review](dist/harsh-buyer-review-skill.zip) ·
   [Careful Mode](dist/careful-mode-skill.zip)
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
dist/                             Skill zips for claude.ai
prompts/README.md                 Links to every paste-in prompt
taste/motion/                     SOLIDS FOR YOU's own motion taste notes
.claude/skills/                   Lets the tools work inside this repo too
scripts/build_skill_zip.py        Rebuilds the zips in dist/
```

## Add or change a tool

See [`CLAUDE.md`](CLAUDE.md): it has the checklist, and Claude Code follows
it when you ask it to add a tool.
