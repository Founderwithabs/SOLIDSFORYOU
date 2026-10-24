#!/usr/bin/env python3
"""Unit economics and pricing for any marketplace or own store, in code.

Usage:
  python3 economics.py template > fees/amazon-in.json
  python3 economics.py unit --fees FEES.json [FEES2.json ...] --price 999 --cost 280
        [--packaging 20] [--inbound 15] [--weight 350] [--tax-rate 12]
        [--products products.csv --sku SKU]
        [--sweep 799,899,999,1099] [--target-margin 25] [--out report.md]

A fee profile (JSON) describes one channel: its fees, tax treatment, returns
and ad cost, each with a source and the date it was checked. Profit is worked
out per order placed, so returns are counted properly:
  kept share k = 1 - return rate
  revenue      = k x price net of output tax
  fees         = k x sale fees + return rate x cost per return
  product cost = landed cost x (k + return rate x unsellable share)
  packaging    = per order shipped, ads = per order placed
Standard library only.
"""
import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

STALE_DAYS = 30

TEMPLATE = {
    "channel": "amazon.in",
    "currency": "INR",
    "source": "Where these numbers came from: settlement report month, or the rate card URL",
    "checked_at": "YYYY-MM-DD",
    "tax": {
        "mode": "inclusive",
        "rate_pct": 12,
        "on_fees_pct": 18,
        "fees_tax_recoverable": True,
        "note": "inclusive: the listed price includes GST/VAT. exclusive: tax is added on top (US-style sales tax). rate_pct is the product's tax rate; on_fees_pct is tax charged on marketplace fees; recoverable means you claim it back as input credit.",
    },
    "fees": [
        {"name": "referral", "type": "percent_tiers", "of": "price",
         "tiers": [{"up_to": 300, "value": 5}, {"up_to": 1000, "value": 12}, {"up_to": None, "value": 17}],
         "note": "EXAMPLE VALUES ONLY: replace every number with your own."},
        {"name": "closing", "type": "fixed_tiers", "of": "price",
         "tiers": [{"up_to": 300, "value": 10}, {"up_to": 1000, "value": 25}, {"up_to": None, "value": 50}]},
        {"name": "shipping", "type": "weight_tiers",
         "tiers": [{"up_to_g": 500, "value": 50}, {"up_to_g": 1000, "value": 70}, {"up_to_g": None, "value": 100}]},
        {"name": "payment", "type": "percent", "value": 0, "of": "price"},
        {"name": "other_fixed", "type": "fixed", "value": 0},
    ],
    "returns": {"rate_pct": 8, "cost_per_return": 100, "unsellable_pct": 20,
                "note": "cost_per_return: reverse shipping plus fees not refunded on a return"},
    "ads": {"tacos_pct": 10, "cost_per_order": None,
            "note": "Use tacos_pct (ad spend as % of sales) or cost_per_order, not both"},
}


# ---------- fee profile ------------------------------------------------------

def load_profile(path):
    try:
        p = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"{path}: {e}")
    warnings = []
    for key in ("channel", "currency", "source", "checked_at", "fees"):
        if key not in p:
            sys.exit(f"{path}: missing '{key}'")
    try:
        checked = datetime.strptime(p["checked_at"], "%Y-%m-%d").date()
        age = (date.today() - checked).days
        if age > STALE_DAYS:
            warnings.append(f"{p['channel']}: fees were checked {age} days ago; re-check them")
    except ValueError:
        warnings.append(f"{p['channel']}: checked_at is not a date, so the fees are unverified")
    if "EXAMPLE" in json.dumps(p) or "YYYY" in p["checked_at"]:
        warnings.append(f"{p['channel']}: still contains template example values")
    problems = profile_problems(p)
    if problems:
        sys.exit(f"{path}: " + "; ".join(problems))
    ads = p.get("ads") or {}
    if ads.get("cost_per_order") is not None and ads.get("tacos_pct"):
        warnings.append(f"{p['channel']}: ads has both tacos_pct and cost_per_order; using cost_per_order")
    return p, warnings


def profile_problems(p):
    """Everything in a fee profile that would make the numbers wrong, said plainly."""
    out = []

    def number(where, v, lo=None, hi=None, hi_open=False):
        try:
            x = float(v)
        except (TypeError, ValueError):
            out.append(f"{where} must be a number, not {v!r}")
            return
        if x != x or (lo is not None and x < lo) or (hi is not None and (x >= hi if hi_open else x > hi)):
            rng = f"from {lo:g} to {'under ' if hi_open else ''}{hi:g}" if hi is not None else f"{lo:g} or more"
            out.append(f"{where} must be {rng}, not {v!r}")

    if not isinstance(p.get("fees"), list) or not all(isinstance(f, dict) for f in p["fees"]):
        return ['"fees" must be a list of fees, each like {"name": ..., "type": ..., "value": ...}']
    tax = p.get("tax") or {}
    if not isinstance(tax, dict):
        return ['"tax" must be an object']
    if tax.get("mode", "inclusive") not in ("inclusive", "exclusive"):
        out.append(f"tax mode must be \"inclusive\" or \"exclusive\", not {tax.get('mode')!r}")
    for key in ("rate_pct", "on_fees_pct"):
        if key in tax:
            number(f"tax {key}", tax[key], 0, 100)
    for fee in p["fees"]:
        name, kind = fee.get("name") or "(no name)", fee.get("type")
        if kind not in {"percent", "fixed", "percent_tiers", "fixed_tiers", "weight_tiers"}:
            out.append(f"fee '{name}' has unknown type '{kind}'")
        elif kind in ("percent", "fixed"):
            number(f"fee '{name}' value", fee.get("value"), 0, 100 if kind == "percent" else None)
        else:
            tiers = fee.get("tiers")
            if not isinstance(tiers, list) or not tiers or not all(isinstance(t, dict) for t in tiers):
                out.append(f"fee '{name}' needs a non-empty list of tiers")
                continue
            for t in tiers:
                number(f"fee '{name}' tier value", t.get("value"), 0, 100 if kind == "percent_tiers" else None)
    ret = p.get("returns") or {}
    if not isinstance(ret, dict):
        return out + ['"returns" must be an object']
    if "rate_pct" in ret and ret["rate_pct"] is not None:
        number("returns rate_pct", ret["rate_pct"], 0, 100, hi_open=True)
    if "unsellable_pct" in ret and ret["unsellable_pct"] is not None:
        number("returns unsellable_pct", ret["unsellable_pct"], 0, 100)
    if "cost_per_return" in ret and ret["cost_per_return"] is not None:
        number("returns cost_per_return", ret["cost_per_return"], 0)
    ads = p.get("ads") or {}
    if not isinstance(ads, dict):
        return out + ['"ads" must be an object']
    if ads.get("tacos_pct") is not None:
        number("ads tacos_pct", ads["tacos_pct"], 0, 100)
    if ads.get("cost_per_order") is not None:
        number("ads cost_per_order", ads["cost_per_order"], 0)
    return out


def tier_value(tiers, x, key="up_to"):
    for t in tiers:
        limit = t.get(key)
        if limit is None or x <= limit:
            return float(t["value"])
    return float(tiers[-1]["value"])


def fee_amount(fee, price, net_price, weight_g):
    base = net_price if fee.get("of") == "price_ex_tax" else price
    kind = fee["type"]
    if kind == "percent":
        return base * float(fee["value"]) / 100
    if kind == "fixed":
        return float(fee["value"])
    if kind == "percent_tiers":
        return base * tier_value(fee["tiers"], price) / 100
    if kind == "fixed_tiers":
        return tier_value(fee["tiers"], price)
    if kind == "weight_tiers":
        if weight_g is None:
            raise ValueError(f"fee '{fee['name']}' depends on weight: pass --weight")
        return tier_value(fee["tiers"], weight_g, key="up_to_g")
    raise ValueError(kind)


# ---------- the model --------------------------------------------------------

def unit(profile, price, cost, packaging=0.0, inbound=0.0, weight_g=None, tax_rate=None):
    tax = profile.get("tax", {})
    mode = tax.get("mode", "inclusive")
    rate = float(tax_rate if tax_rate is not None else tax.get("rate_pct", 0))
    if mode == "inclusive":
        output_tax = price * rate / (100 + rate)
        net_price = price - output_tax
    else:
        output_tax = price * rate / 100
        net_price = price
    sale_fees = {f["name"]: fee_amount(f, price, net_price, weight_g) for f in profile["fees"]}
    fee_total = sum(sale_fees.values())
    fee_tax = fee_total * float(tax.get("on_fees_pct", 0)) / 100
    fee_tax_cost = 0.0 if tax.get("fees_tax_recoverable", True) else fee_tax

    ret = profile.get("returns", {}) or {}
    r = float(ret.get("rate_pct", 0) or 0) / 100
    k = 1 - r
    landed = cost + inbound
    ads = profile.get("ads", {}) or {}
    if ads.get("cost_per_order") is not None:
        ad_cost = float(ads["cost_per_order"])
    else:
        ad_cost = price * float(ads.get("tacos_pct", 0) or 0) / 100 * k

    lines = [
        ("Revenue after tax (kept orders)", k * net_price),
        ("Marketplace fees", -k * (fee_total + fee_tax_cost)),
        ("Return costs", -r * float(ret.get("cost_per_return", 0) or 0)),
        ("Product cost incl. inbound", -landed * (k + r * float(ret.get("unsellable_pct", 0) or 0) / 100)),
        ("Packaging", -packaging),
        ("Advertising", -ad_cost),
    ]
    profit = sum(v for _, v in lines)
    revenue = k * net_price
    before_ads = profit + ad_cost
    return {
        "price": price, "net_price": net_price, "output_tax": output_tax,
        "fees": sale_fees, "fee_total": fee_total, "fee_tax": fee_tax,
        "fee_tax_cost": fee_tax_cost, "lines": lines, "profit": profit,
        "margin_pct": profit / revenue * 100 if revenue else None,
        "roi_pct": profit / landed * 100 if landed else None,
        "breakeven_tacos_pct": before_ads / (price * k) * 100 if price and k else None,
    }


def solve_price(profile, cost, args, target_margin=None):
    """Lowest price (to 0.01) with profit >= 0, or margin >= target. Scans, so tiers are handled."""
    def ok(p):
        u = unit(profile, p, cost, args.packaging, args.inbound, args.weight, args.tax_rate)
        if target_margin is None:
            return u["profit"] >= 0
        return u["margin_pct"] is not None and u["margin_pct"] >= target_margin
    hi = max(cost, 1) * 50
    step = max(cost, 1) / 200
    p = step
    while p <= hi:
        if ok(p):
            lo = p - step
            for _ in range(60):  # refine within the step
                mid = (lo + p) / 2
                if ok(mid):
                    p = mid
                else:
                    lo = mid
            return round(p + 0.005, 2)
        p += step
    return None


# ---------- output -----------------------------------------------------------

def money(x, cur):
    return f"{x:,.2f} {cur}"


def product_from_csv(path, sku):
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        sys.exit(f"can't read {path}: {e.strerror}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")  # Excel on Windows
    for row in csv.DictReader(text.splitlines()):
        if (row.get("sku") or "").strip() == sku:
            return row
    sys.exit(f"{path}: no row with sku '{sku}'")


def cmd_unit(args):
    if args.products:
        row = product_from_csv(args.products, args.sku)
        def pick(attr, col):
            if getattr(args, attr) is None and (row.get(col) or "").strip():
                try:
                    setattr(args, attr, float(row[col]))
                except ValueError:
                    sys.exit(f"{args.products}: {col} for '{args.sku}' must be a number, not {row[col]!r}")
        for attr, col in (("price", "price"), ("cost", "cost"), ("packaging", "packaging_cost"),
                          ("inbound", "inbound_cost"), ("weight", "weight_g"), ("tax_rate", "tax_rate_pct")):
            pick(attr, col)
    if args.price is None or args.cost is None:
        sys.exit("give --price and --cost (or --products and --sku)")
    if not args.price > 0:
        sys.exit("--price must be above 0")
    for name in ("cost", "packaging", "inbound", "weight", "tax_rate"):
        v = getattr(args, name)
        if v is not None and not v >= 0:
            sys.exit(f"--{name.replace('_', '-')} can't be negative")
    if args.target_margin is not None and not 0 <= args.target_margin < 100:
        sys.exit("--target-margin is a percentage of revenue, from 0 to under 100")
    if args.sweep:
        try:
            sweep = [float(x) for x in args.sweep.split(",") if x.strip()]
        except ValueError:
            sys.exit("--sweep takes prices separated by commas, e.g. --sweep 799,899,999")
        if not sweep or min(sweep) <= 0:
            sys.exit("--sweep prices must all be above 0")
    args.packaging = args.packaging or 0.0
    args.inbound = args.inbound or 0.0

    out = ["# Unit economics", "",
           f"Inputs: price {args.price:g}, product cost {args.cost:g}, packaging {args.packaging:g}, "
           f"inbound {args.inbound:g}"
           + (f", weight {args.weight:g} g" if args.weight is not None else "")
           + (f", tax rate {args.tax_rate:g}%" if args.tax_rate is not None else "") + ".",
           "All figures are per order placed, so returns are included. Generated by economics.py.", ""]
    summary = []
    for path in args.fees:
        profile, warnings = load_profile(path)
        cur = profile["currency"]
        try:
            u = unit(profile, args.price, args.cost, args.packaging, args.inbound, args.weight, args.tax_rate)
        except ValueError as e:
            sys.exit(f"{path}: {e}")
        out += [f"## {profile['channel']}", "",
                f"Fee source: {profile['source']} (checked {profile['checked_at']})."]
        out += [f"**Warning:** {w}." for w in warnings]
        out += ["", "| Line | Amount |", "|---|---|"]
        out += [f"| {name} | {money(v, cur)} |" for name, v in u["lines"]]
        out += [f"| **Profit per order** | **{money(u['profit'], cur)}** |", ""]
        fee_rows = ", ".join(f"{n} {money(v, cur)}" for n, v in u["fees"].items())
        out += [f"- Fees per sale: {fee_rows} (total {money(u['fee_total'], cur)}; tax on fees "
                f"{money(u['fee_tax'], cur)}, "
                + ("recoverable, so not a cost)" if not u["fee_tax_cost"] else "counted as a cost)"),
                f"- Output tax inside the price: {money(u['output_tax'], cur)}",
                f"- Margin on revenue: {u['margin_pct']:.1f}%" if u["margin_pct"] is not None else "- Margin: n/a",
                f"- Return on product cost: {u['roi_pct']:.1f}%" if u["roi_pct"] is not None else "- ROI: n/a",
                f"- Break-even ad spend (TACoS): {u['breakeven_tacos_pct']:.1f}% of sales"
                if u["breakeven_tacos_pct"] is not None else ""]
        be = solve_price(profile, args.cost, args)
        out.append(f"- Break-even price: {money(be, cur)}" if be else "- Break-even price: none found")
        if args.target_margin is not None:
            tp = solve_price(profile, args.cost, args, args.target_margin)
            out.append(f"- Lowest price for a {args.target_margin:g}% margin: "
                       + (money(tp, cur) if tp else "none found"))
        if args.sweep:
            prices = [float(x) for x in args.sweep.split(",") if x.strip()]
            out += ["", "| Price | Fees | Profit per order | Margin |", "|---|---|---|---|"]
            margins = []
            for p in prices:
                s = unit(profile, p, args.cost, args.packaging, args.inbound, args.weight, args.tax_rate)
                margins.append(s["profit"])
                out.append(f"| {money(p, cur)} | {money(s['fee_total'], cur)} | {money(s['profit'], cur)} | "
                           + (f"{s['margin_pct']:.1f}%" if s["margin_pct"] is not None else "n/a") + " |")
            if any(b < a for a, b in zip(margins, margins[1:])):
                out.append("\nNote: profit falls as price rises somewhere in this range; a fee tier "
                           "boundary is crossed. Check prices just below the boundary.")
        out.append("")
        summary.append((profile["channel"], u["profit"], u["margin_pct"], cur))
    if len(summary) > 1:
        out += ["## Channel comparison at this price", "", "| Channel | Profit per order | Margin |", "|---|---|---|"]
        for ch, prof, m, cur in sorted(summary, key=lambda s: s[1], reverse=True):
            out.append(f"| {ch} | {money(prof, cur)} | " + (f"{m:.1f}%" if m is not None else "n/a") + " |")
    text = "\n".join(line for line in out if line is not None) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("template", help="print an example fee profile")
    u = sub.add_parser("unit", help="profit per order, break-even and target price")
    u.add_argument("--fees", nargs="+", required=True)
    u.add_argument("--price", type=float)
    u.add_argument("--cost", type=float)
    u.add_argument("--packaging", type=float)
    u.add_argument("--inbound", type=float)
    u.add_argument("--weight", type=float)
    u.add_argument("--tax-rate", type=float, dest="tax_rate")
    u.add_argument("--products")
    u.add_argument("--sku")
    u.add_argument("--sweep")
    u.add_argument("--target-margin", type=float, dest="target_margin")
    u.add_argument("--out")
    args = ap.parse_args()
    if args.cmd == "template":
        print(json.dumps(TEMPLATE, indent=2))
    else:
        cmd_unit(args)


if __name__ == "__main__":
    main()
