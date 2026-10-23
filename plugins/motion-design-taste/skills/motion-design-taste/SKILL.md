---
name: motion-design-taste
description: Judge motion graphics videos with a senior motion designer's taste. Inspects a rendered video (contact sheets, frame-by-frame strips, cuts, loudness), scores it on a 100-point rubric, compares and ranks it against any other videos, lists exact fixes, and when the source is available applies the fixes, re-renders and re-scores. Use for any video review, "is this video good", "compare these videos", "rank these", "fix the animation", "/motion-design-taste", and before delivering any video Claude made.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Read `SKILL_DIR/motion-design-taste.md` and follow it exactly. It holds the
   taste rules, the rubric, the comparison method, the fix loop and the
   output format.

2. Read the user's taste notes before every review. They record this user's
   taste, learned from real videos, and override the general rules when they
   conflict. Use the first of these that exists:
   - `taste/motion/taste-notes.md` in the current project,
   - `${CLAUDE_PLUGIN_DATA}/taste-notes.md` (Claude Code; it survives plugin
     updates),
   - notes the user pasted into the chat.

   If there are none yet, use the format in
   `SKILL_DIR/taste-notes-template.md` when you first save one. Save to the
   project file if the project has a `taste/motion/` folder, otherwise to
   `${CLAUDE_PLUGIN_DATA}/taste-notes.md`. Outside Claude Code, give the user a
   "Taste notes to save" block instead.

3. Inspect every video, including each reference, with the bundled script
   instead of typing the ffmpeg commands by hand:

   ```
   python3 "SKILL_DIR/scripts/inspect_video.py" VIDEO OUT_DIR \
     [--at 3.9,17.0] [--zoom 0,64.5] [--every 1]
   ```

   Put OUT_DIR in a scratch or temp directory, not the user's project. Read
   `report.md`, then look at `hook.png`, every `sheet_NN.png` and the
   `zoom_*.png` strips. Use `--zoom` on the first motion, each scene change and
   each key sync moment. Use `--at` for full-size frames when you need to check
   small text. The script needs `ffmpeg` and `ffprobe`. If they're missing and
   you can't install them, follow the no-terminal path in section 1 of the
   prompt.

4. When the user shows a reference and says it is good or bad, add measured
   notes to the taste notes (step 2) and tell the user what you added.
