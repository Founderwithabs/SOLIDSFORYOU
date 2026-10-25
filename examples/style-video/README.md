# Example: SOLIDS FOR YOU in a liked reel's style

A 34-second 4:5 video (1080 × 1350, 30 fps, -14 LUFS) made with the Master
Skill's video workflow, matching the motion style of a reference reel the
founder liked:
- a hard cut on almost every beat (the reference averages 1.7 s a shot);
- grey-vignette UI scenes, black and neon-magenta word slams with
  hand-drawn strokes, an old-paper look;
- highlighter sweeps, a cursor dot with a trail, red check timelines.

- [`solids-style.mp4`](solids-style.mp4): the video.
- `source/solids.html`: the scene, driven by `renderFrame(t)`, cuts in beats.
- `source/cues.json`: the sound cues for `sfx_mix.py`.

Every claim on screen is true: 14 free skills, and Reels Publisher for
Instagram is the one paid skill. No view counts are shown.

## Sound

All CC0, from the SOLIDS FOR YOU sound library, so no credit is required:
- Music: "Dear Mr Super Computer" by HoliznaCC0 (alvana-audio), from 7.363 s, high-passed at 70 Hz.
- Effects: wyzowl/sfx-kit.

## Rebuild

1. Fetch the sounds with `get_sounds.py fetch sfx-kit` and
   `get_sounds.py fetch alvana --category music-tech`.
2. Mix with `sfx_mix.py --cues source/cues.json --duration 33.996 --vo music.wav`
   (cue paths point at the sound cache; adjust them to yours).
3. Render with `render_html_video.cjs source/solids.html out.mp4 --width 1080 --height 1350 --audio mix.wav`.
