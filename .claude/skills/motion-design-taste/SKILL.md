---
name: motion-design-taste
description: Judge motion graphics videos with a senior motion designer's taste. Inspects a rendered video (contact sheets, frame-by-frame strips, cuts, loudness), scores it on a 100-point rubric, compares and ranks it against any other videos, lists exact fixes, and when the source is available applies the fixes, re-renders and re-scores. Use for any video review, "is this video good", "compare these videos", "rank these", "fix the animation", "/motion-design-taste", and before delivering any video Claude made.
---

1. Read `prompts/motion-design-taste.md` at the repository root and follow it
   exactly. It holds the taste rules, the rubric, the comparison method, the
   fix loop and the output format.
2. Read `taste/motion/taste-notes.md` before every review. It records this
   user's taste learned from real videos and overrides the general rules when
   they conflict.
3. Inspect every video, including each reference, with the bundled script
   instead of typing the ffmpeg commands by hand:

   ```
   python3 .claude/skills/motion-design-taste/scripts/inspect_video.py VIDEO OUT_DIR \
     [--at 3.9,17.0] [--zoom 0,64.5] [--every 1]
   ```

   Put OUT_DIR in your scratchpad, not the repo. Read `report.md`, then look
   at `hook.png`, every `sheet_NN.png`, and the `zoom_*.png` strips. Use
   `--zoom` on the first motion, each scene change and each key sync moment.
   Use `--at` for full-size frames when you need to check small text.
4. When the user shows a reference and says it is good or bad, add measured
   notes to `taste/motion/taste-notes.md` (format in that file) and tell the
   user what you added.
