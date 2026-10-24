#!/usr/bin/env python3
"""outliers.py - rank videos or posts by how far each beat its OWN channel's median.

Adapted from swipe.py in youtube-agent-skill by Jake Schincariol (MIT; see
THIRD_PARTY_NOTICES.md). SOLIDS FOR YOU changes: reads yt-dlp JSON directly, CSV files, and
several files at once; ranks short-form and long-form separately (--split-shorts), because their
view counts aren't comparable; works for any platform with a channel or account column.

    python3 outliers.py collected.json [more files...] [--min 2.0] [--split-shorts] [--json]

Inputs, any mix:
  - a list: [{"channel": "...", "title": "...", "views": 412000, "url": "...", "duration": 613}]
  - yt-dlp output: yt-dlp --flat-playlist -J "https://www.youtube.com/@channel/videos" > ch.json
    (one file per channel; uses entries' title, view_count, url and duration)
  - CSV with columns channel (or account), title (or caption), views, and optionally url, duration

Raw views rank channel size, not ideas. A 400k video on a channel whose median is 30k is the one to
study. Each channel needs at least 4 items or its median means nothing; thin channels are skipped
and listed. The formula label matches the TITLE against hooks.json: it judges the words, not why
the video worked. Collect only public listings; never log in or use anyone's account.
"""
import csv
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(HERE, "hooks.json"), encoding="utf-8"))["hooks"]
SHORT_MAX = 180  # seconds; YouTube Shorts can be up to 3 minutes (check the current limit)


def classify(title):
    scored = sorted(((sum(1 for p in f["match"] if re.search(p, title, re.I)), f["name"])
                     for f in FORMULAS), reverse=True)
    return scored[0][1] if scored and scored[0][0] else "Unclassified"


def num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def load(path):
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = []
            for r in csv.DictReader(f):
                r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
                rows.append({"channel": r.get("channel") or r.get("account") or "?",
                             "title": r.get("title") or r.get("caption") or "",
                             "views": num(r.get("views")), "url": r.get("url", ""),
                             "duration": num(r.get("duration"))})
            return rows
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict) and "entries" in data:          # yt-dlp channel or playlist dump
        channel = data.get("channel") or data.get("uploader") or data.get("title") or "?"
        rows = []
        for e in data["entries"] or []:
            if e is None:
                continue
            if "entries" in e:                                 # channel tabs nest playlists
                rows += [x for x in load_entries(e["entries"], channel)]
            else:
                rows += load_entries([e], channel)
        return rows
    if isinstance(data, dict):
        data = data.get("videos", [])
    return [{"channel": r.get("channel", "?"), "title": r.get("title", ""), "views": num(r.get("views")),
             "url": r.get("url", ""), "duration": num(r.get("duration"))} for r in data]


def load_entries(entries, channel):
    out = []
    for e in entries:
        if not e:
            continue
        out.append({"channel": e.get("channel") or e.get("uploader") or channel,
                    "title": e.get("title") or "", "views": num(e.get("view_count")),
                    "url": e.get("url") or e.get("webpage_url") or "", "duration": num(e.get("duration"))})
    return out


def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    split = "--split-shorts" in a
    a = [x for x in a if x not in ("--json", "--split-shorts")]
    lo = 1.5
    if "--min" in a:
        i = a.index("--min")
        lo = float(a[i + 1])
        a = a[:i] + a[i + 2:]
    files = [x for x in a if os.path.exists(x)]
    if not files:
        print(__doc__)
        sys.exit(1)
    rows = [r for f in files for r in load(f) if r["views"] is not None]
    groups = {}
    for r in rows:
        kind = ""
        if split:
            kind = "short" if (r["duration"] is not None and r["duration"] <= SHORT_MAX) else "long"
        groups.setdefault((r["channel"], kind), []).append(r)
    out, thin = [], []
    for (ch, kind), vids in groups.items():
        if len(vids) < 4:
            thin.append((ch + (f" ({kind})" if kind else ""), len(vids)))
            continue
        med = statistics.median(v["views"] for v in vids)
        for v in vids:
            m = v["views"] / med if med else 0
            out.append({"channel": ch, "format": kind or None, "title": v["title"], "views": int(v["views"]),
                        "median": int(med), "multiple": round(m, 2), "formula": classify(v["title"]),
                        "url": v["url"]})
    out = sorted([r for r in out if r["multiple"] >= lo], key=lambda r: -r["multiple"])
    if as_json:
        print(json.dumps({"outliers": out, "skipped_thin": thin}, indent=1))
        return
    print(f"\n  {len(rows)} items across {len({r['channel'] for r in rows})} channels, outliers at {lo}x or better"
          + (" (shorts and long-form ranked separately)" if split else "") + "\n")
    for r in out[:25]:
        tag = f"[{r['format']}] " if r["format"] else ""
        print(f"    {r['multiple']:5.2f}x  {r['views']:>10,} vs {r['median']:>9,} median  "
              f"{r['channel'][:20]:<20} {tag}{r['title'][:50]}")
        print(f"            {r['formula']}")
    if not out:
        print("    nothing cleared the threshold: collect more per channel or lower --min")
    if thin:
        print(f"\n  skipped (fewer than 4 items, so no real median): "
              + ", ".join(f"{c} ({n})" for c, n in thin[:8]))
    counts = {}
    for r in out:
        counts[r["formula"]] = counts.get(r["formula"], 0) + 1
    if counts:
        print("\n  title formulas among the outliers (a label for the words, not a cause)")
        for f, n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {n:2d}x  {f}")
    print()


if __name__ == "__main__":
    main()
