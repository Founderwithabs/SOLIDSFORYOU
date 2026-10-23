#!/usr/bin/env python3
"""Check and compute a competitor research folder, so no number is guessed.

Usage:
  python3 ledger.py init   FOLDER   create competitors.csv, ledger.csv, reviews.csv, parts/
  python3 ledger.py check  FOLDER   list every problem (main files and parts/)
  python3 ledger.py merge  FOLDER   move parts/ledger-*.csv and parts/reviews-*.csv
                                    into ledger.csv and reviews.csv
  python3 ledger.py sample FOLDER [--pct 20]   pick ledger rows to re-verify
  python3 ledger.py tables FOLDER   write FOLDER/tables.md with every table

Collectors working in parallel each write their own parts/ledger-<id>.csv and
parts/reviews-<id>.csv, so they never write to the same file at once; run
merge before verifying. Standard library only. File formats are described in
competitor-research.md.
"""
import argparse
import csv
import random
import statistics
import sys
from datetime import datetime
from pathlib import Path

COMPETITOR_COLS = ["id", "name", "brand", "channel", "url", "why_chosen"]
LEDGER_COLS = ["id", "competitor_id", "field", "value", "unit", "source_url",
               "captured_at", "method", "quote", "confidence", "verified"]
REVIEW_COLS = ["competitor_id", "source_url", "date", "rating", "themes",
               "sentiment", "excerpt"]

NUMERIC = {"price_selling", "price_mrp", "pack_qty", "rating", "ratings_count",
           "review_count", "bought_past_month", "bsr_rank", "image_count",
           "variant_count", "delivery_days", "website_price",
           "free_shipping_min", "social_followers", "active_ads"}
YES_NO = {"has_video", "has_a_plus", "cod"}
TEXT = {"title", "bullet", "claim", "badge", "material", "spec", "seller",
        "returns", "offer", "range_item", "website_url", "positioning",
        "ad_message", "trust_signal", "note"}
FIELDS = NUMERIC | YES_NO | TEXT
MISSING = {"not found", "blocked"}
METHODS = {"page", "json_ld", "screenshot", "search_result", "ad_library", "user"}
CONFIDENCE = {"high", "medium", "low"}
VERIFIED = {"", "yes", "no", "mismatch"}
KEY_FIELDS = ["price_selling", "rating", "ratings_count"]
CODEBOOK = {"quality", "material", "fit_size", "comfort", "durability",
            "colour_accuracy", "looks_as_pictured", "value_for_money",
            "delivery", "packaging", "customer_service", "returns_refunds",
            "smell", "stitching", "washing", "fake_or_wrong_item", "other"}
SENTIMENTS = {"praise", "complaint", "mixed"}
MAX_EXCERPT_WORDS = 25


# ---------- reading ----------------------------------------------------------

def read_csv(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def load(folder):
    """Main files plus any parts not yet merged."""
    folder = Path(folder)
    if not folder.is_dir():
        sys.exit(f"{folder} is not a folder (run init first)")
    ledger = read_csv(folder / "ledger.csv")
    reviews = read_csv(folder / "reviews.csv")
    for part in sorted((folder / "parts").glob("ledger-*.csv")):
        ledger += read_csv(part)
    for part in sorted((folder / "parts").glob("reviews-*.csv")):
        reviews += read_csv(part)
    return folder, read_csv(folder / "competitors.csv"), ledger, reviews


def append_rows(path, cols, rows):
    new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_time(value):
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.replace("Z", "")[:19], fmt)
        except ValueError:
            continue
    return None


# ---------- init -------------------------------------------------------------

def cmd_init(args):
    folder = Path(args.folder)
    (folder / "pages").mkdir(parents=True, exist_ok=True)
    (folder / "parts").mkdir(exist_ok=True)
    for name, cols in (("competitors.csv", COMPETITOR_COLS),
                       ("ledger.csv", LEDGER_COLS), ("reviews.csv", REVIEW_COLS)):
        path = folder / name
        if path.exists():
            print(f"kept existing {path}")
            continue
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(cols)
        print(f"created {path}")


# ---------- check ------------------------------------------------------------

def problems(folder, competitors, ledger, reviews):
    found = []
    ids = {c.get("id") for c in competitors}
    if not competitors:
        found.append("competitors.csv: no competitors yet")
    if "us" not in ids:
        found.append("competitors.csv: add our own product with id 'us'")
    for c in competitors:
        if not c.get("why_chosen") and c.get("id") != "us":
            found.append(f"competitors.csv {c.get('id')}: why_chosen is empty")

    seen = set()
    for n, r in enumerate(ledger, start=2):
        where = f"ledger.csv line {n} (id {r.get('id') or '?'})"
        if not r.get("id"):
            found.append(f"{where}: id is empty")
        elif r["id"] in seen:
            found.append(f"{where}: duplicate id")
        seen.add(r.get("id"))
        if r.get("competitor_id") not in ids:
            found.append(f"{where}: competitor_id '{r.get('competitor_id')}' is not in competitors.csv")
        field, value = r.get("field", ""), r.get("value", "")
        if field not in FIELDS:
            found.append(f"{where}: unknown field '{field}'")
        if not value:
            found.append(f"{where}: value is empty (use 'not found' or 'blocked')")
        elif value.lower() not in MISSING:
            if field in NUMERIC and to_number(value) is None:
                found.append(f"{where}: {field} must be a plain number, got '{value}'")
            if field in YES_NO and value.lower() not in {"yes", "no"}:
                found.append(f"{where}: {field} must be yes or no, got '{value}'")
            if field == "rating" and to_number(value) is not None and not 0 <= float(value) <= 5:
                found.append(f"{where}: rating must be between 0 and 5")
            if field in {"price_selling", "price_mrp", "website_price"} and not r.get("unit"):
                found.append(f"{where}: {field} needs a currency code in unit")
            if field == "pack_qty" and not r.get("unit"):
                found.append(f"{where}: pack_qty needs a unit (piece, g, ml...)")
        method = r.get("method", "")
        if method not in METHODS:
            found.append(f"{where}: method must be one of {', '.join(sorted(METHODS))}")
        if method != "user" and not r.get("source_url", "").startswith("http"):
            found.append(f"{where}: source_url missing or not a URL")
        if not parse_time(r.get("captured_at", "")):
            found.append(f"{where}: captured_at missing or not a date (YYYY-MM-DD HH:MM)")
        if r.get("confidence") not in CONFIDENCE:
            found.append(f"{where}: confidence must be high, medium or low")
        if r.get("verified", "") not in VERIFIED:
            found.append(f"{where}: verified must be blank, yes, no or mismatch")
        if field in {"title", "bullet", "claim", "positioning", "ad_message"} \
                and value.lower() not in MISSING and not r.get("quote"):
            found.append(f"{where}: {field} needs the exact text in quote")

    for c in competitors:
        cid = c.get("id")
        have = {r["field"] for r in ledger if r.get("competitor_id") == cid}
        for k in KEY_FIELDS:
            if k not in have:
                found.append(f"coverage {cid}: no {k} row (record it, or 'not found' / 'blocked')")

    for n, r in enumerate(reviews, start=2):
        where = f"reviews.csv line {n}"
        if r.get("competitor_id") not in ids:
            found.append(f"{where}: competitor_id '{r.get('competitor_id')}' is not in competitors.csv")
        themes = [t.strip() for t in r.get("themes", "").split(";") if t.strip()]
        if not themes:
            found.append(f"{where}: no themes")
        for t in themes:
            if t not in CODEBOOK:
                found.append(f"{where}: theme '{t}' is not in the codebook "
                             "(add it to the codebook in brief.md if 3+ reviews need it)")
        if r.get("sentiment") not in SENTIMENTS:
            found.append(f"{where}: sentiment must be praise, complaint or mixed")
        rating = to_number(r.get("rating"))
        if r.get("rating") and (rating is None or not 1 <= rating <= 5):
            found.append(f"{where}: rating must be 1 to 5")
        if len(r.get("excerpt", "").split()) > MAX_EXCERPT_WORDS:
            found.append(f"{where}: excerpt longer than {MAX_EXCERPT_WORDS} words")
    return found


def cmd_check(args):
    folder, competitors, ledger, reviews = load(args.folder)
    found = problems(folder, competitors, ledger, reviews)
    print(f"{len(competitors)} competitors, {len(ledger)} ledger rows, {len(reviews)} reviews")
    if found:
        print(f"{len(found)} problem(s):")
        for p in found:
            print(f"- {p}")
        sys.exit(1)
    print("No problems found.")


# ---------- merge ------------------------------------------------------------

def cmd_merge(args):
    folder = Path(args.folder)
    parts = folder / "parts"
    done = parts / "merged"
    done.mkdir(parents=True, exist_ok=True)
    existing = {r.get("id") for r in read_csv(folder / "ledger.csv")}
    moved = 0
    for kind, cols in (("ledger", LEDGER_COLS), ("reviews", REVIEW_COLS)):
        for part in sorted(parts.glob(f"{kind}-*.csv")):
            rows = read_csv(part)
            if kind == "ledger":
                dupes = [r.get("id") for r in rows if r.get("id") in existing]
                if dupes:
                    sys.exit(f"{part.name}: ids already in ledger.csv: {', '.join(dupes[:10])}. "
                             "Renumber them, then merge again.")
                existing.update(r.get("id") for r in rows)
            append_rows(folder / f"{kind}.csv", cols, rows)
            part.rename(done / part.name)
            moved += 1
            print(f"merged {part.name}: {len(rows)} rows")
    if not moved:
        print("no parts to merge")


# ---------- sample -----------------------------------------------------------

def cmd_sample(args):
    folder, _, ledger, _ = load(args.folder)
    rows = [r for r in ledger if r.get("value", "").lower() not in MISSING
            and r.get("verified") not in {"yes", "mismatch"}]
    must = [r for r in rows if r.get("field") in {"price_selling", "price_mrp",
                                                  "rating", "ratings_count",
                                                  "review_count"}]
    rest = [r for r in rows if r not in must]
    rng = random.Random(str(folder.resolve()))
    want = max(0, round(len(ledger) * args.pct / 100) - len(must))
    picked = must + rng.sample(rest, min(want, len(rest)))
    out = folder / "verify_sample.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "competitor_id", "field", "value", "source_url"])
        for r in picked:
            w.writerow([r.get(k, "") for k in ["id", "competitor_id", "field", "value", "source_url"]])
    print(f"{len(picked)} rows to verify ({len(must)} price/rating rows plus a random "
          f"sample), written to {out}")


# ---------- tables -----------------------------------------------------------

def best_rows(ledger):
    """Usable rows per (competitor, field): drop mismatches, prefer verified, then newest."""
    groups = {}
    for r in ledger:
        if r.get("verified") == "mismatch":
            continue
        groups.setdefault((r.get("competitor_id"), r.get("field")), []).append(r)
    for key, rows in groups.items():
        rows.sort(key=lambda r: (r.get("verified") == "yes",
                                 parse_time(r.get("captured_at", "")) or datetime.min),
                  reverse=True)
    return groups


def value(groups, cid, field):
    rows = groups.get((cid, field), [])
    return rows[0] if rows else None


def num(groups, cid, field):
    r = value(groups, cid, field)
    return to_number(r["value"]) if r else None


def show(groups, cid, field):
    r = value(groups, cid, field)
    if not r:
        return "—"
    return f"{r['value']} [{r['id']}]"


def fmt(x, digits=2):
    if x is None:
        return "—"
    if abs(x - round(x)) < 1e-9 and abs(x) >= 1:
        return f"{x:,.0f}"
    return f"{x:,.{digits}f}"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return out


def cmd_tables(args):
    folder, competitors, ledger, reviews = load(args.folder)
    found = problems(folder, competitors, ledger, reviews)
    groups = best_rows(ledger)
    cids = [c["id"] for c in competitors]
    names = {c["id"]: c.get("name") or c["id"] for c in competitors}
    stamps = [parse_time(r.get("captured_at", "")) for r in ledger]
    stamps = [s for s in stamps if s]
    out = ["# Competitor tables", "",
           "Generated by ledger.py. Numbers in [brackets] are ledger row ids; "
           "every value can be traced to its source there.", ""]
    if stamps:
        out.append(f"Data collected between {min(stamps):%Y-%m-%d %H:%M} and "
                   f"{max(stamps):%Y-%m-%d %H:%M}.")
    if found:
        out.append(f"**Warning:** `ledger.py check` reports {len(found)} problem(s). "
                   "Fix them before relying on these tables.")
    out.append("")

    # Price
    unit_prices, units = {}, {}
    rows = []
    for cid in cids:
        sp, mrp, qty = num(groups, cid, "price_selling"), num(groups, cid, "price_mrp"), num(groups, cid, "pack_qty")
        qty_row = value(groups, cid, "pack_qty")
        cur = (value(groups, cid, "price_selling") or {}).get("unit", "")
        disc = (1 - sp / mrp) * 100 if sp is not None and mrp else None
        unit_price = sp / qty if sp is not None and qty else None
        unit_prices[cid] = unit_price
        units[cid] = (qty_row or {}).get("unit", "").lower()
        rows.append([names[cid], f"{fmt(sp)} {cur}".strip(), fmt(mrp),
                     "—" if disc is None else f"{disc:.0f}%",
                     f"{fmt(qty)} {qty_row['unit'] if qty_row else ''}".strip(),
                     fmt(unit_price)])
    # Rank only products sold in the same unit as ours (or the most common unit).
    priced = [c for c in cids if unit_prices[c] is not None]
    common = units.get("us") if "us" in priced else (
        max({units[c] for c in priced}, key=lambda u: sum(units[c] == u for c in priced)) if priced else "")
    ranked = sorted([c for c in priced if units[c] == common], key=lambda c: unit_prices[c])
    rank = {c: i + 1 for i, c in enumerate(ranked)}
    for row, cid in zip(rows, cids):
        row.append(rank.get(cid, "different unit" if cid in priced else "—"))
    out += ["## Price", "", "Unit price = selling price ÷ pack quantity. Rank 1 is the cheapest per unit. "
            "Compare unit prices only between products with the same unit.", ""]
    out += table(["Product", "Selling price", "MRP", "Discount", "Pack", "Unit price", "Unit price rank"], rows)

    # Demand and trust
    rows = [[names[c], fmt(num(groups, c, "rating"), 1), fmt(num(groups, c, "ratings_count")),
             fmt(num(groups, c, "review_count")), fmt(num(groups, c, "bought_past_month")),
             show(groups, c, "bsr_rank")] for c in cids]
    out += ["", "## Demand and trust", ""]
    out += table(["Product", "Rating", "Ratings", "Reviews", "Bought past month", "Bestseller rank"], rows)

    # Listing strength
    rows = []
    for c in cids:
        title = value(groups, c, "title")
        bullet_rows = [r for r in ledger if r.get("competitor_id") == c and r.get("field") == "bullet"
                       and r.get("verified") != "mismatch"]
        bullets = (len([r for r in bullet_rows if r.get("value", "").lower() not in MISSING])
                   if bullet_rows else "—")
        badges = ", ".join(sorted({r["value"] for r in ledger if r.get("competitor_id") == c
                                   and r.get("field") == "badge" and r.get("value", "").lower() not in MISSING})) or "—"
        rows.append([names[c], fmt(num(groups, c, "image_count")), show(groups, c, "has_video"),
                     show(groups, c, "has_a_plus"), bullets,
                     len(title["value"]) if title and title["value"].lower() not in MISSING else "—",
                     badges])
    out += ["", "## Listing strength", ""]
    out += table(["Product", "Images", "Video", "A+ content", "Bullets", "Title length (characters)", "Badges"], rows)

    # Reviews
    out += ["", "## Review themes", ""]
    if not reviews:
        out.append("No coded reviews yet.")
    else:
        totals = {}
        for r in reviews:
            totals[r["competitor_id"]] = totals.get(r["competitor_id"], 0) + 1
        overall = {}
        for c in cids:
            mine = [r for r in reviews if r.get("competitor_id") == c]
            if not mine:
                continue
            counts = {}
            for r in mine:
                for t in {x.strip() for x in r.get("themes", "").split(";") if x.strip()}:
                    k = counts.setdefault(t, {"complaint": 0, "praise": 0, "mixed": 0})
                    k[r.get("sentiment", "mixed") if r.get("sentiment") in SENTIMENTS else "mixed"] += 1
                    if c != "us" and r.get("sentiment") in {"complaint", "mixed"}:
                        o = overall.setdefault(t, {"reviews": 0, "competitors": set()})
                        o["reviews"] += 1
                        o["competitors"].add(c)
            ratings = [to_number(r.get("rating")) for r in mine if to_number(r.get("rating"))]
            out += [f"### {names[c]}: {len(mine)} reviews coded"
                    + (f", average stars in sample {statistics.mean(ratings):.2f}" if ratings else ""), ""]
            trows = sorted(counts.items(), key=lambda kv: (kv[1]["complaint"], kv[1]["praise"]), reverse=True)
            out += table(["Theme", "Complaints", "Praise", "Mixed", "Share of reviews mentioning it"],
                         [[t, v["complaint"], v["praise"], v["mixed"],
                           f"{(v['complaint'] + v['praise'] + v['mixed']) / len(mine) * 100:.0f}%"]
                          for t, v in trows])
            out.append("")
        if overall:
            out += ["### Complaints across competitors (excluding us)", "",
                    "Themes many competitors' buyers complain about are the market's unsolved problems.", ""]
            orows = sorted(overall.items(), key=lambda kv: (len(kv[1]["competitors"]), kv[1]["reviews"]), reverse=True)
            out += table(["Theme", "Complaint or mixed reviews", "Competitors affected"],
                         [[t, v["reviews"], len(v["competitors"])] for t, v in orows])

    # Coverage
    check_fields = ["price_selling", "price_mrp", "pack_qty", "rating", "ratings_count",
                    "review_count", "image_count", "title", "claim", "website_url"]
    rows = []
    for c in cids:
        cells, have = [], 0
        for f in check_fields:
            r = value(groups, c, f)
            if not r:
                cells.append("missing")
            elif r["value"].lower() in MISSING:
                cells.append(r["value"])
            else:
                cells.append("yes")
                have += 1
        n_rev = len([r for r in reviews if r.get("competitor_id") == c])
        rows.append([names[c]] + cells + [n_rev, f"{have / len(check_fields) * 100:.0f}%"])
    out += ["", "## Coverage", ""]
    out += table(["Product"] + check_fields + ["Reviews coded", "Coverage"], rows)

    # One-on-one
    if "us" in cids:
        out += ["", "## One-on-one: us against each competitor", "",
                "Rows marked 'judge' need the reviewer's judgement, using the ledger rows cited.", ""]
        for c in [c for c in cids if c != "us"]:
            def win(field, higher_better=True):
                a, b = num(groups, "us", field), num(groups, c, field)
                if a is None or b is None:
                    return "unknown"
                if a == b:
                    return "tie"
                return "us" if (a > b) == higher_better else "them"
            up_us, up_them = unit_prices.get("us"), unit_prices.get(c)
            if units.get("us") != units.get(c):
                up_us = up_them = None
            price_win = ("unknown (different units)" if units.get("us") != units.get(c)
                         and unit_prices.get("us") is not None and unit_prices.get(c) is not None
                         else "unknown" if up_us is None or up_them is None
                         else "tie" if up_us == up_them
                         else "us" if up_us < up_them else "them")
            out += [f"### Us vs {names[c]}", ""]
            out += table(["Factor", "Us", names[c], "Who wins"], [
                ["Price per unit", fmt(unit_prices.get("us")), fmt(unit_prices.get(c)), price_win],
                ["Rating", show(groups, "us", "rating"), show(groups, c, "rating"), win("rating")],
                ["Ratings count", show(groups, "us", "ratings_count"), show(groups, c, "ratings_count"), win("ratings_count")],
                ["Bought past month", show(groups, "us", "bought_past_month"), show(groups, c, "bought_past_month"), win("bought_past_month")],
                ["Images", show(groups, "us", "image_count"), show(groups, c, "image_count"), win("image_count")],
                ["Main claim", show(groups, "us", "claim"), show(groups, c, "claim"), "judge"],
                ["Key spec", show(groups, "us", "spec"), show(groups, c, "spec"), "judge"],
                ["Trust signals", show(groups, "us", "badge"), show(groups, c, "badge"), "judge"],
                ["Returns", show(groups, "us", "returns"), show(groups, c, "returns"), "judge"],
            ])
            out.append("")

    path = folder / "tables.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {path}" + (f" ({len(found)} ledger problem(s): run check)" if found else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "check", "merge", "tables"):
        sub.add_parser(name).add_argument("folder")
    s = sub.add_parser("sample")
    s.add_argument("folder")
    s.add_argument("--pct", type=float, default=20)
    args = ap.parse_args()
    {"init": cmd_init, "check": cmd_check, "merge": cmd_merge, "sample": cmd_sample,
     "tables": cmd_tables}[args.cmd](args)


if __name__ == "__main__":
    main()
