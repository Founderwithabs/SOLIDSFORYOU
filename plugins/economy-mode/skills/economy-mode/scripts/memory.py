#!/usr/bin/env python3
"""A memory sheet Claude keeps outside the conversation.

Facts, decisions, preferences and open tasks live in a CSV file that Excel
and Google Sheets open directly. Claude adds a row when something worth
remembering happens and looks up only the rows a task needs, so nothing is
forgotten after /clear, /compact or a new session, and the conversation
never has to carry the whole sheet.

  python3 memory.py add --type decision --topic pricing --text "Joggers stay at Rs 999 until Diwali"
  python3 memory.py add --type preference --topic voice --text "No emojis in LinkedIn posts" --pin
  python3 memory.py search "jogger price"       best 5 matching rows
  python3 memory.py pinned                      rows marked as always relevant
  python3 memory.py recent --n 10               newest rows
  python3 memory.py update 12 --text "..." [--pin | --unpin] [--type ...] [--topic ...]
  python3 memory.py forget 12                   hide a row (kept in the sheet, marked forgotten)
  python3 memory.py stats
  python3 memory.py session-start               short pinned summary for a session-start hook

The sheet is memory/memory.csv in the project (or --file PATH, or the
SFY_MEMORY_FILE environment variable). Standard library only.
"""

import argparse
import csv
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

COLUMNS = ["id", "created", "updated", "type", "topic", "text", "source", "pinned", "status"]
TYPES = ["fact", "decision", "preference", "task", "contact", "number", "note"]
MAX_TEXT = 500           # one row is one memory, not a document
SESSION_START_ROWS = 10  # pinned rows printed at session start
STOP = set("a an the and or of to in on for with is are was were be it this that at by from as".split())


def sheet_path(arg):
    if arg:
        return Path(arg)
    if os.environ.get("SFY_MEMORY_FILE"):
        return Path(os.environ["SFY_MEMORY_FILE"])
    base = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return base / "memory" / "memory.csv"


def load(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{c: (row.get(c) or "").strip() for c in COLUMNS} for row in csv.DictReader(f)]


def save(path, rows):
    """Write to a temporary file, then swap it in, so a crash never leaves half a sheet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".memory-", suffix=".csv")
    # utf-8-sig: Excel only shows ₹ and other non-English text correctly with the BOM.
    with os.fdopen(fd, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def line(r):
    pin = " [pinned]" if r["pinned"] == "yes" else ""
    return f"#{r['id']} {r['updated'][:10]} {r['type']}/{r['topic']}{pin}: {r['text']}"


def active(rows):
    return [r for r in rows if r["status"] != "forgotten"]


def find(rows, rid):
    for r in rows:
        if r["id"] == str(rid):
            return r
    sys.exit(f"no row #{rid}")


def cmd_add(a, path):
    text = " ".join(a.text.split())
    if not text:
        sys.exit("--text is empty")
    if len(text) > MAX_TEXT:
        sys.exit(f"keep one memory per row: {len(text)} characters, the limit is {MAX_TEXT}")
    rows = load(path)
    for r in active(rows):  # same topic and text already stored: just refresh it
        if r["topic"] == a.topic.lower() and r["text"].lower() == text.lower():
            r["updated"] = now()
            if a.pin:
                r["pinned"] = "yes"
            save(path, rows)
            print(f"already remembered, refreshed: {line(r)}")
            return
    next_id = max([int(r["id"]) for r in rows if r["id"].isdigit()] or [0]) + 1
    row = {"id": str(next_id), "created": now(), "updated": now(), "type": a.type,
           "topic": a.topic.lower(), "text": text, "source": a.source or "",
           "pinned": "yes" if a.pin else "", "status": "active"}
    rows.append(row)
    save(path, rows)
    print(f"remembered: {line(row)}")


def cmd_search(a, path):
    query = words(a.query)
    if not query:
        sys.exit("give some words to search for")
    scored = []
    for r in active(load(path)):
        topic, text = set(words(r["topic"])), set(words(r["text"] + " " + r["type"]))
        score = sum(2 for q in query if q in topic) + sum(1 for q in query if q in text)
        # partial matches ("price" finds "pricing")
        score += sum(0.5 for q in query for t in topic | text if len(q) > 3 and q != t and (q in t or t in q))
        if score:
            scored.append((score, r["pinned"] == "yes", r["updated"], r))
    scored.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
    if not scored:
        print("nothing in memory matches")
        return
    for *_, r in scored[: a.k]:
        print(line(r))
    if len(scored) > a.k:
        print(f"({len(scored) - a.k} more matches; narrow the search or raise --k)")


def cmd_pinned(a, path):
    rows = [r for r in active(load(path)) if r["pinned"] == "yes"]
    print("\n".join(line(r) for r in rows) or "nothing pinned")


def cmd_recent(a, path):
    rows = sorted(active(load(path)), key=lambda r: r["updated"], reverse=True)[: a.n]
    print("\n".join(line(r) for r in rows) or "memory is empty")


def cmd_update(a, path):
    rows = load(path)
    r = find(rows, a.id)
    if a.text:
        text = " ".join(a.text.split())
        if len(text) > MAX_TEXT:
            sys.exit(f"keep one memory per row: the limit is {MAX_TEXT} characters")
        r["text"] = text
    if a.type:
        r["type"] = a.type
    if a.topic:
        r["topic"] = a.topic.lower()
    if a.pin:
        r["pinned"] = "yes"
    if a.unpin:
        r["pinned"] = ""
    r["status"], r["updated"] = "active", now()
    save(path, rows)
    print(f"updated: {line(r)}")


def cmd_forget(a, path):
    rows = load(path)
    r = find(rows, a.id)
    r["status"], r["updated"] = "forgotten", now()
    save(path, rows)
    print(f"forgotten (kept in the sheet, hidden from searches): #{r['id']}")


def cmd_stats(a, path):
    rows = load(path)
    live = active(rows)
    by_type = {}
    for r in live:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    print(f"{path}: {len(live)} active rows ({sum(r['pinned'] == 'yes' for r in live)} pinned), "
          f"{len(rows) - len(live)} forgotten; " + ", ".join(f"{k} {v}" for k, v in sorted(by_type.items())))


def cmd_session_start(a, path):
    """Prints nothing unless the project has a memory sheet, so it costs nothing elsewhere."""
    rows = active(load(path)) if path.exists() else []
    if not rows:
        return
    pinned = sorted([r for r in rows if r["pinned"] == "yes"], key=lambda r: r["updated"], reverse=True)
    # Give the full command with --file, so a search from any folder finds this sheet.
    cmd = f'python3 "{Path(__file__).resolve()}" --file "{path.resolve()}"'
    print(f"Memory sheet ({len(rows)} rows). Before asking the founder something they may have told "
          f"you, search it (never read the whole file): {cmd} search \"key words\". "
          f"Save new facts and decisions with: {cmd} add --type decision --topic <topic> --text \"...\"")
    for r in pinned[:SESSION_START_ROWS]:
        print(line(r))
    if len(pinned) > SESSION_START_ROWS:
        print(f"({len(pinned) - SESSION_START_ROWS} more pinned rows: run pinned)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="memory sheet (default memory/memory.csv in the project)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("--type", choices=TYPES, default="note")
    p.add_argument("--topic", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--source", help="where it came from, e.g. 'founder, 2026-10-24 chat'")
    p.add_argument("--pin", action="store_true", help="always show it at session start")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    sub.add_parser("pinned")
    p = sub.add_parser("recent")
    p.add_argument("--n", type=int, default=10)
    p = sub.add_parser("update")
    p.add_argument("id")
    p.add_argument("--text")
    p.add_argument("--type", choices=TYPES)
    p.add_argument("--topic")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--pin", action="store_true")
    g.add_argument("--unpin", action="store_true")
    p = sub.add_parser("forget")
    p.add_argument("id")
    sub.add_parser("stats")
    sub.add_parser("session-start")
    a = ap.parse_args()
    path = sheet_path(a.file)
    {"add": cmd_add, "search": cmd_search, "pinned": cmd_pinned, "recent": cmd_recent,
     "update": cmd_update, "forget": cmd_forget, "stats": cmd_stats,
     "session-start": cmd_session_start}[a.cmd](a, path)


if __name__ == "__main__":
    main()
