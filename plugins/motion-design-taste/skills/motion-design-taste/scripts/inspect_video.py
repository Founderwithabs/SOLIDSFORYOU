#!/usr/bin/env python3
"""Turn a video into evidence Claude can look at: specs, contact sheets,
cut timings, static stretches, loudness and frames at chosen moments.

Usage:
  python3 inspect_video.py VIDEO OUT_DIR [--at 3.9,17.0] [--zoom 64.5] [--every 1]

Writes to OUT_DIR:
  report.md          numbers and flags to read first
  sheet_NN.png       contact sheets (one frame every --every seconds)
  hook.png           first 3 seconds, 7 frames (0.0 to 3.0 s)
  at_<t>.png         full-size frames at each --at time
  zoom_<t>.png       every frame of the 1 s starting at each --zoom time
                     (to judge easing, overshoot and sync frame by frame)
Needs ffmpeg and ffprobe on PATH.
"""
import argparse
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

STATIC_THRESHOLD = 0.0002  # scene score below this counts as "nothing moving"
STATIC_MIN_SECONDS = 1.5
CUT_THRESHOLD = 0.3


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(video):
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", video])
    if out.returncode != 0:
        sys.exit(f"ffprobe failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


def frame_scores(video):
    """Return [(time, scene_score)] for every frame."""
    out = run(["ffmpeg", "-hide_banner", "-i", video, "-an", "-vf",
               "select='gte(scene,0)',metadata=print:file=-", "-f", "null", "-"])
    scores, t = [], None
    for line in out.stdout.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1))
        m = re.search(r"lavfi\.scene_score=([\d.]+)", line)
        if m and t is not None:
            scores.append((t, float(m.group(1))))
    return scores


def static_stretches(scores):
    runs, start, last = [], None, None
    for t, s in scores:
        if s < STATIC_THRESHOLD:
            if start is None:
                start = t
            last = t
        else:
            if start is not None and last - start >= STATIC_MIN_SECONDS:
                runs.append((start, last))
            start = None
    if start is not None and last - start >= STATIC_MIN_SECONDS:
        runs.append((start, last))
    return runs


def loudness(video):
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vn",
               "-af", "ebur128=peak=true", "-f", "null", "-"])
    text = out.stderr
    integrated = re.findall(r"I:\s+(-?[\d.]+) LUFS", text)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", text)  # ffmpeg labels true peak "dBFS"
    return (integrated[-1] if integrated else None, peak[-1] if peak else None)


def silences(video):
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vn",
               "-af", "silencedetect=n=-45dB:d=0.8", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out.stderr)]
    return list(zip(starts, ends))


def contact_sheets(video, out_dir, every, width):
    cols, rows = 5, 4
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf",
         f"fps=1/{every},scale={width}:-2,"
         "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=18:fontcolor=white:"
         "box=1:boxcolor=black@0.6,"
         f"tile={cols}x{rows}:padding=4:color=gray",
         "-fps_mode", "vfr", os.path.join(out_dir, "sheet_%02d.png")])


def hook_strip(video, out_dir):
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-t", "3.25",
         "-i", video, "-vf", "fps=2,scale=480:-2,"
         "drawtext=text='%{pts\\:hms}':x=6:y=6:fontsize=16:fontcolor=white:"
         "box=1:boxcolor=black@0.6,tile=7x1:padding=4:color=gray",
         "-frames:v", "1", os.path.join(out_dir, "hook.png")])


def frame_at(video, out_dir, t):
    path = os.path.join(out_dir, f"at_{t:.2f}.png")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t),
         "-i", video, "-frames:v", "1", path])
    return path


def zoom_strip(video, out_dir, t, fps):
    frames = max(1, round(fps))
    cols = 6
    rows = -(-frames // cols)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t),
         "-t", "1", "-i", video, "-vf",
         f"scale=320:-2,drawtext=text='%{{n}}':x=6:y=6:fontsize=16:"
         "fontcolor=white:box=1:boxcolor=black@0.6,"
         f"tile={cols}x{rows}:padding=4:color=gray",
         "-frames:v", "1", os.path.join(out_dir, f"zoom_{t:.2f}.png")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("--at", default="", help="comma-separated times in seconds")
    ap.add_argument("--zoom", default="",
                    help="comma-separated start times for 1 s frame-by-frame strips")
    ap.add_argument("--every", type=float, default=1.0,
                    help="seconds between contact-sheet frames")
    args = ap.parse_args()
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("this needs ffmpeg: install it (Mac: brew install ffmpeg; Windows: winget install ffmpeg; "
                 "Linux: sudo apt install ffmpeg), then run it again")
    if not os.path.isfile(args.video):
        sys.exit(f"not a file: {args.video}")
    if os.path.exists(args.out_dir) and not os.path.isdir(args.out_dir):
        sys.exit(f"{args.out_dir} is a file; give a folder for the frames and report")
    if not args.every > 0:
        sys.exit("--every is the seconds between contact-sheet frames, e.g. --every 1")
    try:
        at_times = [float(x) for x in args.at.split(",") if x.strip()]
        zoom_times = [float(x) for x in args.zoom.split(",") if x.strip()]
    except ValueError:
        sys.exit("--at and --zoom take seconds separated by commas, e.g. --at 3.9,17")
    os.makedirs(args.out_dir, exist_ok=True)

    info = probe(args.video)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        sys.exit("no video stream")
    try:
        duration = float(info["format"]["duration"])
    except (KeyError, ValueError):
        sys.exit(f"{args.video} has no length: give a video, not a still image")
    num, den = v["avg_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 0

    scores = frame_scores(args.video)
    cuts = [t for t, s in scores if s >= CUT_THRESHOLD]
    shots = [b - a_ for a_, b in zip([0.0] + cuts, cuts + [duration])]
    static = static_stretches(scores)

    contact_sheets(args.video, args.out_dir, args.every,
                   384 if int(v["width"]) >= int(v["height"]) else 216)
    hook_strip(args.video, args.out_dir)
    late = [t for t in at_times + zoom_times if not 0 <= t < duration]
    if late:
        print(f"skipping {', '.join(f'{t:g}' for t in late)} s: outside the {duration:.2f} s video", file=sys.stderr)
    at_times = [t for t in at_times if 0 <= t < duration]
    zoom_times = [t for t in zoom_times if 0 <= t < duration]
    for t in at_times:
        frame_at(args.video, args.out_dir, t)
    for t in zoom_times:
        zoom_strip(args.video, args.out_dir, t, fps)

    lines = ["# Video inspection report", "",
             f"- File: `{args.video}`",
             f"- Resolution: {v['width']}x{v['height']}, {fps:.2f} fps, "
             f"{duration:.2f} s, video codec {v['codec_name']}, "
             f"pixel format {v.get('pix_fmt')}",
             f"- Audio: {a['codec_name'] + ', ' + a.get('sample_rate', '?') + ' Hz' if a else 'NONE'}"]
    if a:
        integrated, peak = loudness(args.video)
        lines.append(f"- Loudness: {integrated} LUFS integrated, true peak {peak} dBTP")
        sil = silences(args.video)
        lines.append(f"- Silences over 0.8 s: "
                     + (", ".join(f"{s:.1f}-{e:.1f}s" for s, e in sil) or "none"))
    lines += ["", "## Cuts and pacing",
              f"- Hard cuts (scene score >= {CUT_THRESHOLD}): {len(cuts)}",
              "- Cut times: " + (", ".join(f"{t:.2f}" for t in cuts) or "none"),
              f"- Average shot length: {sum(shots) / len(shots):.2f} s; "
              f"longest: {max(shots):.2f} s",
              f"- Static stretches (nothing moving for {STATIC_MIN_SECONDS}+ s): "
              + (", ".join(f"{s:.1f}-{e:.1f}s" for s, e in static) or "none"),
              "", "## Images to look at",
              "- `hook.png`: first 3 seconds, one frame every 0.5 s",
              f"- `sheet_NN.png`: one frame every {args.every:g} s, timestamps burned in"]
    lines += [f"- `at_{t:.2f}.png`: full-size frame at {t:.2f} s" for t in at_times]
    lines += [f"- `zoom_{t:.2f}.png`: every frame from {t:.2f} s to {t + 1:.2f} s, "
              "frame numbers burned in" for t in zoom_times]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
