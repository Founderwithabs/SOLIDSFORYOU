#!/usr/bin/env python3
"""Find what makes writing read as machine-made, check a rewrite kept every fact, and
compare a draft with the founder's own voice.

  python3 humanize.py check draft.txt [--channel linkedin] [--json]
  python3 humanize.py check --text "one line" [--channel x]
  python3 humanize.py compare before.txt after.txt      facts kept? (exit 1 if not)
  python3 humanize.py voice samples.txt [more.txt ...] --draft draft.txt
  python3 humanize.py profile text.txt                  the style numbers behind voice

Channels: general (default), linkedin, instagram, x, email, listing, script (spoken),
landing, reply. Each has its own limits for sentence length, dashes, exclamation marks,
emoji, hashtags, contractions and bullets (patterns.json).

check scores 0 to 100 (85+ reads human, 70-84 close, under 70 rewrite) from: the
phrase groups in patterns.json (AI vocabulary, hype, filler, essay transitions,
chatbot phrasing, intensifiers, unsupported claims, stock Hindi and Hinglish lines,
generic nouns), stock constructions ("it's not just X, it's Y", "No X. No Y. Just
Z."), openers and recap endings, and the shape of the text: sentence-length
variety, repeated sentence starts, lists of three, dashes, exclamation marks,
emoji, hashtags, bullets, bold, template headings, missing contractions, passive
voice, -ly adverbs, and whether anything concrete (a number, a name, a place) is
said at all.

It finds patterns. It can't tell whether a sentence is true, and a good score is not
a promise that any AI detector will pass the text: the aim is writing people believe.
Standard library only.
"""
import argparse
import collections
import json
import os
import re
import statistics
import sys

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS = os.path.join(os.path.dirname(HERE), "patterns.json")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF☀-➿⬀-⯿⌀-⏿]")
BULLET = re.compile(r"^\s*([-*•▪►→✓✔︎☑]|\d+[.)]|[\U0001F300-\U0001FAFF☀-➿])\s*")
CONTRACTION = re.compile(r"\b[a-z]+(?:'|’)(?:s|re|ve|ll|d|t|m)\b", re.I)
EXPANDABLE = re.compile(r"\b(it is|that is|there is|we are|you are|they are|i am|we have|you have|"
                        r"do not|does not|did not|is not|are not|was not|cannot|can not|will not|would not|"
                        r"should not|we will|you will|i will|let us|we would|it will)\b", re.I)
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+(\w+ed|built|made|done|given|taken|known|seen|shown|"
                     r"written|chosen|grown|worn|sold|kept|found|brought|thought|bought|held|told)\b", re.I)
TEMPLATE_HEADINGS = re.compile(r"^\s*(#+\s*)?\**(key takeaways?|final thoughts|the bottom line|conclusion|"
                               r"tl;?dr|in a nutshell|why it matters|why this matters|the takeaway|"
                               r"what you need to know|let'?s recap)\**\s*:?\s*$", re.I)
NUMBER = re.compile(r"(?:[₹$€£]\s?)?\d[\d,]*(?:\.\d+)?\s?(?:%|k\b|m\b|lakh|crore|cr\b|gsm|ml|kg|g\b|cm|mm|"
                    r"inch(?:es)?|hours?|hrs?|days?|weeks?|months?|years?|mins?|minutes?|x\b)?", re.I)
ROMAN_HINDI = {"hai", "hain", "nahi", "nahin", "kya", "toh", "bhi", "mein", "ka", "ki", "ke", "ko", "se", "yaar",
               "accha", "acha", "bas", "bahut", "kaafi", "matlab", "abhi", "kuch", "aur", "lekin", "par", "wala",
               "wali", "humne", "hum", "aap", "tum", "apna", "apne", "kar", "karo", "karna", "raha", "rahe", "gaya"}
STOP = set("""a an the and or but if then so to of in on at by for with from as is are was were be been being it its
this that these those i we you he she they them our your my me us his her their there here what which who whom
whose when where why how all any both each few more most other some such no nor not only own same than too very
can will just do does did doing have has had having would should could may might must shall about above after
again against because before below between down during further into off once out over through under until up
while also get got make made one two new like""".split())


def load_patterns():
    with open(PATTERNS, encoding="utf-8") as f:
        pats = json.load(f)
    groups, seen = [], {}
    for name, g in pats["groups"].items():
        for raw in g["phrases"]:
            phrase, _, plain = (part.strip() for part in raw.partition("=>"))
            key = phrase.lower()
            if key in seen and seen[key]["weight"] >= g["weight"]:
                continue  # listed in two groups: keep the stronger one
            seen[key] = {"group": name, "weight": g["weight"], "advice": g["advice"], "plain": plain,
                         "density": g.get("density", False), "phrase": phrase}
    for entry in seen.values():
        p = entry["phrase"]
        if all(ord(c) < 128 for c in p):
            entry["rx"] = re.compile(r"(?<![\w'’-])" + re.escape(p.lower()) + r"(?![\w'’-])")
        else:  # Devanagari word boundaries don't work with \b: match the phrase as written
            entry["rx"] = re.compile(re.escape(p.lower()))
        groups.append(entry)
    groups.sort(key=lambda g: -len(g["phrase"]))  # longest first, so "elevate your" isn't also "elevate"
    cons = [dict(c, rx=re.compile(c["regex"], re.I)) for c in pats["constructions"]]
    openers = [re.compile(r, re.I) for r in pats["openers"]]
    closers = [re.compile(r, re.I) for r in pats["closers"]]
    return groups, cons, openers, closers, pats["channels"], pats["claim_words"]


def read(path):
    try:
        return open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError as e:
        sys.exit(f"can't read {path}: {e.strerror}")


def split_sentences(text):
    text = re.sub(r"(?m)^\s*([-*•▪►→✓✔]|\d+[.)])\s+", "", text)  # a bullet's marker isn't part of the sentence
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text)
    return [p.strip() for p in parts if len(re.findall(r"[\w'’]+", p)) >= 2]


def words_of(text):
    return re.findall(r"[\w'’-]+", text)


def dashes(text):
    """Dashes used as punctuation inside a line; a bullet's leading "- " isn't one."""
    body = "\n".join(BULLET.sub("", l) for l in text.splitlines())
    return body.count("—") + len(re.findall(r"(?<=\S) (?:–|--?) (?=\S)", body))


def profile(text):
    """The style numbers voice matching and the shape checks use."""
    words = words_of(text)
    n = max(len(words), 1)
    sents = split_sentences(text)
    lengths = [len(words_of(s)) for s in sents]
    lines = [l for l in text.splitlines() if l.strip()]
    contractions = len(CONTRACTION.findall(text))
    expandable = len(EXPANDABLE.findall(text))
    lower = [w.lower().strip("'’") for w in words]
    mean = statistics.mean(lengths) if lengths else 0
    return {
        "words": len(words),
        "sentences": len(sents),
        "sentence_mean": round(mean, 1),
        "sentence_variety": round(statistics.pstdev(lengths) / mean, 2) if len(lengths) >= 2 and mean else None,
        "contraction_rate": round(contractions / (contractions + expandable), 2) if contractions + expandable else None,
        "exclaim_per_100": round(text.count("!") / n * 100, 2),
        "question_per_100": round(text.count("?") / n * 100, 2),
        "emoji_per_100": round(len(EMOJI.findall(text)) / n * 100, 2),
        "dash_per_100": round(dashes(text) / n * 100, 2),
        "first_person_per_100": round(sum(w in ("i", "we", "me", "us", "my", "our", "i'm", "we're", "we've")
                                          for w in lower) / n * 100, 1),
        "you_per_100": round(sum(w in ("you", "your", "you're", "you'll", "yours") for w in lower) / n * 100, 1),
        "bullet_share": round(sum(bool(BULLET.match(l)) for l in lines) / len(lines), 2) if lines else 0,
        "hinglish_share": round(sum(w in ROMAN_HINDI for w in lower) / n, 2),
        "word_length": round(statistics.mean(len(w) for w in words), 2) if words else 0,
        "concrete_per_100": round(len([m for m in NUMBER.findall(text) if re.search(r"\d", m)]) / n * 100, 2),
    }


def check(text, channel="general"):
    groups, cons, openers, closers, channels, _ = load_patterns()
    if channel not in channels:
        sys.exit(f"unknown --channel {channel}: use {', '.join(channels)}")
    lim = channels[channel]
    lines = text.splitlines()
    issues = []  # (line, kind, detail, weight)
    density_hits = 0
    for n, line in enumerate(lines, 1):
        low = line.lower()
        for g in groups:
            hits = len(g["rx"].findall(low))
            if not hits:
                continue
            low = g["rx"].sub(" ", low) if not g["density"] else low  # don't count it again inside a shorter phrase
            if g["density"]:
                density_hits += hits
                continue
            tip = f' (try "{g["plain"]}")' if g["plain"] else ""
            issues.append((n, g["group"], f'"{g["phrase"]}": {g["advice"]}{tip}', g["weight"] * min(hits, 2)))
        for c in cons:
            if c["rx"].search(line.lower()):
                issues.append((n, "construction", f"stock construction {c['name']}: say it straight", c["weight"]))
        if TEMPLATE_HEADINGS.match(line):
            issues.append((n, "heading", f"template heading \"{line.strip(' #*:')}\": cut it or say what's in it", 3))
        tags = re.findall(r"(?<![\w&])#\w+", line)
        if len(tags) > max(lim["hashtags_max"], 0) and len(tags) >= 2:
            issues.append((n, "hashtags", f"{len(tags)} hashtags on one line (this channel: {lim['hashtags_max']} at most)", 2))
        if line.count("!") >= 2:
            issues.append((n, "exclamation", f"{line.count('!')} exclamation marks in one line", 2))
        if channel in ("instagram", "x", "reply", "script") and ";" in line:
            issues.append((n, "semicolon", "a semicolon: people rarely use them here; use a full stop", 1))
    nonblank = [(i, l) for i, l in enumerate(lines, 1)
                if l.strip() and not re.fullmatch(r"(\s*#\w+)+\s*", l)]  # a hashtag block isn't the last line
    if nonblank:
        first_n, first = nonblank[0]
        last_n, last = nonblank[-1]
        if any(rx.search(first.strip().lower()) for rx in openers):
            issues.append((first_n, "opener", "throat-clearing opener: start with the point", 5))
        if len(nonblank) > 1 and any(rx.search(last.strip().lower()) for rx in closers):
            issues.append((last_n, "closer", "recap or engagement-bait ending: stop when the point is made", 4))

    p = profile(text)
    w = max(p["words"], 1)
    sents = split_sentences(text)
    lengths = [len(words_of(s)) for s in sents]
    lo, hi = lim["sentence_target"]
    if len(lengths) >= 5 and p["sentence_variety"] is not None and p["sentence_variety"] < 0.3:
        issues.append((0, "rhythm", f"sentences are all about {p['sentence_mean']:.0f} words: mix short and long", 4))
    if len(lengths) >= 3 and not lo <= p["sentence_mean"] <= hi:
        issues.append((0, "rhythm", f"sentences average {p['sentence_mean']:.0f} words; for {channel}, aim for "
                                    f"{lo} to {hi}", 2 if channel != "script" else 4))
    starts = [words_of(s)[0].lower() for s in sents if words_of(s)]
    if len(starts) >= 5:
        word, count = collections.Counter(starts).most_common(1)[0]
        if count >= 3 and count / len(starts) > 0.3 and word not in ("i",):
            issues.append((0, "rhythm", f"{count} of {len(starts)} sentences start with \"{word}\"", 3))
    if any(starts[i] == starts[i + 1] == starts[i + 2] for i in range(len(starts) - 2)):
        issues.append((0, "rhythm", "three sentences in a row start with the same word", 3))
    paras = [x for x in re.split(r"\n\s*\n", text) if x.strip()]
    if len(paras) >= 5 and all(len(split_sentences(x)) <= 1 for x in paras):
        issues.append((0, "rhythm", "every paragraph is one sentence: join some", 3))
    triples = re.findall(r"\b[\w'’-]+(?: [\w'’-]+){0,2}, [\w'’-]+(?: [\w'’-]+){0,2},? (?:and|or|&) [\w'’-]+", text)
    if len(triples) >= max(2, w // 120):
        issues.append((0, "rhythm", f"{len(triples)} lists of three (\"X, Y and Z\"): keep the one that matters", 3))
    if p["dash_per_100"] > lim["dash_per_100"] and p["dash_per_100"] * w / 100 >= 1:
        d = round(p["dash_per_100"] * w / 100)
        issues.append((0, "dashes", f"{d} dash{'es' if d != 1 else ''} in {w} words: use commas, "
                                    "full stops or brackets", 4))
    line_bangs = any(k == "exclamation" for _, k, _, _ in issues)
    if p["exclaim_per_100"] > lim["exclaim_per_100"] and text.count("!") >= 2 and not line_bangs:
        issues.append((0, "exclamation", f"{text.count('!')} exclamation marks: keep one, at most", 2))
    if p["emoji_per_100"] > lim["emoji_per_100"] and EMOJI.search(text):
        issues.append((0, "emoji", f"{len(EMOJI.findall(text))} emoji for {w} words: too many for {channel}", 2))
    emoji_starts = sum(bool(EMOJI.match(l.strip())) for l in lines if l.strip())
    if emoji_starts >= 3:
        issues.append((0, "emoji", f"{emoji_starts} lines start with an emoji: the emoji-bullet look reads as generated", 3))
    tags = re.findall(r"(?<![\w&])#\w+", text)
    if len(tags) > lim["hashtags_max"]:
        issues.append((0, "hashtags", f"{len(tags)} hashtags (this channel: {lim['hashtags_max']} at most)", 2))
    bullet_lines = sum(bool(BULLET.match(l)) for l in lines if l.strip())
    if bullet_lines >= 4 and p["bullet_share"] > lim["bullets_max_share"]:
        issues.append((0, "format", f"{bullet_lines} bulleted lines: say most of it in sentences", 3))
    bold = len(re.findall(r"\*\*[^*]+\*\*", text))
    if bold >= 3 and bold / w * 100 > 2:
        issues.append((0, "format", f"{bold} bold phrases: bold one thing, or nothing", 2))
    expandable = len(EXPANDABLE.findall(text))
    if expandable >= 3 and (p["contraction_rate"] or 0) < lim["contractions_min"]:
        issues.append((0, "stiff", f"{expandable} uncontracted forms (\"it is\", \"do not\"): people say \"it's\", "
                                   "\"don't\"", 3 if channel in ("script", "reply", "instagram", "x") else 2))
    passive = sum(bool(PASSIVE.search(s)) for s in sents)
    if len(sents) >= 4 and passive / len(sents) > 0.3:
        issues.append((0, "passive", f"{passive} of {len(sents)} sentences are passive: say who did it", 2))
    ly = [x for x in words_of(text) if len(x) > 4 and x.lower().endswith("ly")
          and x.lower() not in ("only", "early", "family", "daily", "weekly", "monthly", "apply", "supply",
                                "reply", "july", "italy", "likely", "rally", "fly", "ally", "belly", "jelly")]
    if len(ly) >= 3 and len(ly) / w * 100 > 3:
        issues.append((0, "adverbs", f"{len(ly)} -ly adverbs: cut most, or show it", 1))
    if density_hits and density_hits / w * 100 > 2:
        issues.append((0, "generic_nouns", f"{density_hits} generic nouns (users, solutions, results...): "
                                           "name a real customer, product or result", 3))
    if w >= 80 and p["concrete_per_100"] < 0.5 and not re.search(r"\b[A-Z][a-z]+\b(?<!^)", text[1:]):
        issues.append((0, "vague", "nothing concrete: add a number, a name, a place or a real example", 4))
    elif w >= 80 and p["concrete_per_100"] == 0:
        issues.append((0, "vague", "no numbers at all: add the price, size, time or result", 2))

    penalty = sum(x[3] for x in issues)
    score = max(0, min(100, round(100 - penalty / max(w, 60) * 100 * 2)))
    issues.sort(key=lambda x: (-x[3], x[0]))
    return {"channel": channel, "score": score, "verdict": verdict(score), "profile": p,
            "issues": [{"line": n, "kind": k, "detail": d, "weight": wt} for n, k, d, wt in issues]}


def verdict(score):
    return "reads human" if score >= 85 else "close: fix the flagged lines" if score >= 70 else "rewrite it"


def facts(text, claim_words):
    """What a rewrite must keep: numbers and money, links, handles, names and claims."""
    t = text.replace("’", "'")
    # A number is its value (and currency): "30-day" and "30 days" are the same fact, 220 and 240 aren't.
    nums = set()
    for m in re.finditer(r"([₹$€£])?\s?(\d[\d,]*(?:\.\d+)?)", t):
        value = m.group(2).replace(",", "").rstrip(".")
        nums.add((m.group(1) or "") + value)
    links = {u.rstrip(".,;:!?)'\"") for u in
             re.findall(r"https?://\S+|www\.\S+|\b[\w.-]+@[\w-]+\.[\w.]+\b", t)}
    handles = set(re.findall(r"(?<![\w@])@\w+", t))
    sentence_starts = {m.end() for m in re.finditer(r"(^|[.!?]\s+|\n\s*)", t)}
    names = set()
    for m in re.finditer(r"\b[A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*)*", t):
        if m.start() in sentence_starts and " " not in m.group(0):
            continue  # a capital at a sentence start is just grammar
        if m.group(0).lower() not in STOP and len(m.group(0)) > 1:
            names.add(m.group(0))
    low = t.lower()
    claims = {c for c in claim_words if re.search(r"(?<![\w-])" + re.escape(c) + r"(?![\w-])", low)}
    return {"numbers": nums, "links": links | handles, "names": names, "claims": claims}


def cmd_check(a):
    text = a.text if a.text is not None else (read(a.file) if a.file else None)
    if text is None:
        sys.exit("give a file, or --text")
    if not text.strip():
        sys.exit("nothing to check: the text is empty")
    r = check(text, a.channel)
    if a.json:
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return
    print(f"Humanizer ({r['channel']}): {r['score']}/100, {r['verdict']}. {r['profile']['words']} words, "
          f"{len(r['issues'])} flags.")
    for i in r["issues"]:
        print(f"- {'line ' + str(i['line']) if i['line'] else 'whole text'}: {i['detail']}")
    if r["issues"]:
        kinds = collections.Counter(i["kind"] for i in r["issues"])
        print("\nRewrite plan, biggest first: " + "; ".join(
            f"{k} ({c})" for k, c in sorted(kinds.items(), key=lambda kv: -sum(
                i["weight"] for i in r["issues"] if i["kind"] == kv[0])))[:400])
    else:
        print("- nothing flagged. Still read it aloud, check it sounds like the founder and every fact is true.")


def cmd_compare(a):
    *_, claim_words = load_patterns()
    before, after = read(a.before), read(a.after)
    fb, fa = facts(before, claim_words), facts(after, claim_words)
    lost = {k: sorted(fb[k] - fa[k]) for k in fb}
    added = {k: sorted(fa[k] - fb[k]) for k in fb}
    hard = any(lost[k] or added[k] for k in ("numbers", "links", "claims"))
    sb, sa = check(before, a.channel)["score"], check(after, a.channel)["score"]
    out = {"score_before": sb, "score_after": sa, "lost": lost, "added": added, "facts_kept": not hard}
    if a.json:
        print(json.dumps(out, indent=1, ensure_ascii=False))
    else:
        print(f"Humanizer score: {sb} -> {sa}.")
        if not hard and not lost["names"] and not added["names"]:
            print("Every number, price, link, name and claim is unchanged.")
        for k, label in (("numbers", "numbers and prices"), ("links", "links and handles"),
                         ("claims", "claims"), ("names", "names")):
            if lost[k]:
                print(f"- LOST {label}: {', '.join(lost[k])}")
            if added[k]:
                print(f"- ADDED {label}: {', '.join(added[k])}" + ("  (check: only the founder can add facts)"
                                                               if k != "names" else ""))
        if lost["names"] or added["names"]:
            print("  Names can change with rephrasing; check each one by eye.")
    sys.exit(1 if hard else 0)


def cmd_voice(a):
    samples = "\n\n".join(read(f) for f in a.samples)
    draft = read(a.draft)
    if len(words_of(samples)) < 80:
        sys.exit("give at least 80 words of the founder's own writing (posts, emails, messages) as samples")
    ps, pd = profile(samples), profile(draft)
    rows, notes = [], []
    checks = [
        ("sentence_mean", "words per sentence", 0.35, 3),
        ("sentence_variety", "sentence-length variety", 0.4, 0.15),
        ("contraction_rate", "contractions (it's, don't)", 0.35, 0.2),
        ("exclaim_per_100", "exclamation marks per 100 words", 0.6, 0.5),
        ("emoji_per_100", "emoji per 100 words", 0.6, 0.5),
        ("first_person_per_100", "I/we per 100 words", 0.5, 1.5),
        ("you_per_100", "you/your per 100 words", 0.5, 1.5),
        ("question_per_100", "questions per 100 words", 0.6, 0.5),
        ("bullet_share", "share of bulleted lines", 0.5, 0.2),
        ("hinglish_share", "Hinglish words", 0.5, 0.05),
        ("dash_per_100", "dashes per 100 words", 0.6, 0.4),
        ("word_length", "average word length", 0.12, 0.4),
    ]
    for key, label, rel, abs_ in checks:
        s, d = ps.get(key), pd.get(key)
        if s is None or d is None:
            continue
        off = abs(d - s) > abs_ and abs(d - s) > rel * max(abs(s), 1e-9)
        rows.append((label, s, d, off))
        if off:
            notes.append(f"{label}: founder {s}, draft {d}: move the draft toward the founder")
    sample_words = [w.lower() for w in words_of(samples) if w.lower() not in STOP and len(w) > 3]
    draft_words = {w.lower() for w in words_of(draft)}
    favourites = [w for w, c in collections.Counter(sample_words).most_common(40) if c >= 2]
    used = [w for w in favourites if w in draft_words]
    groups, *_ = load_patterns()
    sample_low, draft_low = samples.lower(), draft.lower()
    never = sorted({g["phrase"] for g in groups if not g["density"] and g["rx"].search(draft_low)
                    and not g["rx"].search(sample_low)})
    match = round(100 * (1 - sum(r[3] for r in rows) / max(len(rows), 1)))
    out = {"voice_match": match, "founder": ps, "draft": pd, "off": notes, "founder_words": favourites[:15],
           "founder_words_used": used, "phrases_the_founder_never_uses": never}
    if a.json:
        print(json.dumps(out, indent=1, ensure_ascii=False))
        return
    print(f"Voice match: {match}/100 against {ps['words']} words of the founder's writing.")
    print("\n| Measure | Founder | Draft | |\n|---|---|---|---|")
    for label, s, d, off in rows:
        print(f"| {label} | {s} | {d} | {'differs' if off else 'ok'} |")
    if notes:
        print("\nTo sound like the founder:")
        for n_ in notes:
            print(f"- {n_}")
    if never:
        print(f"- phrases in the draft the founder never uses: {', '.join(never[:12])}")
    if favourites:
        print(f"- words the founder uses often: {', '.join(favourites[:12])}"
              + (f" (the draft uses {', '.join(used)})" if used else " (the draft uses none)"))


def cmd_profile(a):
    text = read(a.file)
    if not text.strip():
        sys.exit("nothing to profile: the text is empty")
    print(json.dumps(profile(text), indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="score a draft and list what reads as machine-made")
    c.add_argument("file", nargs="?")
    c.add_argument("--text")
    c.add_argument("--channel", default="general")
    c.add_argument("--json", action="store_true")
    c = sub.add_parser("compare", help="check a rewrite kept every number, price, link, name and claim")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--channel", default="general")
    c.add_argument("--json", action="store_true")
    c = sub.add_parser("voice", help="compare a draft with the founder's own writing")
    c.add_argument("samples", nargs="+")
    c.add_argument("--draft", required=True)
    c.add_argument("--json", action="store_true")
    c = sub.add_parser("profile", help="the style numbers of a text")
    c.add_argument("file")
    a = ap.parse_args()
    {"check": cmd_check, "compare": cmd_compare, "voice": cmd_voice, "profile": cmd_profile}[a.cmd](a)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:  # output piped into head and cut short: not an error
        sys.stderr.close()
        os._exit(0)
