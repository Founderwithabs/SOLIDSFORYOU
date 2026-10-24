#!/usr/bin/env python3
"""Check a LinkedIn post, headline, About section, comment or connection note before it goes out.

  python3 linkedin_check.py post.txt            a post (default)
  python3 linkedin_check.py --text "..."        a short piece given inline
  python3 linkedin_check.py headline.txt --headline
  python3 linkedin_check.py about.txt --about
  python3 linkedin_check.py note.txt --note      connection request note
  python3 linkedin_check.py reply.txt --comment  a comment or reply
  add --json for machine-readable output

For a post it shows what appears before "...see more" on a phone and on a desktop,
then checks: length against the limit, the hook (throat-clearing, announcements,
questions, a weak first line), wall-of-text paragraphs and one-line "broetry",
hashtags, tags, links, engagement bait ("Agree?", "Comment YES"), emoji bullets,
unicode bold, ALL CAPS, and whether anything concrete is said. Errors must be fixed;
warnings are judgement calls. It also runs the humanizer skill's check on the same
text when the humanizer is installed (found next to this plugin, or at
$SFY_HUMANIZER): under 70 is an error, under 85 a warning.

Limits (check LinkedIn's help pages; they change): post 3,000 characters, headline
220, About 2,600, connection note about 300. The fold is roughly 140 characters on a
phone and 210 on a desktop, and never more than 3 lines. Standard library only.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import unicodedata

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

LIMITS = {"post": 3000, "headline": 220, "about": 2600, "note": 300, "comment": 1250}
FOLD = {"phone": 140, "desktop": 210}
FOLD_LINES = 3
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF☀-➿⬀-⯿]")
BAIT = [r"\bagree\s*\?", r"\bthoughts\s*\?\s*$", r"\bcomment ['\"“]?\w+['\"”]? (below|if|to get)",
        r"\b(type|drop|comment) ['\"“]?(yes|me|interested|1|🔥|👇)\b", r"\blike if\b", r"\brepost (if|this)\b",
        r"♻️", r"\btag (someone|a friend|3|three)\b", r"\bfollow (me )?for more\b", r"\bsmash (that|the) like\b",
        r"\bwho else\b.*\?", r"\bshare (this )?if\b", r"\bdm me ['\"“]?\w+['\"”]?\b", r"\bp\.?s\.? follow\b",
        r"\bhit (the|that) bell\b", r"\bvote (in|below)\b"]
HOOK_BAD = [
    (r"^(i'?m|we'?re|i am|we are) (so )?(thrilled|excited|delighted|happy|proud|honou?red|humbled|pleased)",
     "an announcement opener: lead with what changed for the reader"),
    (r"^(i'?ve been thinking|lately i'?ve|let'?s talk about|today i want to|i wanted to share|here'?s (a|my) "
     r"(thought|story)|a few (thoughts|words)|quick (thought|update))", "throat-clearing: start with the point"),
    (r"^(in today'?s|in a world|in the (fast|ever|digital|modern))", "a cliché opener: start with something specific"),
    (r"^(did you know|have you ever|are you|do you|what if)\b.*\?", "a question the reader can answer \"no\" to"),
    (r"^(big news|exciting news|announcement|update|news)\b", "a label, not a hook: say the news itself"),
    (r"^(\d+ (lessons|tips|things|ways|mistakes|reasons))\b", "a listicle hook: lead with the most surprising one"),
]
BUZZ = ["passionate", "visionary", "guru", "ninja", "rockstar", "thought leader", "serial entrepreneur",
        "disruptor", "disruptive", "evangelist", "wizard", "hustler", "change-maker", "changemaker", "innovator",
        "results-driven", "results-oriented", "dynamic", "go-getter", "self-starter", "synergy", "growth hacker",
        "aspiring", "lifelong learner", "problem solver", "detail-oriented", "strategic thinker"]
COMMENT_EMPTY = [r"^(great|nice|awesome|amazing|insightful|interesting|love this|loved this|well said|so true|"
                 r"thanks for sharing|thank you for sharing|congrats|congratulations|spot on|100%|this|"
                 r"well put|very true|great insights?|valuable|helpful)( post| share| insights?| read| article| one|"
                 r" points?)?( [a-z]+)?[!. 👏🔥💯🙌]*$"]
GENERIC_END = (r"(what do you think|what are your thoughts|let me know (your thoughts|in the comments)|"
               r"share your thoughts|how about you|would love to hear your thoughts)\s*[?!.]*\s*$")


def is_math_styled(ch):
    """Unicode 'bold' and 'italic' letters (𝗕𝗼𝗹𝗱, 𝘪𝘵𝘢𝘭𝘪𝘤) used to fake formatting."""
    return "MATHEMATICAL" in unicodedata.name(ch, "")


def fold(text, width):
    lines = text.strip().splitlines()
    shown, used = [], 0
    for line in lines[:FOLD_LINES]:
        if used + len(line) > width:
            shown.append(line[: max(0, width - used)].rstrip() + "…")
            return "\n".join(shown), True
        shown.append(line)
        used += len(line) + 1
    return "\n".join(shown), len(lines) > FOLD_LINES or used < len(text.strip())


def check_post(text):
    errors, warnings = [], []
    chars = len(text.strip())
    if chars > LIMITS["post"]:
        errors.append(f"{chars} characters: LinkedIn posts stop at {LIMITS['post']}; cut {chars - LIMITS['post']}")
    lines = [l for l in text.strip().splitlines()]
    first = next((l.strip() for l in lines if l.strip()), "")
    low_first = first.lower()
    for rx, why in HOOK_BAD:
        if re.search(rx, low_first):
            errors.append(f"hook: {why}")
            break
    if len(first) > FOLD["phone"]:
        warnings.append(f"the first line is {len(first)} characters: a phone cuts it at about {FOLD['phone']}, "
                        "so the hook may be lost")
    if len(first.split()) <= 2 and not re.search(r"\d", first):
        warnings.append("the first line is only a word or two: say the concrete thing")
    if not re.search(r"\d|[A-Z][a-z]+\s+[A-Z]|₹|\$|%", " ".join(lines[:3])):
        warnings.append("nothing concrete before the fold (no number, name or price): readers decide there")
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    for p in paras:
        if len(p) > 300 and "\n" not in p:
            warnings.append(f"a {len(p)}-character paragraph: on a phone that's a wall; break it up "
                            f"(\"{p[:40]}...\")")
    single = [p for p in paras if len(re.findall(r"[.!?](\s|$)", p)) <= 1 and len(p) < 90]
    if len(paras) >= 8 and len(single) / len(paras) > 0.8:
        warnings.append(f"{len(single)} of {len(paras)} paragraphs are one short line (broetry): join some into "
                        "paragraphs of two or three sentences")
    tags = re.findall(r"(?<![\w&])#\w+", text)
    if len(tags) > 3:
        warnings.append(f"{len(tags)} hashtags: use three at most, at the end")
    body_tags = [t for t in tags if t not in (lines[-1] if lines else "")]
    if body_tags and len(tags) >= 1 and any(t in " ".join(lines[:-1]) for t in body_tags):
        warnings.append("hashtags inside sentences: move them to the end")
    mentions = re.findall(r"(?<![\w@])@\w[\w .'-]{0,30}", text)
    if len(mentions) > 5:
        warnings.append(f"{len(mentions)} people tagged: tag only those in the story who agreed")
    low = text.lower()
    for rx in BAIT:
        m = re.search(rx, low, re.M)
        if m:
            errors.append(f"engagement bait (\"{m.group(0).strip()}\"): LinkedIn says it limits this; "
                          "end with a takeaway or a specific question")
    last = next((l.strip() for l in reversed(lines) if l.strip() and not re.fullmatch(r"(#\w+\s*)+", l.strip())), "")
    if re.search(GENERIC_END, last.lower()):
        warnings.append(f"a generic closing question (\"{last[:50]}\"): ask something specific that invites "
                        "experience, or end on the takeaway")
    links = re.findall(r"https?://\S+|www\.\S+", text)
    if links:
        warnings.append(f"{len(links)} link(s) in the post: fine, but if reach matters, test putting it in the "
                        "first comment (LinkedIn hasn't confirmed a penalty)")
    emoji_lines = sum(bool(EMOJI.match(l.strip())) for l in lines if l.strip())
    if emoji_lines >= 3:
        errors.append(f"{emoji_lines} lines start with an emoji: the emoji-bullet look reads as generated")
    styled = sum(is_math_styled(c) for c in text)
    if styled:
        errors.append(f"{styled} unicode 'bold' or 'italic' characters: screen readers and LinkedIn search "
                      "can't read them; use plain text")
    caps = [w for w in re.findall(r"\b[A-Z]{4,}\b", text) if w not in ("GSM", "COVID", "NASA", "SAAS", "HTTPS")]
    if len(caps) >= 3:
        warnings.append(f"{len(caps)} words in ALL CAPS ({', '.join(caps[:4])}): it reads as shouting")
    words = len(re.findall(r"[\w'’-]+", text))
    if words < 40:
        warnings.append(f"{words} words: fine for a quick update; most founder posts that land are 120 to 300")
    elif words > 450:
        warnings.append(f"{words} words: long for LinkedIn; is it one idea?")
    return errors, warnings, {"characters": chars, "limit": LIMITS["post"], "words": words,
                              "read_seconds": round(words / 4), "fold_phone": fold(text, FOLD["phone"])[0],
                              "fold_desktop": fold(text, FOLD["desktop"])[0]}


def check_short(text, kind):
    errors, warnings = [], []
    chars = len(text.strip())
    if chars > LIMITS[kind]:
        errors.append(f"{chars} characters: the {kind} limit is about {LIMITS[kind]}")
    low = text.lower()
    if kind in ("headline", "about"):
        hits = [b for b in BUZZ if re.search(r"(?<![\w-])" + re.escape(b) + r"(?![\w-])", low)]
        if hits:
            errors.append(f"buzzwords: {', '.join(hits)}: say who you help and one proof instead")
        if kind == "headline" and text.count("|") >= 3:
            warnings.append("a chain of titles separated by |: say who you help, how, and one result")
        if not re.search(r"\d", text):
            warnings.append("no number: one result (customers, %, ₹, years) makes it believable")
    if kind == "about":
        first3 = "\n".join(text.strip().splitlines()[:3])
        if len(first3) > FOLD["desktop"] + 60:
            warnings.append("the first lines are long: only about three lines show before 'see more'")
        if re.search(r"\b(he|she) (is|has)\b", low[:200]):
            warnings.append("written in the third person: the About section reads better as 'I'")
    if kind == "note":
        if re.search(r"\b(buy|pricing|demo|our product|our service|sale|discount|offer)\b", low):
            warnings.append("a pitch in a connection note: give the reason to connect, sell later")
        if len(text.split()) < 8:
            warnings.append("too short to say why you're connecting")
    if kind == "comment":
        if any(re.search(rx, low.strip()) for rx in COMMENT_EMPTY):
            warnings.append("an empty comment: add an experience, a number or a real question")
        if len(text.split()) > 120:
            warnings.append("a long comment: two to four sentences usually lands better")
    styled = sum(is_math_styled(c) for c in text)
    if styled:
        errors.append(f"{styled} unicode 'bold' or 'italic' characters: use plain text")
    return errors, warnings, {"characters": chars, "limit": LIMITS[kind]}


def find_humanizer():
    """The humanizer skill's checker, wherever the founder installed it: next to this plugin in the
    plugin cache (<marketplace>/humanizer/<version>/...), next to it in the repo (plugins/humanizer/...),
    or at $SFY_HUMANIZER."""
    if os.environ.get("SFY_HUMANIZER") and os.path.isfile(os.environ["SFY_HUMANIZER"]):
        return os.environ["SFY_HUMANIZER"]
    here = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    tail = os.path.join("skills", "humanizer", "scripts", "humanize.py")
    found = [os.path.join(os.path.dirname(plugin_root), "humanizer", tail)]
    found += glob.glob(os.path.join(os.path.dirname(os.path.dirname(plugin_root)), "humanizer", "*", tail))
    found = [f for f in found if os.path.isfile(f)]
    return max(found, key=os.path.getmtime) if found else None


def humanizer_pass(text, kind):
    """Run the humanizer on the same text, so the LinkedIn check never skips it."""
    hz = find_humanizer()
    if not hz:
        return None, ("the humanizer skill isn't installed, so the writing itself wasn't checked: "
                      "/plugin install humanizer@solidsforyou")
    channel = "reply" if kind in ("note", "comment") else "linkedin"
    r = subprocess.run([sys.executable, hz, "check", "--text", text, "--channel", channel, "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout), None
    except ValueError:
        return None, "the humanizer couldn't check this text: run it yourself"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--text")
    kind = ap.add_mutually_exclusive_group()
    for k in ("headline", "about", "note", "comment"):
        kind.add_argument(f"--{k}", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.text is not None:
        text = a.text
    elif a.file:
        try:
            text = open(a.file, encoding="utf-8-sig", errors="replace").read()
        except OSError as e:
            sys.exit(f"can't read {a.file}: {e.strerror}")
    else:
        ap.print_help()
        sys.exit(2)
    if not text.strip():
        sys.exit("nothing to check: the text is empty")
    if "\x00" in text:
        sys.exit("that isn't text: give the post as a .txt file or with --text")
    k = next((x for x in ("headline", "about", "note", "comment") if getattr(a, x)), "post")
    errors, warnings, stats = check_post(text) if k == "post" else check_short(text, k)
    human, problem = humanizer_pass(text, k)
    if problem:
        warnings.append(problem)
    elif human:
        stats["humanizer_score"] = human["score"]
        stats["humanizer_flags"] = [i["detail"] for i in human["issues"][:6]]
        if human["score"] < 70:
            errors.append(f"humanizer {human['score']}/100: it reads machine-written; rewrite it (flags below)")
        elif human["score"] < 85:
            warnings.append(f"humanizer {human['score']}/100: close; fix the flags below")
    if a.json:
        print(json.dumps({"kind": k, "errors": errors, "warnings": warnings, **stats}, indent=1,
                         ensure_ascii=False))
    else:
        print(f"LinkedIn {k}: {stats['characters']}/{stats['limit']} characters, "
              f"{len(errors)} errors, {len(warnings)} warnings.")
        if k == "post":
            print(f"\nBefore 'see more' on a phone:\n  " + stats["fold_phone"].replace("\n", "\n  "))
            print(f"On a desktop:\n  " + stats["fold_desktop"].replace("\n", "\n  "))
        for e in errors:
            print(f"- ERROR: {e}")
        for w in warnings:
            print(f"- warning: {w}")
        if "humanizer_score" in stats:
            print(f"\nHumanizer ({'reply' if k in ('note', 'comment') else 'linkedin'}): {stats['humanizer_score']}/100")
            for flag in stats["humanizer_flags"]:
                print(f"  - {flag}")
        if not errors and not warnings:
            print("- nothing flagged. After any rewrite, run the humanizer's compare so no fact changed.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.stderr.close()
        sys.exit(0)
