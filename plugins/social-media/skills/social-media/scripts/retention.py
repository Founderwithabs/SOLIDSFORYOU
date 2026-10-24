#!/usr/bin/env python3
"""retention.py - read an audience-retention export and find where viewers leave.

Adapted from retention.py in youtube-agent-skill by Jake Schincariol (MIT; see
THIRD_PARTY_NOTICES.md). SOLIDS FOR YOU changes: reads positions and retention given as
fractions (0-1) as well as percentages or seconds, works for any platform's two-column export,
ignores rewatch peaks above 100% when finding the start, and prints the timestamps to inspect
with the motion-design-taste skill.

    python3 retention.py retention.csv --duration 600
    python3 retention.py retention.csv --duration 600 --transcript transcript.srt
    python3 retention.py retention.csv --json

YouTube: Studio > the video > Analytics > Engagement > audience retention chart > download >
"Audience retention". Other platforms: any export with a position column and a
percentage-still-watching column.

Three different problems, three different fixes:
  HOOK LEAK   what was lost in the first 30 seconds (or 10% of the video without --duration)
  CLIFFS      single steep drops after the opening: a moment people left at
  SLIDE       the steady bleed across the middle: pacing
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcript import load as load_cues  # noqa: E402


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        for r in csv.reader(fh):
            nums = []
            for c in r:
                c = c.strip().replace("%", "").replace(",", "")
                try:
                    nums.append(float(c))
                except ValueError:
                    pass
            if len(nums) >= 2:
                rows.append((nums[0], nums[1]))
    rows.sort()
    return rows


def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    opts = {}
    for flag in ("--duration", "--transcript"):
        if flag in a:
            i = a.index(flag)
            opts[flag] = a[i + 1]
            a = a[:i] + a[i + 2:]
    if not a or not os.path.exists(a[0]):
        print(__doc__)
        sys.exit(1)
    rows = load_csv(a[0])
    if len(rows) < 8:
        print("could not read at least 8 data points (position, % watching) from that file")
        sys.exit(1)
    xs, ys = [r[0] for r in rows], [r[1] for r in rows]
    if max(xs) <= 1.0:                       # position as a fraction of the video
        xs = [x * 100 for x in xs]
    if max(ys) <= 3.0:                       # retention as a fraction (rewatches can exceed 1)
        ys = [y * 100 for y in ys]
    dur = float(opts["--duration"]) if "--duration" in opts else None
    pct_axis = max(xs) <= 100.5 and (dur is None or dur > 100.5)

    def seconds(x):
        if not pct_axis:
            return x
        return x / 100.0 * dur if dur else None

    start = min(100.0, max(ys[:3]))         # a rewatch spike at 0 isn't the starting audience
    if pct_axis:
        cutoff = (30.0 / dur * 100) if dur else 10.0
    else:
        cutoff = 30.0
    hook_end = min((y for x, y in zip(xs, ys) if x <= cutoff), default=start)
    hook_leak = max(0.0, start - hook_end)

    drops = []
    for i in range(1, len(xs)):
        lost = ys[i - 1] - ys[i]
        span = (xs[i] - xs[i - 1]) or 1
        drops.append((lost / span, xs[i - 1], xs[i], lost))
    cliffs = []
    after_hook = [d for d in drops if d[1] >= cutoff]  # opening losses are the hook leak, not cliffs
    for rate, x0, x1, lost in sorted(after_hook, reverse=True)[:5]:
        if lost > 0.8:
            s = seconds(x0)
            cliffs.append({"from": round(x0, 2), "to": round(x1, 2), "lost": round(lost, 2),
                           "at_seconds": round(s, 1) if s is not None else None})
    mid = [rate for rate, x0, _, _ in drops if x0 > cutoff]
    slide = sum(mid) / len(mid) if mid else 0.0

    said = {}
    if opts.get("--transcript") and os.path.exists(opts["--transcript"]):
        cues = load_cues(opts["--transcript"])
        for c in cliffs:
            t = c["at_seconds"]
            if t is None:
                continue
            near = [q[2] for q in cues if q[0] <= t + 4 and q[1] >= t - 4]
            said[str(c["from"])] = " ".join(near)[:160]

    verdict = "healthy" if hook_leak < 25 else "leaking" if hook_leak < 40 else "severe"
    unit = "% of the video" if pct_axis else "s"
    out = {"points": len(xs), "start": round(start, 1), "end": round(ys[-1], 1),
           "hook_leak": round(hook_leak, 2), "hook_verdict": verdict, "cliffs": cliffs,
           "slide_per_unit": round(slide, 3), "slide_unit": unit, "said": said}
    if as_json:
        print(json.dumps(out, indent=1))
        return
    print(f"\n  {a[0]}   {len(xs)} points   {start:.1f}% -> {ys[-1]:.1f}%\n")
    print(f"  HOOK LEAK   {hook_leak:.1f} points lost in the opening   [{verdict}]")
    print("              under 25 is healthy for most lengths. Fix the first line before anything else.\n")
    print("  CLIFFS      the moments people actually left, after the opening")
    for c in cliffs:
        where = f"{c['at_seconds']:.0f}s" if c["at_seconds"] is not None else f"{c['from']}{unit}"
        line = f"    -{c['lost']:5.1f}  at {where:>8}"
        if said.get(str(c["from"])):
            line += f'   "{said[str(c["from"])]}"'
        print(line)
    if not cliffs:
        print("    none steeper than 0.8 points: the loss is all slide, not moments")
    print(f"\n  SLIDE       {slide:.3f} points lost per {'1' + unit if not pct_axis else '1' + unit} across the middle")
    print("              a steep, even slide is pacing: cut the middle, don't rewrite it.")
    times = [c["at_seconds"] for c in cliffs if c["at_seconds"] is not None]
    if times:
        print(f"\n  To see what was on screen: motion-design-taste's inspect_video.py --zoom "
              + ",".join(f"{max(0, t - 0.5):.1f}" for t in sorted(times)))
    print()


if __name__ == "__main__":
    main()
