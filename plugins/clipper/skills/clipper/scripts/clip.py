#!/usr/bin/env python3
"""clip.py - find the best short clips in a long video's transcript, then cut them vertical,
captioned and loudness-matched, ready to post.

    python3 clip.py find transcript.json [--min 20] [--max 55] [--top 8] [--json]
    python3 clip.py render video.mp4 transcript.json --spans 12.4-48.9,95-131 --out-dir clips/
        [--frame blur|crop] [--x 0.5] [--hook "First clip's line|Second clip's line" --hook-seconds 2.5]
        [--no-captions] [--width 1080] [--height 1920] [--lufs -14]

find     ranks spans that open on a complete thought, contain a turn and end on a finished
         sentence. The score is a starting list for you to judge, not a verdict: read each
         span's first and last line before choosing.
render   cuts each span, reframes it to 9:16 (blur: the whole frame over a blurred fill, safe
         for any footage; crop: a 9:16 crop centred at --x, 0 = left edge, 1 = right edge),
         burns in word-by-word captions (from the transcriber's .json word timings; an .srt or
         .vtt is spread evenly across each cue), adds an optional hook line over the first
         seconds (one line for every clip, or one per span separated by |), and normalises loudness (default -14 LUFS, true peak -1.5 dBTP).

The transcript can be the transcriber skill's .json (best: word timings), an .srt or a .vtt.
Needs Python 3; render also needs ffmpeg with libass (most builds have it).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# A clip can't open on these: they lean on something said before it.
LEANS_BACK = re.compile(r"^(and|but|so|because|which|that|then|also|or|plus|anyway|as i said|like i said|"
                        r"he|she|they|it|this|that|these|those|him|her|them)\b", re.I)
TURN = re.compile(r"\b(but|actually|instead|the reason|turns out|the problem|the truth|nobody|except|"
                  r"until|the mistake|what (?:really|actually)|here'?s (?:why|how|what))\b", re.I)
HOOKY = re.compile(r"\b(you|your|why|how|what|never|stop|mistake|secret|nobody|most people|wrong|"
                   r"lost|losing|made|money|million|crore|lakh|first|only|biggest)\b", re.I)
FILLER = re.compile(r"\b(um+|uh+|er+|you know|i mean|kind of|sort of|basically|like)\b", re.I)
NUMBER = re.compile(r"(\d|₹|\$|%|\bone\b|\btwo\b|\bthree\b|\bten\b|\bhundred\b|\bthousand\b)", re.I)
ENDS = re.compile(r"[.!?…]['\")\]]?\s*$")


def parse_ts(s):
    s = s.strip().replace(",", ".")
    p = s.split(":")
    if len(p) == 3:
        return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
    if len(p) == 2:
        return int(p[0]) * 60 + float(p[1])
    return float(p[0])


def load(path):
    """Cues as dicts: start, end, text, words (list of (start, end, word), possibly empty)."""
    try:
        raw = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError as e:
        sys.exit(f"can't read {path}: {e.strerror}")
    if "\x00" in raw:
        sys.exit(f"{path} isn't a transcript (binary data): give the transcriber's .json, an .srt or a .vtt")
    cues = []
    if path.lower().endswith(".json"):
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            sys.exit(f"{path} isn't valid JSON; give the transcriber's .json, an .srt or a .vtt")
        segs = d.get("segments", []) if isinstance(d, dict) else d
        for s in segs if isinstance(segs, list) else []:
            try:
                a, b = float(s["start"]), float(s["end"])
            except (TypeError, KeyError, ValueError):
                continue  # a segment without times can't be placed
            words = []
            for w in s.get("words") or [] if isinstance(s, dict) else []:
                try:
                    words.append((float(w["start"]), float(w["end"]), str(w["word"]).strip()))
                except (TypeError, KeyError, ValueError):
                    continue
            text = str(s.get("text") or " ".join(w[2] for w in words)).strip()
            if text and b > a >= 0:
                cues.append({"start": a, "end": b, "text": text, "words": [w for w in words if w[2]]})
        return sorted(cues, key=lambda c: c["start"])
    cur = None
    for line in raw.splitlines():
        m = re.match(r"\s*(\d[\d:.,]*)\s*-->\s*(\d[\d:.,]*)", line)
        if m:
            try:
                cur = {"start": parse_ts(m.group(1)), "end": parse_ts(m.group(2)), "text": [], "words": []}
            except ValueError:
                cur = None  # an unreadable timestamp: skip that cue
                continue
            cues.append(cur)
        elif cur is not None and line.strip() and not line.strip().isdigit() \
                and not line.startswith(("WEBVTT", "NOTE")):
            cur["text"].append(re.sub(r"<[^>]+>", "", line.strip()))
    out = [dict(c, text=" ".join(c["text"])) for c in cues if c["text"] and c["end"] > c["start"] >= 0]
    return sorted(out, key=lambda c: c["start"])


def score(span):
    """0-100 and its parts, for a list of consecutive cues."""
    first, last = span[0]["text"], span[-1]["text"]
    text = " ".join(c["text"] for c in span)
    dur = span[-1]["end"] - span[0]["start"]
    words = len(text.split())
    pace = words / dur if dur else 0
    parts = {
        "opens_clean": 0 if LEANS_BACK.match(first) else 20,
        "hook": min(25, 8 * len(HOOKY.findall(first)) + (9 if NUMBER.search(first) else 0)),
        "turn": 20 if TURN.search(text) else 0,
        "ends_clean": 15 if ENDS.search(last) else 0,
        "pace": 10 if 1.8 <= pace <= 3.6 else 4 if 1.2 <= pace <= 4.2 else 0,
        "no_filler": max(0, 10 - 2 * len(FILLER.findall(text))),
    }
    return sum(parts.values()), parts, round(pace, 2)


def find(cues, lo, hi, top):
    cands = []
    for i in range(len(cues)):
        for j in range(i, len(cues)):
            dur = cues[j]["end"] - cues[i]["start"]
            if dur > hi:
                break
            if dur >= lo:
                total, parts, pace = score(cues[i:j + 1])
                cands.append((total, -dur, i, j, parts, pace))
    cands.sort(reverse=True)
    picked, used = [], []
    for total, ndur, i, j, parts, pace in cands:
        a, b = cues[i]["start"], cues[j]["end"]
        if any(a < y and x < b for x, y in used):
            continue  # overlaps a better clip
        used.append((a, b))
        picked.append({"start": round(a, 2), "end": round(b, 2), "duration": round(-ndur, 1),
                       "score": total, "parts": parts, "words_per_s": pace,
                       "first_line": cues[i]["text"], "last_line": cues[j]["text"]})
        if len(picked) == top:
            break
    return picked


def ass_time(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass_text(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def caption_chunks(cues, a, b, max_words=3):
    """(start, end, text) chunks of up to max_words, in clip time."""
    out = []
    for c in cues:
        if c["end"] <= a or c["start"] >= b:
            continue
        words = c["words"]
        if not words:  # no word timings: spread the cue's words evenly
            ws = c["text"].split()
            step = (c["end"] - c["start"]) / max(1, len(ws))
            words = [(c["start"] + k * step, c["start"] + (k + 1) * step, w) for k, w in enumerate(ws)]
        words = [w for w in words if a <= w[0] < b]
        for k in range(0, len(words), max_words):
            g = words[k:k + max_words]
            out.append((g[0][0] - a, min(g[-1][1], b) - a, " ".join(w[2] for w in g)))
    for k in range(len(out) - 1):  # hold each chunk until the next one starts
        s, _, t = out[k]
        out[k] = (s, out[k + 1][0], t)
    return [(s, max(e, s + 0.2), t) for s, e, t in out]


def write_ass(path, chunks, hook, hook_s, w, h):
    big = round(h * 0.045)
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
             "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
             f"Style: Cap,Arial,{big},&H00FFFFFF,&H00000000,&H64000000,1,1,{round(big / 9)},0,2,60,60,{round(h * 0.28)}",
             f"Style: Hook,Arial,{round(big * 0.95)},&H00000000,&H00FFFFFF,&H00FFFFFF,1,3,{round(big / 4)},0,8,70,70,{round(h * 0.12)}",
             "", "[Events]", "Format: Layer, Start, End, Style, Text"]
    if hook:
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(hook_s)},Hook,{ass_text(hook)}")
    for s, e, t in chunks:
        lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,{ass_text(t)}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout or "{}")
        st = d["streams"][0]
        return int(st["width"]), int(st["height"]), float(d["format"]["duration"])
    except (KeyError, IndexError, ValueError, TypeError):
        sys.exit(f"{path} has no video stream ffmpeg can read: is it a video file?")


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return bool(r.stdout.strip())


def render(video, cues, spans, out_dir, frame, x, hooks, hook_s, captions, w, h, lufs, say=print):
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("render needs ffmpeg: install it (Mac: brew install ffmpeg; Windows: winget install "
                 "ffmpeg; Linux: apt install ffmpeg)")
    if not os.path.isfile(video):
        sys.exit(f"not a file: {video}")
    video = os.path.abspath(video)
    vw, vh, vdur = probe(video)
    audio = has_audio(video)
    os.makedirs(out_dir, exist_ok=True)
    out_dir = os.path.abspath(out_dir)
    made = []
    for n, (a, b) in enumerate(spans, 1):
        b = min(b, vdur)
        if b - a < 1:
            say(f"  skipped {a}-{b}: shorter than a second inside a {vdur:.1f}s video")
            continue
        if frame == "crop":
            cw = min(vw, round(vh * w / h / 2) * 2)
            left = max(0, min(vw - cw, round((vw - cw) * x)))
            vf = f"crop={cw}:{vh}:{left}:0,scale={w}:{h}"
        else:
            vf = (f"split[bg][fg];[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                  f"gblur=sigma=30,eq=brightness=-0.08[b];[fg]scale={w}:{h}:force_original_aspect_ratio=decrease[f];"
                  f"[b][f]overlay=(W-w)/2:(H-h)/2")
        vf += ",fps=30,setsar=1"
        hook = (hooks[n - 1] if len(hooks) > 1 else hooks[0]) if hooks else None
        with tempfile.TemporaryDirectory() as tmp:
            chunks = caption_chunks(cues, a, b) if captions else []
            if chunks or hook:
                write_ass(os.path.join(tmp, "c.ass"), chunks, hook, hook_s, w, h)
                vf += ",ass=c.ass"  # relative name: ffmpeg runs in tmp, so no path escaping
            out = os.path.join(out_dir, f"clip_{n:02d}.mp4")
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", video,
                   "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]"]
            if audio:
                cmd += ["-map", "0:a:0", "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-ar", "48000",
                        "-c:a", "aac", "-b:a", "192k"]
            cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", out]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)
        if r.returncode != 0:
            sys.exit(f"ffmpeg failed on clip {n}: {r.stderr.strip()[-800:]}")
        made.append({"clip": out, "start": round(a, 2), "end": round(b, 2), "duration": round(b - a, 2),
                     "hook": hook})
        say(f"  {out}   {a:.2f} -> {b:.2f}  ({b - a:.1f}s)")
    if not made:
        sys.exit("no clips made: check the spans against the video's length")
    return made


def take(a, flag, default=None, cast=str):
    if flag not in a:
        return default
    i = a.index(flag)
    try:
        v = cast(a[i + 1])
    except (IndexError, ValueError):
        sys.exit(f"{flag} needs a value; see the usage at the top of this script")
    del a[i:i + 2]
    return v


def finite(v, flag, lo=None, hi=None):
    if v != v or v in (float("inf"), float("-inf")) or (lo is not None and v < lo) or (hi is not None and v > hi):
        sys.exit(f"{flag} is out of range")
    return v


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("find", "render"):
        print(__doc__)
        sys.exit(1)
    cmd, a = a[0], a[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    if cmd == "find":
        lo = finite(take(a, "--min", 20.0, float), "--min", 1, 600)
        hi = finite(take(a, "--max", 55.0, float), "--max", 1, 600)
        top = take(a, "--top", 8, int)
        if hi <= lo or top < 1:
            sys.exit("--max must be above --min, and --top at least 1")
        if not a or not os.path.isfile(a[0]):
            sys.exit("give the transcript: the transcriber's .json, an .srt or a .vtt")
        cues = load(a[0])
        if not cues:
            sys.exit("no timed lines found: is this the transcriber's .json, an .srt or a .vtt?")
        picks = find(cues, lo, hi, top)
        if as_json:
            print(json.dumps(picks, ensure_ascii=False, indent=1))
            return
        if not picks:
            print(f"no span between {lo:g} and {hi:g} seconds: the transcript is shorter, or lower --min")
            return
        print(f"\n  {len(picks)} candidate clips ({lo:g} to {hi:g}s), best first. Read each before choosing.\n")
        for n, p in enumerate(picks, 1):
            weak = [k for k, v in p["parts"].items() if v == 0]
            print(f"  {n}. {p['start']:.2f}-{p['end']:.2f}  ({p['duration']}s)  score {p['score']}"
                  + (f"  missing: {', '.join(weak)}" if weak else ""))
            print(f"     opens: {p['first_line'][:110]}")
            print(f"     ends:  {p['last_line'][:110]}\n")
        print("  Render chosen ones with: clip.py render VIDEO TRANSCRIPT --spans "
              + ",".join(f"{p['start']}-{p['end']}" for p in picks[:3]) + " --out-dir clips/\n")
        return
    out_dir = take(a, "--out-dir", "clips")
    spans_s = take(a, "--spans")
    frame = take(a, "--frame", "blur")
    x = finite(take(a, "--x", 0.5, float), "--x", 0, 1)
    hook = take(a, "--hook")
    hook_s = finite(take(a, "--hook-seconds", 2.5, float), "--hook-seconds", 0.1, 30)
    w = take(a, "--width", 1080, int)
    h = take(a, "--height", 1920, int)
    lufs = finite(take(a, "--lufs", -14.0, float), "--lufs", -40, -5)
    captions = "--no-captions" not in a
    a = [v for v in a if v != "--no-captions"]
    if frame not in ("blur", "crop"):
        sys.exit("--frame is blur or crop")
    if not (16 <= w <= 4096 and 16 <= h <= 4096) or w % 2 or h % 2:
        sys.exit("--width and --height must be even numbers from 16 to 4096")
    if len(a) < 2 or not spans_s:
        sys.exit("render needs the video, the transcript and --spans, e.g. --spans 12.4-48.9,95-131")
    spans = []
    for part in spans_s.split(","):
        m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*", part)
        if not m or float(m.group(2)) <= float(m.group(1)):
            sys.exit(f"bad span {part!r}: write start-end in seconds, e.g. 12.4-48.9")
        spans.append((float(m.group(1)), float(m.group(2))))
    hooks = [s.strip() for s in hook.split("|")] if hook else []
    if len(hooks) > 1 and len(hooks) != len(spans):
        sys.exit(f"{len(hooks)} hooks for {len(spans)} spans: give one hook for all, or one per span separated by |")
    if not os.path.isfile(a[1]):
        sys.exit(f"not a file: {a[1]}")
    cues = load(a[1])
    made = render(a[0], cues, spans, out_dir, frame, x, hooks, hook_s, captions, w, h, lufs,
                  say=(lambda m: print(m, file=sys.stderr)) if as_json else print)
    if as_json:
        print(json.dumps(made, indent=1))
    else:
        print(f"\n  {len(made)} clip(s) in {out_dir}. Watch each one before posting.\n")


if __name__ == "__main__":
    main()
