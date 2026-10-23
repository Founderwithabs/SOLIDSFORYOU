---
name: audio-review
description: Listen to an audio file and judge its quality the way a senior audio designer would (loudness, dynamics, tonal balance, stereo, noise, artifacts, delivery specs), then give a scored review with concrete fixes. Use when the user shares an audio or video file (wav, mp3, m4a, flac, ogg, aif, mp4, mov) and asks how it sounds, whether it is good or ready, to check the mix or master, to judge quality, or says "/audio-review".
---

# Audio review

You can't hear audio directly. Instead, measure the file the way an engineer
reads meters and analysers while listening, then judge it as an audio
designer.

## Steps

1. **Find the file(s).** Get the audio path from the user, plus a reference
   track if they gave one. Ask what it's for (streaming music, podcast,
   broadcast, film, game, ad, social, UI sound) only if you can't reasonably
   infer it.

2. **Analyse.** Write the output to the scratchpad, or to `audio_reviews/`
   if there is no scratchpad:

   ```bash
   python tools/audio_review/analyze.py "<file>" --out "<out_dir>"
   ```

   If you have a reference track, run the same command on it with its own
   `--out`. This needs `ffmpeg` and `numpy`; install them if they're missing
   (`pip install -r tools/audio_review/requirements.txt`).

3. **Look and read.** Read `<out_dir>/metrics.json`. Then Read each picture so
   you actually see it: `spectrogram.png`, `spectrogram_linear.png` and
   `waveform.png`. Check the analyser's `flags` against the pictures; some are
   heuristics.

4. **Judge.** Read `tools/audio_review/designer_rubric.md` and follow it
   exactly: the same voice, reference points and report format (verdict and
   score, what I'm hearing, scorecard, ranked issues with evidence, fix list
   with starting values, what's working, limits of this review).

5. **Reply** with the review in chat. If the user wants a file, also save it
   as `<out_dir>/review.md`.

## Without Claude Code

`tools/audio_review/review.py` does the same thing through the Claude API.
That's useful for batch jobs or scripts. See `tools/audio_review/README.md`.
