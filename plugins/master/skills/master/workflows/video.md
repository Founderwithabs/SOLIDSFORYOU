# Video workflow (part of the SOLIDS FOR YOU Master Skill)

You are an extremely good video editor and motion designer. Whenever you are
about to produce a video, you follow this workflow from start to finish. It
combines the SOLIDS FOR YOU video, design, audio and feedback tools into one
pipeline so that every video is the best it can be, not just finished.

## 0. When this applies

Before generating anything, ask yourself: **is the output a video?** That
includes: an MP4 or any video file, a reel, short, ad, explainer, animation,
motion graphic, title card, slideshow video, product video, edit of existing
footage, or a GIF meant to show motion. If yes, run this whole workflow, even
if the user did not mention it. If you are only planning or writing a script
for a video, run stages 1 to 3 and stop.

Do not skip a stage because the video is short or the request sounds simple.
If a stage cannot run here (no subagents, no terminal, no web search), say
which one, why, and do the closest thing you can.

## 1. Skill registry

These are the SOLIDS FOR YOU skills this workflow uses. When a stage names a
skill, use it the first time that stage starts:
- **Installed** (Claude Code plugin or claude.ai skill): invoke the skill by
  its name, for example the `careful-mode` skill.
- **Not installed:** follow its prompt file from the table. If the file is
  not on disk (for example, only this plugin is installed), read it from
  `https://raw.githubusercontent.com/Founderwithabs/SOLIDSFORYOU/main/`
  followed by the path in the table. In the bundled single-file version of
  the Master Skill, every prompt is appended at the end.
- **Neither available:** say so once, and apply the stage's instructions
  below as well as you can.

| Skill | Used in stages | Prompt file (in the SOLIDS FOR YOU repo) |
|---|---|---|
| economy-mode | 1 (on for the whole workflow) | `plugins/economy-mode/skills/economy-mode/SKILL.md` |
| careful-mode | 2, 7, and every delivery | `plugins/careful-mode/skills/careful-mode/careful-mode.md` |
| motion-design-taste | 3, 6, 8 | `plugins/motion-design-taste/skills/motion-design-taste/motion-design-taste.md` |
| audio-review | 4, 6, 8 (whenever the video has sound) | `plugins/audio-review/skills/audio-review/initiation_prompt.md` |
| harsh-buyer-review | 5 | `plugins/harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md` |

Tools. The video build tools sit in the `master` skill's folder, next to its
SKILL.md (in Claude Code, `${CLAUDE_SKILL_DIR}`); below, `SKILL_DIR` means
that folder.
- `SKILL_DIR/templates/scene-template.html`: starting point for an HTML
  motion-graphics scene driven by `renderFrame(t)`.
- `SKILL_DIR/scripts/render_html_video.cjs`: renders that page to MP4 frame
  by frame, optionally with audio, or to a transparent ProRes 4444 `.mov`.
- `SKILL_DIR/scripts/sfx_mix.py`: synthesizes sound effects, places them on
  cue times, mixes them under the voiceover and normalizes loudness.
- The motion-design-taste skill's `scripts/inspect_video.py`: turns a video
  into contact sheets, a hook strip, frame-by-frame strips, cut times, static
  stretches and loudness. The audio-review skill's `analyze.py` measures the
  soundtrack.

If you do not have these files (for example, in a chat with only this
document), build the same thing yourself: stage 4 describes how each tool
works, and the ffmpeg commands in the motion design taste prompt replace the
inspection script. Check that Chromium (via Playwright) and ffmpeg are
available before planning a render; if they are not, say so at stage 2.

## 2. The pipeline at a glance

```
1 Economy mode on ──► 2 Careful brief ──► 3 Taste: pre-production
                                                   │
             ┌─────────────────────────────────────┘
             ▼
4 Build and draft render ──► 5 Harsh buyer review ──► 6 Taste review and fix list
                                                              │
             ┌────────────────────────────────────────────────┘
             ▼
7 Careful review of the fix plan ──► 8 Final regeneration ──► deliver
                                          │        ▲
                                          └────────┘  up to 3 rounds until the bar is met
```

Keep a short running log as you go (stage, what you did, scores, open
questions). You will need it for the final report.

## Stage 1: Economy mode on

Use the economy-mode skill for the whole workflow.
- Delegate low-judgment work: running renders and inspection scripts and
  reporting the output, extracting frames, converting files, generating
  sound effects from a cue list, collecting reference links, first-pass
  competitor searches.
- Keep for yourself: the brief, creative direction, every design decision,
  every review and score, the fix plan, and the final sign-off.
- Never do maths in your head or on a cheaper model: compute timings, frame
  counts and loudness in code, and check the result.
- Every review in this workflow (stages 5 to 8) is done by you, never by a
  cheaper model. Helpers may gather evidence for a review; they do not judge.

## Stage 2: Careful brief

Use the careful-mode skill. Careful mode stays on until delivery.
Before making anything, write down the brief as a numbered requirement list:
- the goal: the one thing a viewer must understand, feel or do;
- the audience and where it will be watched (platform, phone or desktop,
  sound on or off);
- format: aspect ratio, resolution, frame rate, length;
- inputs: script, voiceover, footage, brand assets, references, and which are
  final;
- style decisions that must not change;
- what "done" means: the deliverables and the quality bar (below).

Ask the user, in one message, only for what is missing and would change the
result. Never invent facts, claims, prices or brand details.

**Quality bar (default; the user can change it):**
- motion design taste score of at least 85 out of 100,
- no criterion below 7 out of 10,
- audio review: no clipping, voice clear above effects, loudness on target
  for the platform,
- no open problem from the harsh buyer review that the user would see as
  serious ("would scroll past", "can't read", "don't believe it"),
- careful mode's three reviews all pass on the final file.

## Stage 3: Taste: pre-production

Use the motion-design-taste skill, starting before anything is built.
1. Read the user's taste notes, wherever that skill says they live (the
   project's `taste/motion/taste-notes.md`, the plugin data folder, or what
   the user pasted).
2. Inspect each reference video the user gave, as in section 1 of that
   prompt, and note the measurable techniques worth matching.
3. Write a **style spec**: palette with hex values and the meaning of each
   colour, typefaces and sizes (as px at the target resolution), grid and
   margins, motion vocabulary (entrance and exit types, durations in frames,
   easing, stagger), transition types, sound palette and loudness target.
4. Write a **scene plan**: one row per beat with start and end time (from the
   voiceover timing when there is one), what is said, what is on screen, what
   moves and how, and which sound effect lands where. Every spoken line gets
   its own visual change. One idea per screen.
5. Check the plan against the brief before building. Fixing a plan costs
   minutes; fixing a render costs a re-render.

## Stage 4: Build and draft render

Choose the build path that fits the inputs.

**Path A: motion graphics (no footage).** Build an HTML page per video (or
per scene) from the scene template:
- All motion is driven by `renderFrame(t)` so the same time always gives the
  same frame. No CSS transitions or animations, `setTimeout`, or real-time
  video playback.
- Put every cue time in one `CUE` table at the top, taken from the scene
  plan. Never scatter magic numbers through the code.
- Use the template's `tween`, `enter` and easing helpers: entrances ease out,
  exits ease in and are shorter, groups stagger by 2 to 4 frames, overshoot
  only on the one or two moments that deserve it.
- Use local or embedded fonts. Keep light grain over gradients to prevent
  banding.
- Render a short section first (`--from`/`--to`) and inspect it before
  rendering the whole video.

```
node "SKILL_DIR/scripts/render_html_video.cjs" \
  scene.html draft.mp4 --fps 30 --width 1920 --height 1080 [--audio mix.wav] [--from 0 --to 6]
```

**Path B: editing footage.** Use ffmpeg. Re-encode with `-c:v libx264 -crf 17
-pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart` unless only
copying streams. For talking-head footage with a transcript (.srt, .vtt or
Whisper .json), start from the rough cut: `python3
"SKILL_DIR/scripts/transcript_edit.py" transcript.srt` lists dead air,
filler and retakes, and `--apply in.mp4 rough.mp4` cuts them. Check the list
against the footage first: a silent demo is not dead air.

```
# Trim (frame-accurate, re-encoded)
ffmpeg -ss 12.4 -to 18.9 -i in.mp4 -c:v libx264 -crf 17 -c:a aac clip.mp4

# Crossfade two clips (offset = first clip length minus fade length)
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=3.5[v];[0:a][1:a]acrossfade=d=0.5[a]" -map "[v]" -map "[a]" out.mp4

# Reframe 16:9 to 9:16 (centre crop; move x= to follow the subject)
ffmpeg -i in.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a copy vertical.mp4

# Duck music under the voice (MUSIC is input 0, VOICE is input 1)
ffmpeg -i music.mp3 -i voice.wav -filter_complex "[1:a]asplit=2[sc][vo];[0:a][sc]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[ducked];[ducked][vo]amix=inputs=2:normalize=0[a]" -map "[a]" mix.wav

# Burn in captions from an .srt file
ffmpeg -i in.mp4 -vf "subtitles=captions.srt:force_style='FontName=Arial,FontSize=18,Bold=1,Outline=2,MarginV=60'" -c:a copy captioned.mp4

# Gentle colour correction
ffmpeg -i in.mp4 -vf "eq=contrast=1.08:saturation=1.1:gamma=0.97" -c:a copy graded.mp4

# Speed up 1.25x (video and audio together)
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS/1.25[v];[0:a]atempo=1.25[a]" -map "[v]" -map "[a]" faster.mp4
```

Editing rules: cut on action or on the beat of the voice; remove dead air,
ums and repeated takes; vary shot length; captions in short chunks (one to
seven words) that appear with the words; music under a voice ducks by 10 to
15 dB; no jump between very different colour looks.

**Path C: both.** Edit the footage first (Path B). Then build the graphics as
in Path A with a transparent page background (`html, body { background:
transparent; }`), render them with `--transparent` to a ProRes 4444 `.mov`
with alpha, and lay them over the footage:

```
node "SKILL_DIR/scripts/render_html_video.cjs" \
  graphics.html graphics.mov --transparent
ffmpeg -i footage.mp4 -i graphics.mov -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass[v]" \
  -map "[v]" -map 0:a -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac final.mp4
```

**Sound (every path).** Write a cue list from the scene plan and mix it:

```
python3 "SKILL_DIR/scripts/sfx_mix.py" --cues cues.json \
  --duration 102.5 --vo vo.mp3 --out mix.wav
```

Built-in sounds: whoosh (transitions), pop and tick (small elements),
thump (emphasis), ding (answers and success), riser (build into a reveal).
Effects sit about 10 dB under the voice (gain 0.2 to 0.35), land on the exact
frame of their motion, and never more than one per second unless the moment
calls for it. Final loudness: -14 LUFS integrated, true peak -1.5 dBTP.

**Draft check.** Run `inspect_video.py` on the draft, and when the video has
sound, run the audio-review skill on it (it accepts video files) for the
voiceover and mix. Before moving on, fix anything broken outright: missing
frames, wrong length, out-of-sync audio, clipping, text off screen, errors in
the page console.

## Stage 5: Harsh buyer review

Use the harsh-buyer-review skill on the draft render.
- The "buyer" is the person the video is for: the customer for an ad or
  listing video, the student for a lesson, the company being pitched for a
  pitch video. Fill in section 1 of that prompt from the brief. Never invent
  claims the user did not provide.
- The "competitors" are the videos this one competes with for the same
  viewer's attention: comparable videos on the same platform and topic. Find
  them with web search when available; otherwise use the user's references
  and say research was not possible.
- Review the video second by second as that prompt requires, including
  whether it works on mute.
- Keep the buyer's top fixes. They feed stage 6.

## Stage 6: Taste review and fix list

Use the motion-design-taste skill on the same draft, and the audio-review
skill on its soundtrack.
1. Inspect the draft and every reference video with the same method.
2. Score the draft with the full scorecard, and rank it against the
   references.
3. Merge the buyer's fixes (stage 5), the taste fixes and the audio fixes
   into **one ranked fix list**. Remove duplicates. For each fix: timestamp, evidence, the exact
   change with numbers, which review it came from, and expected score gain.
4. Mark any fix that would change the script, the voiceover, the brand look
   or a style decision the user made. Those need the user's approval.

## Stage 7: Careful review of the fix plan

Use the careful-mode skill on the fix list itself, before changing
anything:
1. **Correct?** Every fix's evidence is real (you looked at that frame) and
   its numbers are right.
2. **Complete?** Every requirement from the stage 2 brief is either already
   met or covered by a fix. Nothing in the list breaks a user decision.
3. **What could go wrong?** Which fixes could break something else (timing
   that shifts later cues, a bigger text that now overlaps)? Plan how to
   check for that.
Ask the user about marked fixes in one message. Carry on with the rest.

## Stage 8: Final regeneration

1. Apply the approved fixes, highest gain first.
2. Re-render (affected section first, then the whole video), re-mix audio if
   cue times changed.
3. Inspect the new render again. Never claim a fix worked without looking at
   the new frames.
4. Re-score with the motion design taste scorecard (and re-run the audio
   review if the sound changed). Show before and after per criterion.
5. If the quality bar is not met, return to stage 6 with the new render (and
   stage 5 if the problems are about message or appeal rather than craft).
   Stop after three rounds, or earlier if what remains needs a user decision,
   and say exactly what is left and why.
6. Final careful mode pass on the file you will deliver: play-through checks
   (length, start and end frames, audio present and in sync, loudness, no
   black or frozen frames, file opens), and every requirement in the brief
   ticked off.

## Delivery

Deliver the final file (as a download or at the path the user asked for),
then a short report:
1. **Verdict**: final score out of 100, and whether the quality bar was met.
2. **Scorecard**: before and after for each criterion.
3. **Ranking** against the references.
4. **Buyer verdict**: would the target viewer keep watching or buy, and the
   remaining biggest objection.
5. **What changed** across rounds, in a few lines.
6. **Open items** that need the user (approvals, assets, decisions).
7. **Careful mode record** for the final file.
8. **Economy mode line**: what ran on which model.
9. **Taste notes to save**: anything learned from the references.

Keep the source files (HTML, cue lists, mixes) with the video so it can be
changed later. If the session's files will be lost, give the user the source
files as downloads too.

## How to add a new skill to this workflow

This document is meant to grow. To add a SOLIDS FOR YOU skill to it:
1. Add the skill to the Master Skill first (section 6 of `master.md`).
2. Add a row to the skill registry table in section 1: the skill's name, the
   stages that use it, and its prompt file.
3. Add or edit a stage in the pipeline that says exactly when to use it, what
   it takes in, and what it hands to the next stage. If it is a new stage,
   add it to the diagram in section 2.
4. Run `python3 scripts/build_bundle.py` to rebuild `dist/master-full.md`,
   the single file other people's Claude can read.
