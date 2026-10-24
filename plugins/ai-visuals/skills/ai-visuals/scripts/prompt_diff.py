#!/usr/bin/env python3
"""Show exactly what changed between two prompts, word by word.

Usage:
  python3 prompt_diff.py old_prompt.txt new_prompt.txt [--json]

Prints the words removed, added and replaced (with a few words of context so
each change can be found), plus words that only moved. Use it to explain
every change in a fixed prompt; anything it lists must trace to a problem
found in the image. Standard library only.
"""
import difflib
import json
import re
import sys
from pathlib import Path


PARAM = re.compile(r"(?:^|\s)--([a-zA-Z][\w-]*)((?:\s+(?!--)[^\s]+)*)")


def split_params(text):
    """Separate tool parameters (--ar 4:5, --no text, --s 100) from the prompt's words."""
    params = {}
    for m in PARAM.finditer(text):
        params[m.group(1).lower()] = m.group(2).strip()
    first = text.find(" --") if not text.startswith("--") else 0
    body = text[:first] if first >= 0 else text
    return body.strip(), params


def tokens(text):
    return re.findall(r"\"[^\"]*\"|[\w'’.%#:/-]+|[^\w\s]", text)


def context(toks, i, n=4):
    return " ".join(toks[max(0, i - n):i])


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    old_t, old_p = split_params(Path(args[0]).read_text(encoding="utf-8").strip())
    new_t, new_p = split_params(Path(args[1]).read_text(encoding="utf-8").strip())
    old, new = tokens(old_t), tokens(new_t)
    param_changes = []
    for k in sorted(set(old_p) | set(new_p)):
        if old_p.get(k) != new_p.get(k):
            param_changes.append({"param": "--" + k, "old": old_p.get(k), "new": new_p.get(k)})
    sm = difflib.SequenceMatcher(a=[t.lower() for t in old], b=[t.lower() for t in new], autojunk=False)
    changes = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        changes.append({"kind": {"delete": "removed", "insert": "added", "replace": "replaced"}[op],
                        "old": " ".join(old[i1:i2]), "new": " ".join(new[j1:j2]),
                        "after": context(old, i1) if op != "insert" else context(new, j1)})
    removed = {c["old"].lower() for c in changes if c["old"]}
    added = {c["new"].lower() for c in changes if c["new"]}
    moved = sorted(removed & added)
    changes = [c for c in changes if not (c["kind"] in ("removed", "added")
                                          and (c["old"] or c["new"]).lower() in moved)]
    result = {"old_words": len(old), "new_words": len(new),
              "similarity": round(sm.ratio() * 100, 1), "changes": changes, "moved": moved,
              "parameters": param_changes}
    if as_json:
        print(json.dumps(result, indent=1, ensure_ascii=False))
        return
    print(f"Old prompt {len(old)} tokens, new {len(new)}; {result['similarity']}% unchanged.\n")
    for n, c in enumerate(changes, 1):
        where = f' (after "{c["after"]}")' if c["after"] else " (at the start)"
        if c["kind"] == "removed":
            print(f'{n}. Removed: "{c["old"]}"{where}')
        elif c["kind"] == "added":
            print(f'{n}. Added: "{c["new"]}"{where}')
        else:
            print(f'{n}. Replaced "{c["old"]}" with "{c["new"]}"{where}')
    for m in moved:
        print(f'- Moved: "{m}"')
    for pc in param_changes:
        if pc["old"] is None:
            print(f'- Parameter added: {pc["param"]} {pc["new"]}'.rstrip())
        elif pc["new"] is None:
            print(f'- Parameter removed: {pc["param"]} {pc["old"]}'.rstrip())
        else:
            print(f'- Parameter {pc["param"]}: {pc["old"] or "(on)"} -> {pc["new"] or "(on)"}')
    if not changes and not moved and not param_changes:
        print("No changes.")


if __name__ == "__main__":
    main()
