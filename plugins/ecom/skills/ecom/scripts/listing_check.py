#!/usr/bin/env python3
"""Check listing text in code: lengths, repeats, keyword coverage, risky words.

Usage:
  python3 listing_check.py listing.json [--keywords keywords.txt]
        [--limits title=200,bullet=500,description=2000,search_terms=250]

listing.json: {"title": "...", "bullets": ["...", ...], "description": "...",
"search_terms": "..."} (any field may be missing). keywords.txt: one keyword
or phrase per line. Limits are the ones you confirmed for this marketplace
and category; the search_terms limit is checked in bytes (UTF-8), the others
in characters. Standard library only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

RISKY = [
    "best", "#1", "number one", "no. 1", "top rated", "top-rated", "bestseller", "best seller",
    "guarantee", "guaranteed", "100%", "cheapest", "lowest price", "free", "sale", "offer",
    "limited time", "hurry", "today only", "cure", "cures", "heal", "treat", "prevents",
    "antibacterial", "antimicrobial", "anti-bacterial", "eco-friendly", "eco friendly",
    "biodegradable", "non-toxic", "organic", "fda", "approved", "certified", "clinically",
    "doctor recommended", "dermatologist", "miracle", "amazing", "perfect", "unbeatable",
    "original", "genuine", "authentic", "replica", "compatible with",
]
STOP = {"a", "an", "and", "the", "for", "with", "of", "in", "on", "to", "by", "or", "is", "it",
        "your", "you", "our", "from", "at", "as", "be", "are", "this", "that", "&", "-"}


def words(text):
    return re.findall(r"[a-z0-9][a-z0-9'\-]*", text.lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("listing")
    ap.add_argument("--keywords")
    ap.add_argument("--limits", default="")
    args = ap.parse_args()
    try:
        listing = json.loads(Path(args.listing).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"{args.listing}: {e}")
    limits = {}
    for part in [p for p in args.limits.split(",") if p.strip()]:
        k, _, v = part.partition("=")
        limits[k.strip()] = int(v)

    fields = []
    if listing.get("title"):
        fields.append(("title", "title", listing["title"]))
    for i, b in enumerate(listing.get("bullets") or [], start=1):
        fields.append((f"bullet {i}", "bullet", b))
    if listing.get("description"):
        fields.append(("description", "description", listing["description"]))
    if listing.get("search_terms"):
        fields.append(("search terms", "search_terms", listing["search_terms"]))
    if not fields:
        sys.exit("no title, bullets, description or search_terms found")

    out = ["# Listing check", "", "| Field | Characters | Bytes | Limit | Status |", "|---|---|---|---|---|"]
    problems = 0
    for label, kind, text in fields:
        chars, nbytes = len(text), len(text.encode("utf-8"))
        limit = limits.get(kind)
        measure = nbytes if kind == "search_terms" else chars
        status = "—" if limit is None else ("ok" if measure <= limit else f"OVER by {measure - limit}")
        if limit is not None and measure > limit:
            problems += 1
        out.append(f"| {label} | {chars} | {nbytes} | {limit if limit is not None else 'not set'}"
                   f"{' bytes' if kind == 'search_terms' and limit else ''} | {status} |")

    visible = " ".join(t for _, k, t in fields if k != "search_terms")
    title_words = [w for w in words(listing.get("title", "")) if w not in STOP]
    repeats = sorted({w for w in title_words if title_words.count(w) > 1})
    out += ["", f"Words repeated in the title: {', '.join(repeats) if repeats else 'none'}."]
    if listing.get("search_terms"):
        st = words(listing["search_terms"])
        dup = sorted({w for w in st if w in set(words(visible)) and w not in STOP})
        out.append("Search-term words already in the title, bullets or description (usually wasted): "
                   + (", ".join(dup) if dup else "none") + ".")

    everything = " ".join(t for _, _, t in fields).lower()
    if args.keywords:
        kws = [k.strip() for k in Path(args.keywords).read_text(encoding="utf-8").splitlines() if k.strip()]
        covered = [k for k in kws if all(w in words(everything) for w in words(k))]
        missing = [k for k in kws if k not in covered]
        in_title = [k for k in covered if all(w in words(listing.get("title", "")) for w in words(k))]
        out += ["", f"Keywords covered: {len(covered)} of {len(kws)}.",
                f"- In the title: {', '.join(in_title) if in_title else 'none'}",
                f"- Missing everywhere: {', '.join(missing) if missing else 'none'}"]

    hits = []
    for term in RISKY:
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        for label, _, text in fields:
            if re.search(pattern, text.lower()):
                hits.append(f"'{term}' in {label}")
    out += ["", "Words to check against the marketplace's rules and your evidence: "
            + ("; ".join(hits) if hits else "none") + "."]
    out += ["", f"{problems} field(s) over their limit." if problems else "All fields within the limits given."]
    print("\n".join(out))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
