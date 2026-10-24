#!/usr/bin/env python3
"""Store operations numbers, in code: ads, returns and stock.

Usage:
  python3 ops.py ads REPORT.csv [--breakeven-acos 36.7] [--total-sales 250000] [--out ads.md]
  python3 ops.py returns RETURNS.csv [--orders 1200] [--out returns.md]
  python3 ops.py reorder --daily-sales 14 --lead-days 30 --on-hand 300
        [--inbound 0] [--safety-days 14] [--cover-days 60]

ads reads an advertising report (Amazon, Flipkart, Walmart and most others):
it finds the columns for campaign, spend, sales, orders, clicks and
impressions by name, then computes ACoS, ROAS, CPC, CTR and conversion per
row and in total, and flags rows above the break-even ACoS from economics.py.
returns reads a returns export and counts reasons. reorder works out the
reorder point and how much to order. Standard library only.
"""
import argparse
import csv
import io
import math
import sys
from pathlib import Path

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ADS_COLUMNS = {
    "campaign": ["campaign name", "campaign", "ad group name", "ad group", "keyword", "search term", "name"],
    "spend": ["spend", "cost", "ad spend", "total spend"],
    "sales": ["7 day total sales", "14 day total sales", "total sales", "sales", "attributed sales",
              "revenue", "ad sales"],
    "orders": ["7 day total orders (#)", "14 day total orders (#)", "total orders", "orders",
               "units sold", "conversions", "attributed orders"],
    "clicks": ["clicks"],
    "impressions": ["impressions", "views"],
}
RETURN_REASON = ["return reason", "reason", "customer comments", "return_reason"]
# Summary rows many exports end with; counting them would double every total.
TOTAL_ROWS = {"total", "totals", "grand total", "sum", "summary", "all campaigns"}


def number(value):
    v = (value or "").strip().replace(",", "")
    for sym in ("₹", "$", "€", "£", "%", "INR", "USD", "EUR", "GBP"):
        v = v.replace(sym, "")
    try:
        return float(v.strip())
    except ValueError:
        return None


def read_table(path):
    """Rows of a CSV or TSV export, however Excel or the platform saved it: UTF-8 or
    Windows (cp1252) text, separated by commas, semicolons or tabs."""
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        sys.exit(f"can't read {path}: {e.strerror}")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if "\x00" in text:
        sys.exit(f"{path} isn't a text table (CSV or TSV); export it again as CSV")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text, newline=""), dialect=dialect))


def read(path):
    rows = read_table(path)
    if not rows:
        sys.exit(f"{path} has no rows")
    return rows


def find_column(headers, names):
    low = {h.strip().lower(): h for h in headers if h}
    for n in names:
        if n in low:
            return low[n]
    for n in names:  # looser: header contains the name
        for k, h in low.items():
            if n in k:
                return h
    return None


def pct(a, b):
    return a / b * 100 if b else None


def f(x, suffix="", digits=2):
    return "n/a" if x is None else f"{x:,.{digits}f}{suffix}"


def write(text, out):
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


def cmd_ads(args):
    rows = read(args.report)
    cols = {k: find_column(rows[0].keys(), v) for k, v in ADS_COLUMNS.items()}
    if not cols["spend"] or not cols["sales"]:
        sys.exit(f"couldn't find spend and sales columns; headers are: {', '.join(rows[0].keys())}")
    groups, skipped = {}, []
    for r in rows:
        key = (r.get(cols["campaign"]) or "(all)").strip() if cols["campaign"] else "(all)"
        if key.lower().rstrip(":") in TOTAL_ROWS or key.lower().startswith("total "):
            skipped.append(key)
            continue
        g = groups.setdefault(key, {"spend": 0, "sales": 0, "orders": 0, "clicks": 0, "impressions": 0})
        for k in g:
            if cols[k]:
                g[k] += number(r.get(cols[k])) or 0
    total = {k: sum(g[k] for g in groups.values()) for k in ["spend", "sales", "orders", "clicks", "impressions"]}
    out = ["# Advertising report", "",
           "Columns used: " + ", ".join(f"{k} = '{v}'" for k, v in cols.items() if v) + ".",
           "ACoS = spend ÷ ad sales. ROAS = ad sales ÷ spend. CVR = orders ÷ clicks."]
    if skipped:
        out.append(f"Left out the report's own summary row ({', '.join(skipped)}), so nothing is counted twice.")
    out.append("")
    head = "| Campaign | Spend | Ad sales | ACoS | ROAS | Orders | CPC | CTR | CVR |" + (" Flag |" if args.breakeven_acos else "")
    out += [head, "|" + "---|" * (head.count("|") - 1)]
    ranked = sorted(groups.items(), key=lambda kv: kv[1]["spend"], reverse=True)
    for name, g in ranked + [("**Total**", total)]:
        acos = pct(g["spend"], g["sales"])
        flag = ""
        if args.breakeven_acos:
            if g["sales"] == 0 and g["spend"] > 0:
                flag = "spend with no sales"
            elif acos is not None and acos > args.breakeven_acos:
                flag = "above break-even"
        out.append(f"| {name} | {f(g['spend'])} | {f(g['sales'])} | {f(acos, '%', 1)} | "
                   f"{f(g['sales'] / g['spend'] if g['spend'] else None)} | {f(g['orders'], '', 0)} | "
                   f"{f(g['spend'] / g['clicks'] if g['clicks'] else None)} | "
                   f"{f(pct(g['clicks'], g['impressions']), '%')} | {f(pct(g['orders'], g['clicks']), '%')} |"
                   + (f" {flag} |" if args.breakeven_acos else ""))
    if args.total_sales:
        out += ["", f"TACoS (ad spend ÷ all sales {f(args.total_sales)}): "
                f"{f(pct(total['spend'], args.total_sales), '%', 1)}"]
    if args.breakeven_acos:
        losing = [n for n, g in groups.items()
                  if (g["sales"] == 0 and g["spend"] > 0) or (pct(g["spend"], g["sales"]) or 0) > args.breakeven_acos]
        waste = sum(groups[n]["spend"] for n in losing)
        out += ["", f"Break-even ACoS: {args.breakeven_acos:g}%. {len(losing)} of {len(groups)} rows are above "
                f"it or have spend with no sales, using {f(waste)} of {f(total['spend'])} spend "
                f"({f(pct(waste, total['spend']), '%', 1)})."]
    write("\n".join(out) + "\n", args.out)


def cmd_returns(args):
    rows = read(args.report)
    col = find_column(rows[0].keys(), RETURN_REASON)
    if not col:
        sys.exit(f"couldn't find a reason column; headers are: {', '.join(rows[0].keys())}")
    counts = {}
    for r in rows:
        reason = (r.get(col) or "").strip() or "(blank)"
        counts[reason] = counts.get(reason, 0) + 1
    n = len(rows)
    out = ["# Returns report", "", f"Returns: {n}. Reason column: '{col}'."]
    if args.orders:
        out.append(f"Return rate: {n} ÷ {args.orders:g} orders = {f(pct(n, args.orders), '%', 1)}.")
        if n > args.orders:
            out.append("More returns than orders: check that --orders covers the same period as this export.")
    out += ["", "| Reason | Returns | Share |", "|---|---|---|"]
    for reason, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        out.append(f"| {reason} | {c} | {f(pct(c, n), '%', 1)} |")
    write("\n".join(out) + "\n", args.out)


def cmd_reorder(args):
    for name in ("daily_sales", "lead_days", "on_hand", "inbound", "safety_days", "cover_days"):
        v = getattr(args, name)
        if not math.isfinite(v) or v < 0 or v > 1e9:
            sys.exit(f"--{name.replace('_', '-')} must be a plain number from 0 up, not {v:g}")
    d = args.daily_sales
    if d <= 0:
        sys.exit("--daily-sales must be above 0")
    stock = args.on_hand + args.inbound
    safety = d * args.safety_days
    reorder_point = d * args.lead_days + safety
    days_cover = stock / d
    order_now = stock <= reorder_point
    target = d * (args.lead_days + args.cover_days) + safety
    qty = max(0.0, target - stock)
    print("\n".join([
        "# Reorder",
        "",
        f"Daily sales {d:g}, lead time {args.lead_days:g} days, safety stock {args.safety_days:g} days, "
        f"cover after arrival {args.cover_days:g} days.",
        f"- Stock on hand plus inbound: {stock:,.0f} units = {days_cover:,.1f} days of cover",
        f"- Reorder point: {reorder_point:,.0f} units (lead time demand {d * args.lead_days:,.0f} + safety {safety:,.0f})",
        f"- Order now: {'yes' if order_now else 'not yet'}"
        + ("" if order_now else f" (about {(stock - reorder_point) / d:,.1f} days until the reorder point)"),
        f"- Suggested order quantity: {qty:,.0f} units (to reach {target:,.0f} units of cover)",
    ]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ads")
    a.add_argument("report")
    a.add_argument("--breakeven-acos", type=float, dest="breakeven_acos")
    a.add_argument("--total-sales", type=float, dest="total_sales")
    a.add_argument("--out")
    r = sub.add_parser("returns")
    r.add_argument("report")
    r.add_argument("--orders", type=float)
    r.add_argument("--out")
    o = sub.add_parser("reorder")
    o.add_argument("--daily-sales", type=float, required=True, dest="daily_sales")
    o.add_argument("--lead-days", type=float, required=True, dest="lead_days")
    o.add_argument("--on-hand", type=float, required=True, dest="on_hand")
    o.add_argument("--inbound", type=float, default=0)
    o.add_argument("--safety-days", type=float, default=14, dest="safety_days")
    o.add_argument("--cover-days", type=float, default=60, dest="cover_days")
    args = ap.parse_args()
    {"ads": cmd_ads, "returns": cmd_returns, "reorder": cmd_reorder}[args.cmd](args)


if __name__ == "__main__":
    main()
