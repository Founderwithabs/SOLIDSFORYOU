#!/usr/bin/env python3
"""Print only the numbered sections of a long prompt that a task needs.

Reading a whole prompt for a small job wastes tokens. This prints the
"## N." sections you ask for (with all their subsections), or one
"### N.M" subsection.

  python3 read_sections.py PROMPT.md 1 2 3 11      sections 1, 2, 3 and 11
  python3 read_sections.py PROMPT.md 6.2           only subsection 6.2
  python3 read_sections.py PROMPT.md step3 step4   only steps 3 and 4
  python3 read_sections.py PROMPT.md --list        section titles and sizes

Standard library only.
"""
import re
import sys


def parse(text):
    """[(key, top, title, body)] for every "## N." and "### ..." heading.

    key is "N" for "## N.", "N.M" for "### N.M" and "stepK" for "### Step K.";
    top is the "## N." section a heading sits in.
    """
    out, current, top = [], None, None
    for line in text.splitlines(keepends=True):
        m2 = re.match(r"## (\d+)\.? ", line)
        m3 = re.match(r"### (Step )?(\d+(?:\.\d+)?)\.? ", line)
        if m2:
            top = m2.group(1)
            current = [top, top, line.rstrip("\n"), [line]]
            out.append(current)
        elif m3 and top:
            key = ("step" + m3.group(2)) if m3.group(1) else m3.group(2)
            current = [key, top, line.rstrip("\n"), [line]]
            out.append(current)
        elif current:
            current[3].append(line)
    return [(k, t, title, "".join(body)) for k, t, title, body in out]


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    text = open(sys.argv[1], encoding="utf-8").read()
    parts = parse(text)
    if sys.argv[2] == "--list":
        for key, _, title, body in parts:
            print(f"[{key}] {title}  (~{len(body) // 4} tokens)")
        return
    wanted = sys.argv[2:]
    printed = set()
    for want in wanted:
        # A top-level number brings its whole section, subsections included.
        hits = [p for p in parts if p[0] == want or (want.isdigit() and p[1] == want)]
        if not hits:
            sys.exit(f"no section {want} in {sys.argv[1]} (use --list)")
        for key, _, _, body in hits:
            if key not in printed:
                printed.add(key)
                sys.stdout.write(body)


if __name__ == "__main__":
    main()
