#!/usr/bin/env python3
"""transcript_edit.py - an edit list from a timestamped transcript, and optionally the cut video.

Adapted from deadair.py in youtube-agent-skill by Jake Schincariol (MIT; see
THIRD_PARTY_NOTICES.md next to this skill). SOLIDS FOR YOU changes: overlapping cuts are merged
before totals are counted, --keep-filler and --no-repeats switch checks off, and --apply cuts the
video and audio with ffmpeg so the edit list becomes a finished rough cut.

    python3 transcript_edit.py transcript.srt                       # .srt, .vtt or whisper .json
    python3 transcript_edit.py transcript.srt --floor 0.35 --json
    python3 transcript_edit.py transcript.srt --apply in.mp4 out.mp4

Finds:
  DEAD    gaps between spoken cues longer than the floor, trimmed from the MIDDLE so both
          sides keep a breath (cutting flush against speech sounds gasping)
  FILLER  cues that are nothing but filler ("um", "so yeah", "basically")
  REPEAT  a sentence restarted: the earlier take is cut when the new cue opens with the same
          three or more words and they cover most of the earlier take (60%+), compared against
          the last real speech cue so retakes with an "um" between them are caught

Check the list against the footage before applying: a long silent demo or B-roll section is not
dead air. The removed percentage is a share of the timeline, not of the speech.
"""
import json
import os
import re
import shutil
import subprocess
import sys

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

FILLER_ONLY = re.compile(r"^[\s,.-]*((um+|uh+|er+|ah+|hmm+|so|okay|ok|right|yeah|like|anyway|basically|"
                         r"actually|you know|i mean|let me see|hold on)[\s,.-]*)+$", re.I)


def parse_ts(s):
    s = s.strip().replace(",", ".")
    p = s.split(":")
    if len(p) == 3:
        return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
    if len(p) == 2:
        return int(p[0]) * 60 + float(p[1])
    return float(p[0])


def load(path):
    try:
        raw = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError as e:
        sys.exit(f"can't read {path}: {e.strerror}")
    if path.lower().endswith(".json"):
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            sys.exit(f"{path} isn't valid JSON; give Whisper's .json, an .srt or a .vtt")
        segs = d.get("segments", []) if isinstance(d, dict) else d
        cues = []
        for s in segs if isinstance(segs, list) else []:
            try:
                cues.append((float(s["start"]), float(s["end"]), (s.get("text") or "").strip()))
            except (TypeError, KeyError, ValueError):
                continue  # a segment without times can't be placed
        return cues
    cues, cur = [], None
    for line in raw.splitlines():
        m = re.match(r"\s*(\d[\d:.,]*)\s*-->\s*(\d[\d:.,]*)", line)
        if m:
            try:
                cur = [parse_ts(m.group(1)), parse_ts(m.group(2)), []]
            except ValueError:
                cur = None  # an unreadable timestamp: skip that cue
                continue
            cues.append(cur)
        elif cur is not None and line.strip() and not line.strip().isdigit() \
                and not line.startswith(("WEBVTT", "NOTE")):
            cur[2].append(re.sub(r"<[^>]+>", "", line.strip()))
    return [(a, b, " ".join(t)) for a, b, t in cues if t]


def norm(t):
    return re.sub(r"[^a-z ]", "", t.lower()).split()


def find_cuts(cues, floor, filler=True, repeats=True):
    cuts = []
    for i, (s, e, t) in enumerate(cues):
        if filler and FILLER_ONLY.match(t):
            cuts.append({"kind": "FILLER", "start": s, "end": e, "why": t.strip()[:48]})
        if i:
            gap = s - cues[i - 1][1]
            if gap > floor:
                keep = floor / 2
                cuts.append({"kind": "DEAD", "start": round(cues[i - 1][1] + keep, 3),
                             "end": round(s - keep, 3), "why": f"{gap:.2f}s gap"})
        if repeats and t.strip() and not FILLER_ONLY.match(t):
            j = i - 1
            while j >= 0 and (FILLER_ONLY.match(cues[j][2]) or not cues[j][2].strip()):
                j -= 1
            if j >= 0:
                prev, cur = norm(cues[j][2]), norm(t)
                same = 0
                while same < min(len(prev), len(cur)) and prev[same] == cur[same]:
                    same += 1
                if same >= 3 and (same >= 5 or same / len(prev) >= 0.6):
                    cuts.append({"kind": "REPEAT", "start": cues[j][0], "end": cues[j][1],
                                 "why": f'restart of "{" ".join(prev[:same])}"'})
    cuts = sorted((c for c in cuts if c["end"] > c["start"]), key=lambda c: c["start"])
    return cuts


def merge(cuts):
    """Union of the cut intervals, so overlapping cuts are counted once."""
    spans = []
    for c in cuts:
        if spans and c["start"] <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], c["end"])
        else:
            spans.append([c["start"], c["end"]])
    return spans


def keep_spans(spans, duration):
    keep, t = [], 0.0
    for s, e in spans:
        if s > t:
            keep.append((t, s))
        t = max(t, e)
    if t < duration:
        keep.append((t, duration))
    return keep


def media_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=nw=1:nk=1", path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffprobe failed on {path}: {r.stderr.strip()}")
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit(f"{path} has no playable length: is it a video or audio file?")


def apply(spans, src, dst):
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("--apply needs ffmpeg: install it (Mac: brew install ffmpeg; Windows: winget install "
                 "ffmpeg; Linux: sudo apt install ffmpeg), or apply the edit list by hand")
    if not os.path.isfile(src):
        sys.exit(f"not a file: {src}")
    dur = media_duration(src)
    keep = keep_spans(spans, dur)
    if not keep:
        sys.exit("every second would be cut: check the edit list against the footage")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src,
           "-vf", f"select='{expr}',setpts=N/FRAME_RATE/TB",
           "-af", f"aselect='{expr}',asetpts=N/SR/TB",
           "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {r.stderr.strip()[-800:]}")
    return dur, media_duration(dst)


def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    keep_filler = "--keep-filler" in a
    no_repeats = "--no-repeats" in a
    a = [x for x in a if x not in ("--json", "--keep-filler", "--no-repeats")]
    floor, applying = 0.45, None
    if "--floor" in a:
        i = a.index("--floor")
        try:
            floor = float(a[i + 1])
            if floor <= 0:
                raise ValueError
        except (IndexError, ValueError):
            sys.exit("--floor is the shortest pause to cut, in seconds, e.g. --floor 0.45")
        a = a[:i] + a[i + 2:]
    if "--apply" in a:
        i = a.index("--apply")
        if len(a) < i + 3:
            sys.exit("--apply needs the video and where to write the cut: --apply in.mp4 out.mp4")
        applying = (a[i + 1], a[i + 2])
        a = a[:i] + a[i + 3:]
    if not a or not os.path.exists(a[0]):
        print(__doc__)
        sys.exit(1)
    cues = load(a[0])
    if not cues:
        print("no cues found: is this an srt, vtt or whisper json?")
        sys.exit(1)
    cuts = find_cuts(cues, floor, filler=not keep_filler, repeats=not no_repeats)
    spans = merge(cuts)
    dur = max(e for _, e, _ in cues)
    removed = sum(e - s for s, e in spans)
    result = {"source": a[0], "transcript_end": dur, "cuts": cuts,
              "merged_spans": [[round(s, 3), round(e, 3)] for s, e in spans],
              "removed": round(removed, 3), "out": round(dur - removed, 3)}
    if applying:
        before, after = apply(spans, *applying)
        result.update({"applied_to": applying[0], "wrote": applying[1],
                       "media_before": round(before, 3), "media_after": round(after, 3)})
    if as_json:
        print(json.dumps(result, indent=1))
        return
    print(f"\n  {a[0]}   transcript ends at {dur:.2f}s, {len(cues)} cues, dead-air floor {floor}s\n")
    for c in cuts:
        print(f"    {c['kind']:<7} {c['start']:8.2f} -> {c['end']:8.2f}   {c['end'] - c['start']:5.2f}s   {c['why']}")
    print(f"\n  {len(cuts)} cuts ({len(spans)} after merging overlaps), {removed:.2f}s removed, "
          f"{dur - removed:.2f}s left ({removed / dur * 100 if dur else 0:.1f}% shorter)")
    if applying:
        print(f"  Applied: {applying[0]} {result['media_before']:.2f}s -> {applying[1]} "
              f"{result['media_after']:.2f}s. Watch the cut points before publishing.")
    print()


if __name__ == "__main__":
    main()
