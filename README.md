# SOLIDSFORYOU: Claude tools for founders

Free tools that make Claude better at real founder work. Use them in Claude
Code, on claude.ai, or in any Claude chat.

## SOLIDS FOR YOU Audio Review: Claude listens like a senior audio designer

Give Claude a podcast, ad, song, voice-over or product sound. You get back
what a senior audio designer would tell you:

- a score out of 10 and whether it's ready to ship
- how it actually sounds (muddy, harsh, squashed, noisy, wide, punchy…)
- ranked problems, with the exact time or frequency of each
- a fix list an engineer can apply straight away
- a loudness check against Spotify, Apple Music, YouTube, podcast, broadcast,
  game and social specs

Claude can't hear audio directly, so the tool measures it the way an engineer
reads meters: loudness, dynamics, frequency balance, stereo, noise, clicks,
hum and clipping. It also draws a spectrogram and waveform for Claude to look
at.

### Connect it to your Claude

Pick the option that matches where you use Claude.

**1. Claude Code (recommended: it runs the full analysis)**

Inside a Claude Code session:

```
/plugin install audio-review --marketplace Founderwithabs/SOLIDSFORYOU
```

On older Claude Code versions, run these two commands instead:

```
/plugin marketplace add Founderwithabs/SOLIDSFORYOU
/plugin install audio-review@solidsforyou
```

Then share an audio file and ask *"How does this sound?"*, or run
`/audio-review:audio-review`. You need `ffmpeg` and Python with `numpy`
installed.

**2. claude.ai, Claude Desktop or Claude Mobile (as a custom skill)**

1. Download [`dist/audio-review-skill.zip`](dist/audio-review-skill.zip).
2. In Claude, open **Settings → Capabilities**, turn on code execution, and
   upload the zip under **Skills**.
3. In any chat, upload an audio file and ask Claude to review it.

**3. Any Claude chat (paste-in prompt, no setup)**

Copy everything in
[`initiation_prompt.md`](plugins/audio-review/skills/audio-review/initiation_prompt.md)
into a new chat, or into a Claude Project's instructions, then upload your
audio. If that Claude can browse the web, you can also just tell it:

> Read https://raw.githubusercontent.com/Founderwithabs/SOLIDSFORYOU/main/plugins/audio-review/skills/audio-review/initiation_prompt.md and follow it for this conversation.

**4. Your own code (Claude API)**

```bash
git clone https://github.com/Founderwithabs/SOLIDSFORYOU
cd SOLIDSFORYOU/plugins/audio-review/skills/audio-review
pip install -r requirements.txt     # also needs ffmpeg
export ANTHROPIC_API_KEY=...
python review.py your_mix.wav --context "podcast episode for Spotify"
```

Add `--reference pro_track.wav` to compare against a track you love.

### What it can't do

It judges the measurable sound: level, balance, noise, width, artifacts and
delivery specs. It can't judge performance, emotion or taste, so it tells you
what to double-check by ear.

## Also in this repo (for Claude Code)

- **Economy mode** (`/economy-mode`) routes simple tasks to cheaper models.
- **Careful mode** (`/careful-mode`) makes Claude review its work three times
  before it hands it over.

## For Claude, if you're reading this repository

To review audio, follow
`plugins/audio-review/skills/audio-review/SKILL.md`. If you can't run code,
follow `plugins/audio-review/skills/audio-review/initiation_prompt.md`.
