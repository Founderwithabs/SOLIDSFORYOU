---
name: audio-review
description: Judge audio like a senior audio designer (loudness, dynamics, tonal balance, stereo, noise, artifacts, delivery specs) and give a scored review with fixes. Use when the user shares audio or a video's sound (podcast, voiceover, music, mix, wav, mp3) and asks how it sounds, whether it is ready, or for an audio review.
---

# Audio review

You can't hear audio directly. Instead, measure the file the way an engineer
reads meters and analysers while listening, then judge it as an audio
designer.

All the files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`. Anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

## Steps

1. **Find the file(s).** Get the audio path from the user, plus a reference
   track if they gave one. Ask what it's for (streaming music, podcast,
   broadcast, film, game, ad, social, UI sound) only if you can't reasonably
   infer it.

2. **Analyse.** Write the output to a scratch or temp directory:

   ```bash
   python3 "SKILL_DIR/analyze.py" "<file>" --out "<out_dir>"
   ```

   If you have a reference track, run the same command on it with its own
   `--out`. This needs `ffmpeg` and `numpy`. If they're missing, install them
   (`pip install numpy`, plus ffmpeg from the system package manager). If you
   can't run code at all, skip to the no-code fallback in
   `SKILL_DIR/initiation_prompt.md`.

3. **Look and read.** Read `<out_dir>/metrics.json`. Then open each picture so
   you actually see it: `spectrogram.png`, `spectrogram_linear.png` and
   `waveform.png`. Check the analyser's `flags` against the pictures; some are
   heuristics.

4. **Judge.** Read `SKILL_DIR/designer_rubric.md` and follow it exactly: the
   same voice, reference points and report format (verdict and score, what
   I'm hearing, scorecard, ranked issues with evidence, fix list with starting
   values, what's working, limits of this review).

5. **Reply** with the review. If the user wants a file, also save it as
   `<out_dir>/review.md`.

## Other ways to run it

- `SKILL_DIR/review.py` does the same thing through the Claude API, for
  scripts and batch jobs.
- `SKILL_DIR/initiation_prompt.md` is a paste-in prompt for any Claude chat.

See `SKILL_DIR/README.md` for details.
