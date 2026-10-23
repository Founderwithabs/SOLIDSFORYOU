#!/usr/bin/env python3
"""Analyse a social media post log so results are calculated, not guessed.

Usage:
  python3 content_log.py template > posts.csv
  python3 content_log.py analyze posts.csv [--by pillar,format,hook_type] [--out report.md]
  python3 content_log.py score 8 8 8 9 6 9 8 8 8 10
      (the ten pre-publish scorecard criteria, 1 to 10 each, in the skill's order)

posts.csv has one row per published post. Recognised columns (blank is fine):
  date, platform, format, pillar, funnel, hook_type, topic, url,
  views, reach, likes, comments, shares, saves, follows, clicks,
  watch_time_s, avg_watch_pct
Rates use views, or reach when views is blank. Every post is compared with
the median of the same platform, because accounts and platforms differ too
much for outside benchmarks to mean anything. A post's overall score is the
geometric mean of its relative rates, so one extreme rate can't dominate it.
Platforms with fewer than MIN_GROUP posts are reported but not ranked.
Standard library only.
"""
import argparse
import csv
import math
import statistics
import sys

COLUMNS = ["date", "platform", "format", "pillar", "funnel", "hook_type", "topic",
           "url", "views", "reach", "likes", "comments", "shares", "saves",
           "follows", "clicks", "watch_time_s", "avg_watch_pct"]
COUNTS = ["likes", "comments", "shares", "saves", "follows", "clicks"]
RATES = {
    "engagement": ["likes", "comments", "shares", "saves"],
    "share": ["shares"],
    "save": ["saves"],
    "follow": ["follows"],
    "click": ["clicks"],
}
# Pre-publish scorecard (section 7.1 of social-media.md): name, weight.
SCORECARD = [
    ("Hook stopping power", 20), ("Payoff and value", 15), ("Shareability", 10),
    ("Clarity", 10), ("Proof and specificity", 10), ("Native to the platform", 10),
    ("Brand voice", 10), ("Call to action fits the goal", 5), ("Human writing", 5),
    ("Compliance and honesty", 5),
]
SHIP_TOTAL, SHIP_MIN = 80, 6
MIN_GROUP = 3  # fewer posts than this are reported but not ranked
FLOOR = 0.05   # relative rates below this count as this in the overall score


def num(value):
    value = (value or "").strip().replace(",", "").rstrip("%")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path} has no posts")
    posts = []
    for i, row in enumerate(rows, start=2):
        row = {(k or "").strip().lower(): v for k, v in row.items()}
        audience = num(row.get("views")) or num(row.get("reach"))
        post = {"line": i, "row": row, "audience": audience,
                "platform": (row.get("platform") or "unknown").strip().lower()}
        for rate, parts in RATES.items():
            values = [num(row.get(p)) for p in parts]
            if audience and any(v is not None for v in values):
                post[rate] = sum(v or 0 for v in values) / audience
            else:
                post[rate] = None
        posts.append(post)
    return posts


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def pct(x):
    return "n/a" if x is None else f"{x * 100:.2f}%"


def ratio(x):
    return "n/a" if x is None else f"{x:.2f}x"


def relative_scores(posts):
    """Each post's rates divided by the median of its platform."""
    by_platform = {}
    for p in posts:
        by_platform.setdefault(p["platform"], []).append(p)
    medians = {}
    for platform, group in by_platform.items():
        medians[platform] = {r: median([p[r] for p in group]) for r in RATES}
        for p in group:
            rel = {}
            for r in RATES:
                m = medians[platform][r]
                rel[r] = p[r] / m if (p[r] is not None and m) else None
            p["rel"] = rel
            # Overall score: geometric mean of the relative rates that exist.
            vals = [max(v, FLOOR) for v in rel.values() if v is not None]
            p["score"] = (math.exp(sum(math.log(v) for v in vals) / len(vals))
                          if vals and len(group) >= MIN_GROUP else None)
    return by_platform, medians


def label(p):
    r = p["row"]
    bits = [r.get("date", ""), p["platform"], r.get("format", ""),
            (r.get("topic") or r.get("url") or "").strip()[:50]]
    return " · ".join(b for b in bits if b)


def analyze(args):
    posts = load(args.csv)
    by_platform, medians = relative_scores(posts)
    missing = [p["line"] for p in posts if not p["audience"]]
    out = ["# Social media performance report", "",
           f"Posts analysed: {len(posts)}. Rates are per view (or per reach "
           "when views are missing). Relative scores compare a post with the "
           "median post on the same platform: 1.00x is typical, 2.00x is twice "
           "as good.", ""]
    if missing:
        out += [f"Rows without views or reach (rates not calculated): lines "
                f"{', '.join(map(str, missing))}.", ""]

    out += ["## Account medians by platform", "",
            "| Platform | Posts | Median views or reach | Engagement | Share | Save | Follow | Click | Note |",
            "|---|---|---|---|---|---|---|---|---|"]
    for platform, group in sorted(by_platform.items()):
        m = medians[platform]
        mv = median([p["audience"] for p in group])
        out.append(f"| {platform} | {len(group)} | "
                   f"{'n/a' if mv is None else f'{mv:,.0f}'} | "
                   + " | ".join(pct(m[r]) for r in RATES) + " | "
                   + ("too few posts to rank" if len(group) < MIN_GROUP else "") + " |")

    scored = [p for p in posts if p.get("score") is not None]
    scored.sort(key=lambda p: p["score"], reverse=True)
    n = min(5, len(scored) // 2)
    if n == 0:
        out += ["", f"Not enough posts to rank yet: each platform needs at least "
                f"{MIN_GROUP} posts with views or reach."]
    for title, chosen in (("Top posts", scored[:n]),
                          ("Bottom posts", list(reversed(scored[-n:])))):
        if n == 0:
            break
        out += ["", f"## {title} (overall relative score)", "",
                "| Post | Score | Engagement | Share | Save | Follow | Click |",
                "|---|---|---|---|---|---|---|"]
        for p in chosen:
            out.append(f"| {label(p)} | {ratio(p['score'])} | "
                       + " | ".join(ratio(p['rel'][r]) for r in RATES) + " |")

    for field in [f.strip().lower() for f in args.by.split(",") if f.strip()] if scored else []:
        groups = {}
        for p in scored:
            key = (p["row"].get(field) or "").strip() or "(blank)"
            groups.setdefault(key, []).append(p)
        ranked = sorted(groups.items(),
                        key=lambda kv: median([p["score"] for p in kv[1]]),
                        reverse=True)
        out += ["", f"## By {field}", "",
                "| Value | Posts | Median score | Median share | Median save | Median follow | Note |",
                "|---|---|---|---|---|---|---|"]
        for key, group in ranked:
            note = "too few posts to judge" if len(group) < MIN_GROUP else ""
            out.append(f"| {key} | {len(group)} | "
                       f"{ratio(median([p['score'] for p in group]))} | "
                       f"{ratio(median([p['rel']['share'] for p in group]))} | "
                       f"{ratio(median([p['rel']['save'] for p in group]))} | "
                       f"{ratio(median([p['rel']['follow'] for p in group]))} | {note} |")

    text = "\n".join(out) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


def score(args):
    if len(args.scores) != len(SCORECARD):
        sys.exit(f"give {len(SCORECARD)} scores, one per criterion, in this order: "
                 + "; ".join(name for name, _ in SCORECARD))
    if any(not 1 <= v <= 10 for v in args.scores):
        sys.exit("each score must be between 1 and 10")
    total = sum(v * w for v, (_, w) in zip(args.scores, SCORECARD)) / 10
    problems = []
    if total < SHIP_TOTAL:
        problems.append(f"total below {SHIP_TOTAL}")
    low = [n for v, (n, _) in zip(args.scores, SCORECARD) if v < SHIP_MIN]
    if low:
        problems.append("below " + str(SHIP_MIN) + ": " + ", ".join(low))
    if args.scores[-1] != 10:
        problems.append("compliance and honesty must be 10")
    print("| Criterion | Weight | Score | Points |")
    print("|---|---|---|---|")
    for v, (n, w) in zip(args.scores, SCORECARD):
        print(f"| {n} | {w} | {v:g} | {v * w / 10:g} |")
    print(f"\nTotal: {total:g}/100. "
          + ("Ready to ship." if not problems else "Not ready: " + "; ".join(problems) + "."))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template", help="print an empty posts.csv header")
    a = sub.add_parser("analyze", help="analyse a posts.csv")
    a.add_argument("csv")
    a.add_argument("--by", default="pillar,format,hook_type",
                   help="comma-separated columns to group by")
    a.add_argument("--out")
    sc = sub.add_parser("score", help="total the pre-publish scorecard")
    sc.add_argument("scores", type=float, nargs="+")
    args = ap.parse_args()
    if args.cmd == "template":
        print(",".join(COLUMNS))
    elif args.cmd == "score":
        score(args)
    else:
        analyze(args)


if __name__ == "__main__":
    main()
