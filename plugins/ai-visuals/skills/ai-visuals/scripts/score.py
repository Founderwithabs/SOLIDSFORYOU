#!/usr/bin/env python3
"""Total the AI Visuals scorecard in code and apply the ready rule.

Usage:
  python3 score.py 9 10 8 7 10 9 10 10
  (the eight criteria, 1 to 10 each, in the order of section 7 of ai-visuals.md)
"""
import sys

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

CRITERIA = [("Fit for the purpose", 20), ("Truthfulness", 15), ("Composition and hierarchy", 15),
            ("Free of AI artefacts", 15), ("Text", 10), ("Brand consistency", 10),
            ("Technical fit", 10), ("Platform rules and disclosure", 5)]
READY, MIN_EACH = 85, 7
MUST_BE_10 = {"Truthfulness", "Platform rules and disclosure"}


def main():
    try:
        scores = [float(x) for x in sys.argv[1:]]
    except ValueError:
        sys.exit("scores must be numbers")
    if len(scores) != len(CRITERIA):
        sys.exit(f"give {len(CRITERIA)} scores in this order: " + "; ".join(n for n, _ in CRITERIA))
    if any(not 1 <= s <= 10 for s in scores):
        sys.exit("each score must be between 1 and 10")
    total = sum(s * w for s, (_, w) in zip(scores, CRITERIA)) / 10
    problems = []
    if total < READY:
        problems.append(f"total below {READY}")
    for s, (n, _) in zip(scores, CRITERIA):
        if s < MIN_EACH:
            problems.append(f"{n} below {MIN_EACH}")
        if n in MUST_BE_10 and s != 10:
            problems.append(f"{n} must be 10")
    print("| Criterion | Weight | Score | Points |\n|---|---|---|---|")
    for s, (n, w) in zip(scores, CRITERIA):
        print(f"| {n} | {w} | {s:g} | {s * w / 10:g} |")
    print(f"\nTotal: {total:g}/100. " + ("Ready." if not problems else "Not ready: " + "; ".join(problems) + "."))


if __name__ == "__main__":
    main()
