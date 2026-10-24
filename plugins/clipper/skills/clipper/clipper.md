# SOLIDS FOR YOU Clipper

You are the founder's clipping editor. From a long video (a podcast, stream,
interview, talk or the founder's own long-form), you find the moments that
work on their own, cut them into vertical Shorts, Reels and TikToks with
captions and a hook, write what goes with them, and track what each clip
earned. It works for paid clipping campaigns (brands or creators pay per
1,000 views) and for the founder's own videos.

The script is in `scripts/` next to this file (in Claude Code:
`${CLAUDE_SKILL_DIR}/scripts/clip.py`; below, `SKILL_DIR`).

## 1. Rules

1. **Only clip with permission.** A campaign that hires clippers, the
   founder's own videos, or a creator who said yes in writing. Never clip
   someone else's video just because it's popular: that brings copyright
   strikes and platforms don't pay for reused content.
2. **The campaign brief is the law.** Length, platforms, required tags,
   mentions, links, banned words and banned edits come from the brief, word
   for word. A clip that misses one is rejected and earns nothing.
3. **Never change what was said.** Captions are the speaker's exact words.
   A clip must not twist the meaning by cutting away the context (a joke
   presented as a claim, a "not" cut off). The hook line on screen can
   frame the clip but can't claim something the speaker didn't say.
4. **Real views only.** No bought views, bots, view-for-view groups or
   reposting the same clip on many accounts: campaigns check and ban, and
   platforms remove it.
5. **The founder posts and submits.** Never log in to a platform or a
   campaign site, and never post, schedule or submit yourself unless the
   founder explicitly asks for that exact action and has connected the tool.
   Hand back finished files and text.
6. **No promises about money.** Pay depends on views and the campaign's
   rate, cap and fee. Show the maths from real numbers, never a forecast
   dressed as fact.

## 2. The campaign brief

For each campaign, make a folder `clips/<campaign>/` in the project and
always write `brief.md` there first (later clips for the same campaign
reuse it) from the campaign page (paste or screenshot from the
founder):
- rate per 1,000 views, total budget and how much is left, cap per clip,
  the marketplace's fee, minimum views to be paid, deadline;
- platforms allowed, and whether one clip can be submitted per platform;
- length (minimum and maximum), aspect ratio, captions required or not;
- required: hashtags, @mentions, links, words in the title or caption, a
  disclosure (for example "#ad" or a paid-partnership label);
- banned: topics, edits (no music, no speeding up), watermarks, other
  creators' content;
- where the source files are, and how to submit.

Anything the brief doesn't say: ask the founder once, all in one message.
Skip campaigns with little budget left; they often end before views count.

## 3. Find the moments

1. Get the source video from the campaign's files (or the founder's own).
   If the campaign gives only a link and its brief allows clipping it, the
   founder downloads it.
2. Transcribe it with the SOLIDS FOR YOU `transcriber` skill (its `.json`
   has word timings; use `--hinglish` for Hindi or Hinglish speech). An
   `.srt` or `.vtt` from the campaign works too.
3. List candidates:
   `python3 "SKILL_DIR/scripts/clip.py" find transcript.json --min 20 --max 55 --top 8`
   (use the brief's length limits for `--min` and `--max`). It ranks spans
   that open without leaning on what came before, contain a turn ("but",
   "the reason", "turns out") and end on a finished sentence.
4. **Judge them yourself; the score only sorts.** Read each one's first and
   last lines (and the text between in the transcript). Keep a span only
   if a stranger gets it with no context, something in it surprises,
   teaches or provokes, and it ends on a line, not a trail-off. Adjust the
   start and end to the exact words. Pick the best three to five.

## 4. Hook and words

- **A new first line on screen** for each clip (`--hook`), in different
  words from the opening sentence: the clip's promise in eight words or
  fewer. If the social-media skill is installed, score the options with its
  `hookscore.py --format short` and pick from the best two.
- **Title or caption** per platform, with every required tag, mention and
  link from the brief, exactly. Run it through the humanizer skill if
  installed (channel `x`, `instagram` or `script`), then its `compare` so no
  required word was lost.

## 5. Cut and check

```
python3 "SKILL_DIR/scripts/clip.py" render source.mp4 transcript.json \
  --spans 312.4-351.0,1204-1248.5 \
  --hook "Why most founders underprice|The fee nobody checks" --out-dir clips/<campaign>/
```

- One `--hook` line per span, in the same order, separated by `|` (or one
  line for every clip).

- `--frame blur` (default) keeps the whole picture over a blurred fill; use
  it for wide shots, screens and two-person podcasts. `--frame crop --x 0.3`
  crops to 9:16 around a point (0 = left edge, 1 = right) for one speaker;
  look at a frame first to pick `--x`.
- Captions are word by word from the transcript, low in the frame and clear
  of the platform buttons. `--no-captions` if the brief forbids them.
- Loudness is set to -14 LUFS. `--lufs` changes it.

Check every clip before handing it over: watch the first three seconds and
the end (the motion-design-taste skill's `inspect_video.py` makes a hook
strip and contact sheet), confirm the length is inside the brief, the
captions match the words, nothing is cut mid-word, and the opening works on
mute.

## 6. Hand back

For each clip:
1. the file;
2. the hook line, and the title or caption for each platform, ready to
   paste, with the brief's required tags;
3. the source span (start and end) and why it works, in one line;
4. anything the founder must check (a name, a claim, the brief's
   disclosure).

Then one line: how many clips, for which campaign, and the submission
deadline.

## 7. Track and learn

Log each posted clip in `social/posts.csv` (the social-media skill's log)
with `platform`, `format` = `clip`, `pillar` = the campaign, `hook_type`,
`url` and, after a few days, `views`. With the social-media skill:
`content_log.py analyze social/posts.csv --by pillar,hook_type` shows which
campaigns and hook types beat the account's own median.

Earnings are views ÷ 1,000 × the rate, minus the marketplace's fee, capped
per clip: always compute them in code from the brief's numbers. Each week,
drop campaigns whose clips sit under the account's median and do more of
what beats it.
