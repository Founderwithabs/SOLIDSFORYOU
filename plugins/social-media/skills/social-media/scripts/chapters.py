#!/usr/bin/env python3
"""chapters.py - YouTube chapters from a transcript, or a check of a chapter list you wrote.

Adapted from chapters.py in youtube-agent-skill by Jake Schincariol (MIT; see
THIRD_PARTY_NOTICES.md). SOLIDS FOR YOU changes: --check validates a chapter list written by
hand (or by you, after retitling), including order and the video's length.

    python3 chapters.py transcript.srt --target 8          # draft chapters (.srt, .vtt, whisper .json)
    python3 chapters.py --check chapters.txt --duration 612 # validate "0:00 Title" lines

YouTube's rules, checked rather than assumed: the first chapter starts at 0:00, there are at least
three, each lasts at least 10 seconds, and they are in order. A list that breaks any of them
silently doesn't become chapters. Check the current rules in YouTube's help if a list still fails.

Draft boundaries come from the pauses you actually took, scored by pause length and how much the
vocabulary changes across them. Draft titles are topic words: retitle every one.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript import load, parse_ts  # noqa: E402

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

MIN = 10.0
STOP = set("the a an of for to in on and or is are was were be been with this that it as at by from "
           "you your i my we our they them he she but so if then than there here what which who how "
           "when where why not no yes do does did just really very like about into over out up down "
           "can could will would should have has had get got make made go going went one two".split())


def keywords(text):
    return {w for w in re.findall(r"[a-z']{4,}", text.lower()) if w not in STOP}


def mmss(t):
    t = int(round(t))
    h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def validate(chapters, duration):
    """chapters: [(start_seconds, title)]. Returns a list of problems."""
    problems = []
    if len(chapters) < 3:
        problems.append(f"only {len(chapters)} chapters; YouTube needs at least 3")
    if chapters and chapters[0][0] != 0:
        problems.append(f"the first chapter starts at {mmss(chapters[0][0])}; it must start at 0:00")
    for i, (t, title) in enumerate(chapters):
        end = chapters[i + 1][0] if i + 1 < len(chapters) else duration
        if i + 1 < len(chapters) and chapters[i + 1][0] <= t:
            problems.append(f"'{title}' at {mmss(t)} is not before the next chapter")
        if end is not None and end - t < MIN:
            problems.append(f"'{title}' at {mmss(t)} lasts {end - t:.0f}s; each chapter needs {MIN:.0f}s")
        if duration is not None and t >= duration:
            problems.append(f"'{title}' at {mmss(t)} starts after the video ends")
        if not title.strip():
            problems.append(f"the chapter at {mmss(t)} has no title")
    return problems


def check_list(path, duration):
    chapters = []
    for line in open(path, encoding="utf-8").read().splitlines():
        m = re.match(r"\s*\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\s*[-–:]?\s*(.*)", line)
        if m:
            chapters.append((parse_ts(m.group(1)), m.group(2).strip()))
    problems = validate(chapters, duration)
    for t, title in chapters:
        print(f"  {mmss(t)} {title}")
    if duration is None:
        print("\n  (add --duration to check the last chapter's length)")
    if problems:
        print("\n  INVALID:")
        for p in problems:
            print(f"   - {p}")
        sys.exit(1)
    print(f"\n  {len(chapters)} chapters, valid.")


def draft(path, target, as_json):
    cues = load(path)
    if len(cues) < 6:
        print("too few cues to chapter")
        sys.exit(1)
    dur = cues[-1][1]
    cand = []
    for i in range(1, len(cues)):
        gap = cues[i][0] - cues[i - 1][1]
        before = " ".join(c[2] for c in cues[max(0, i - 12):i])
        after = " ".join(c[2] for c in cues[i:i + 12])
        kb, ka = keywords(before), keywords(after)
        shift = 1 - (len(kb & ka) / len(kb | ka)) if (kb | ka) else 0
        cand.append((gap * 1.6 + shift * 3.2, cues[i][0]))
    cand.sort(reverse=True)
    picked = [0.0]
    for _, t in cand:
        if len(picked) >= target:
            break
        if all(abs(t - p) >= MIN for p in picked) and dur - t >= MIN:
            picked.append(t)
    picked.sort()
    chapters = []
    for n, t in enumerate(picked):
        end = picked[n + 1] if n + 1 < len(picked) else dur
        text = " ".join(c[2] for c in cues if c[0] >= t and c[1] <= end)
        kw = sorted(keywords(text), key=lambda w: -text.lower().count(w))
        chapters.append({"start": round(t, 2), "label": mmss(t),
                         "draft_title": " ".join(w.capitalize() for w in kw[:3]) or "Section",
                         "seconds": round(end - t, 2)})
    problems = validate([(c["start"], c["draft_title"]) for c in chapters], dur)
    if as_json:
        print(json.dumps({"valid": not problems, "problems": problems, "chapters": chapters}, indent=1))
        return
    print()
    for c in chapters:
        print(f"  {c['label']} {c['draft_title']}")
    print(f"\n  {len(chapters)} chapters" + ("" if not problems else "  -- INVALID: " + "; ".join(problems)))
    print("  Retitle every line as the promise of that section (3 to 5 words), then run --check.\n")


def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    opts = {}
    for flag in ("--target", "--duration", "--check"):
        if flag in a:
            i = a.index(flag)
            opts[flag] = a[i + 1]
            a = a[:i] + a[i + 2:]
    duration = float(opts["--duration"]) if "--duration" in opts else None
    if "--check" in opts:
        check_list(opts["--check"], duration)
    elif a and os.path.exists(a[0]):
        draft(a[0], int(opts.get("--target", 7)), as_json)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
