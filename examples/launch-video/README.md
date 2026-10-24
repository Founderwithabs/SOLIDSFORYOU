# Example: the launch video, made by the Master Skill's video workflow

![The SOLIDS FOR YOU launch video](../../assets/demo.gif)

The video at the top of the README was made by Claude with the SOLIDS FOR
YOU video workflow, start to finish: a brief, a style spec and scene plan, a
build in HTML rendered frame by frame, then a harsh buyer review, a motion
design review and an audio review on every draft, with fixes in between. The
GIF is the silent version; the full video has music and sound effects.

## Version 2: rebuilt after the founder's review

The first version scored 83 on the rubric, and the founder rejected it
anyway: "all of these motions look the same, all of the cards look the same,
the background feels very childish." They were right, and the rubric missed
it, so the verdict went into `taste/motion/taste-notes.md` as a measured
note. Version 2 was rebuilt from those notes:

- **Background:** off-black (#0a0a0a) with a 120 px grid of 1 px lines,
  instead of a soft blue glow on navy. One accent colour (#ff5b2e), used
  only for what matters.
- **Type:** Inter Display for headlines, Inter for body, JetBrains Mono for
  labels and data.
- **A different visual for each tool,** showing what the tool does:
  - Harsh Buyer: a listing marked up in pen, then stamped "NOT YET".
  - Ecom: a price chart whose last bar earns less.
  - Competitor Research: a ledger whose rows are verified one by one.
  - Social Media: a post with its 10-criterion scorecard.
  - Video: an edit timeline with this video's own review scores.
- **A different motion for each job:**
  - headlines rise from behind a mask;
  - annotations draw like a pen;
  - bars grow from the baseline;
  - rows type in and light up as they're checked;
  - score bars fill;
  - clips cut onto tracks;
  - tile borders draw on a diagonal.
- **Four kinds of transition,** none of them a fade: hard cuts on the
  beat, an orange wipe, a push up and a zoom through.

## The brief

- **Goal:** in about 30 seconds, a founder on GitHub or X understands "11
  Claude specialists for founders, installed in two commands, free" and
  stars or installs it.
- **Format:** 1920 × 1080, 30 fps, 32 s. Must work on mute (README GIFs and
  most social autoplay are silent).
- **Rule:** no invented claims.
  - The chart is the real output in
    [`../ecom-unit-economics`](../ecom-unit-economics).
  - The listing is labelled "illustrative".
  - The social scorecard is labelled "example" and uses the real criteria
    and weights from the Social Media skill.
  - The review scores are this video's own.

## Rounds (version 2)

| Round | What changed | Motion design score |
|---|---|---|
| Draft | New design from the taste notes | 83 |
| Round 1 | The ledger's ticks spread over the beat, and each row lights up as it is verified (the scene stood still for 1.8 s); an underline draws under "solid." at the end; labels 24 to 26 px | 84 |
| Final | The video scene shows these real scores | 86 |

**Final: 86 out of 100, above the workflow's bar of 85.**

| Criterion (weight) | Score | Evidence |
|---|---|---|
| Hook (1.5) | 9 | "Claude is smart." is on screen from frame 0; "solid." slams in at 300 px on beat 3 (1.39 s) with an impact |
| Clarity (1.5) | 9 | Each tool shows its proof: the marked-up listing, the real chart, the ledger, the scorecard, the scores |
| Motion purpose (1.2) | 9 | Every move shows something happening: a pen marking, bars growing, rows being verified, a playhead running |
| Timing and easing (1.2) | 8 | Quartic ease-out reveals of 14 frames, 3-frame staggers; overshoot only on "solid." and the stamp |
| Rhythm and sync (1.0) | 9 | Scene changes on the bar (8 beats per tool); 34 effects, each on its sync point |
| Typography (1.0) | 8 | Two families plus a mono; mono labels are still small on a phone |
| Layout (0.8) | 8 | A 96 px margin and a 120 px grid throughout; left text column, right visual |
| Colour and finish (0.6) | 9 | One background, one accent with one meaning, grain against banding |
| Audio (0.6) | 8 | -13.9 LUFS, -2.4 dBTP, no clipping; music EQ'd for phone speakers |
| Works on mute and ending (0.6) | 9 | Text carries everything; ends on the URL, the star line and a drawn underline |

**Harsh buyer (a founder scrolling X):** keeps watching, because every scene
shows a different thing happening, and the ₹1,099 bar coming out lower is
a reason to stop. Biggest objection: the listing and scorecard are
illustrative. The real chart and [`../ecom-unit-economics`](../ecom-unit-economics)
answer part of it; a recording of a real session would answer the rest.

## Sound

Both are from the SOLIDS FOR YOU sound library
(`plugins/master/skills/master/sounds/`), and both are CC0, so no credit is
required:

- **Music:** "Dear Mr Super Computer" by HoliznaCC0, via
  [alvana-audio](https://github.com/seyedpouramir/alvana-audio). It starts at
  7.363 s so the video opens at full energy, and is EQ'd for phones.
- **Effects:** [wyzowl/sfx-kit](https://github.com/wyzowl/sfx-kit):
  - marker strokes for the annotations, an impact for the stamp;
  - bar-grow and number-land for the chart, pen ticks for the ledger;
  - a count-up for the score, a progress sweep for the timeline;
  - whooshes and swipes for the transitions, typing for the install, and a
    tech logo sting.

## Rebuild it

`source/` has the scene (`scene.html`), the beat grid (`beats.json`) and the
sound cues (`cues.json`, paths relative to the sound library's download
folder).

1. In the scene, replace `__BEATS__` with the `beats` list and `__ROUNDS__`
   with `[["Draft","83"],["Round 1","84"],["Final","86"]]`.
2. Fetch the sounds with `get_sounds.py fetch sfx-kit` and
   `get_sounds.py fetch alvana --category music-tech`.
3. Mix with `sfx_mix.py` and render with `render_html_video.cjs`.
