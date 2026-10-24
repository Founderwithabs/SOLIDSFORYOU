# YouTube (part of SOLIDS FOR YOU Social Media)

Everything specific to running a founder's YouTube channel. Use it with
`social-media.md`: always its sections 1, 2 and 3 (rules, brand memory, job
table), plus the sections named below. Ideas and tools here are adapted from
youtube-agent-skill by Jake Schincariol (MIT; see THIRD_PARTY_NOTICES.md).

## 1. What Claude can and can't do on YouTube

- **Can:** write scripts, titles, thumbnail briefs, descriptions, chapters
  and replies; plan; read exports the founder downloads (retention,
  analytics CSVs); read transcripts; read public channel listings with
  `yt-dlp` where the network allows; cut a rough edit from a transcript
  (the `master` skill's `transcript_edit.py`).
- **Can't, by default:** log in, upload, publish, change a live video,
  reply to comments on the channel or see private analytics. The founder
  publishes. If the founder connects a YouTube connector or the YouTube Data
  API with their own consent, Claude can use what it allows (for example
  reading analytics or updating a description), and still asks before any
  change that is public.
- **Never:** use someone else's account, scrape behind a login, buy views,
  or automate engagement.

## 2. The voice file

Every script is spoken on camera, so the voice matters more here than
anywhere. Use `brand-voice.md` from the founder's `social/` folder (section 2
of `social-media.md`). If it has no transcripts yet, ask for three of the
founder's own videos or transcripts and add how they actually talk, their
phrases, words they never use and what they won't claim.

## 3. Long-form script

**The first 15 seconds are the whole job.** They must confirm the click the
title promised, open a question the viewer can't close, and prove the payoff
exists.

1. **Hook.** Write five, using the formulas in `scripts/hooks.json`, score
   them with `scripts/hookscore.py` (long format), and show the founder the
   top two with their scores.
2. **The turn (about 0:15 to 0:45).** Say what the video will do in one
   sentence and start doing it. No channel intro, no "before we get
   started", no subscribe pitch: they cause the early cliff.
3. **The body.** One idea per beat. Mark every beat with what is ON SCREEN,
   not just what is said: a talking head with nothing to look at is a podcast.
4. **The payoff.** Deliver what the hook promised, explicitly.
5. **The close.** One ask, not three.

Hand back: the two best hooks with their score panels, the script beat by
beat with `[ON SCREEN: ...]` on every beat, the runtime at about 150 words a
minute (or the founder's measured pace) calculated in code, and the formula
the winning hook used and why it fits.

## 4. Packaging: title and thumbnail

Follow section 6.8 of `social-media.md` and lint every candidate with
`scripts/package_check.py`. For the winner, write the thumbnail brief: the
expression, the framing, the three words, and what the background must do to
hold contrast at feed size. If retention is healthy but views are low, the
problem is packaging, not the video.

## 5. Description, tags and search

- **The first two lines are the only ones most people read.** They show
  above "...more" and in search. Say what the video gives, in the words the
  viewer would type. Then the link or resource, if any.
- Then chapters (section 6), then the longer version: what's covered, who
  it's for, what it assumes.
- **Tags** are a weak signal. Use them for spellings, tool and brand names
  and abbreviations people really type; about fifteen is plenty. Unrelated
  tags break YouTube's rules.
- **The query test:** write the three searches the video should win and
  check the title and the first two description lines contain their words.
  If they don't, fix the title.
- For videos aimed at subscribers rather than search, say so and spend the
  effort on packaging instead.

## 6. Chapters

```
python3 "SKILL_DIR/scripts/chapters.py" transcript.srt --target 8
python3 "SKILL_DIR/scripts/chapters.py" --check chapters.txt --duration <seconds>
```

The first command drafts boundaries from the pauses and topic shifts in the
transcript. Retitle every chapter as the promise of that section, three to
five words in the founder's voice, then validate the final list with
`--check` (first chapter at 0:00, at least three, each at least 10 seconds,
in order). A section that can't be named in five words is two sections or
filler.

## 7. Editing a raw recording

With a timestamped transcript (from the SOLIDS FOR YOU `transcriber` skill,
which makes one from the uploaded video in the chat, or from the captions
YouTube makes for an unlisted upload):

```
python3 "<master skill folder>/scripts/transcript_edit.py" transcript.srt [--apply raw.mp4 rough_cut.mp4]
```

It lists dead air (trimmed from the middle so both sides keep a breath),
filler-only lines and restarted sentences, with timecodes, and can apply
them with ffmpeg. Check the list against the footage first: a silent demo
isn't dead air. For a full edit with graphics, use the `master` skill's video
workflow.

## 8. Shorts from a long video

Follow section 8, step 4 of `social-media.md`: self-contained 20 to 55
second spans, a new first line for each, on-screen text, a loop point, and
the vertical crop.

## 9. Retention, analytics and audits

- Retention exports: section 9.2 of `social-media.md` (`scripts/retention.py`).
- Channel audit: section 7.3 of `social-media.md`, ending in one fix.
- Comments: section 11 of `social-media.md` (triage, short replies, one pin).
- What's working in the niche: section 10, step 2 (`scripts/outliers.py`).
- Weekly plan: section 5 (anchor video, one cheap video, Shorts cut from the
  anchor, sized to the founder's real hours).

Every delivery ends with the question: **Ship it, or change it?**
