# Audio review: Claude listening as an audio designer

Claude can't take audio as input. This tool gives Claude what an audio designer
actually works from while listening: meters, analysers and a spectrogram. Claude
then judges the file against a senior-designer rubric.

```
audio file ──► analyze.py ──► metrics.json + spectrogram.png + waveform.png
                                   │
                                   ▼
                designer_rubric.md + Claude ──► review.md
                (scored verdict, ranked issues, fix list)
```

## What gets measured

| Area | Measurements |
|---|---|
| Loudness | Integrated LUFS, loudness range, true peak (EBU R128 via ffmpeg), a short-term loudness timeline, and pass/fail against Spotify, Apple Music, YouTube, podcast, EBU R128, ATSC A/85, game and social targets |
| Dynamics | Crest factor, macro-dynamics, section-by-section level |
| Tonal balance | Energy in sub, bass, low-mid, mid, high-mid, presence, brilliance and air bands; spectral tilt; centroid |
| Problems | Clipping, DC offset, clicks/pops, 50/60 Hz hum, narrow resonances, sibilance, noise floor and SNR, lossy-codec bandwidth cutoff, leading/trailing silence |
| Stereo | L/R correlation, width, mono-fold loss, low-end width, L/R balance |
| Pictures | Log and linear spectrograms and a per-channel waveform, which Claude reads |

## Two ways to use it

**1. Inside Claude Code (no API key needed).** Install the plugin (see the
repository README), then share a file and ask "how does this sound?". The
skill in `SKILL.md` runs the analyzer, looks at the images and writes the
review.

**2. From the command line, through the Claude API**, for scripts and batch
jobs:

```bash
pip install -r plugins/audio-review/skills/audio-review/requirements.txt   # also needs ffmpeg
export ANTHROPIC_API_KEY=...

python plugins/audio-review/skills/audio-review/review.py mix.wav
python plugins/audio-review/skills/audio-review/review.py mix.wav --context "podcast episode for Spotify"
python plugins/audio-review/skills/audio-review/review.py mix.wav --reference pro_master.wav   # A/B against a reference
python plugins/audio-review/skills/audio-review/review.py mix.wav --dry-run                    # analyse only, no API call
```

The output goes to `audio_reviews/<name>/` (metrics.json, the images and
review.md). You can also run the analyzer alone with
`python plugins/audio-review/skills/audio-review/analyze.py mix.wav --out some_dir`.

## Use it in any Claude chat

`initiation_prompt.md` is a self-contained prompt. Paste it into any Claude conversation (claude.ai, the desktop or mobile apps, or a Project's instructions) and Claude will act as an audio designer for the rest of the chat. Where Claude can run code, it analyses uploaded audio itself.

## Limits

The review judges the measurable sound: level, balance, noise, width,
artifacts and delivery specs. It can't judge performance, emotion, lyrics or
taste the way a human ear does. The rubric tells Claude to say so and to
treat deliberate creative choices (lo-fi, heavy limiting) as choices, not
defects. Click and resonance detection are heuristics, so Claude checks them
against the spectrogram before reporting them.
