#!/usr/bin/env python3
"""Build dist/<skill>-skill.zip for each tool that works on claude.ai.

These are the files people upload to claude.ai as custom skills. Run this
after changing any skill. Economy mode is left out because it needs Claude
Code's subagents.

The zips are reproducible: the same files always give byte-identical zips,
so git only shows a zip as changed when its contents changed.

  python3 scripts/build_skill_zip.py          rebuild the zips
  python3 scripts/build_skill_zip.py --check  exit 1 if a zip is out of date
"""

import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = [
    "audio-review",
    "motion-design-taste",
    "harsh-buyer-review",
    "careful-mode",
    "master",
    "social-media",
    "competitor-research",
    "ecom",
]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)  # earliest date a zip can hold


def add(z, src, arcname):
    info = zipfile.ZipInfo(str(arcname), date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    mode = 0o755 if src.stat().st_mode & 0o111 else 0o644
    info.external_attr = (0o100000 | mode) << 16
    z.writestr(info, src.read_bytes())


def build(name):
    folder = ROOT / "plugins" / name / "skills" / name
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                add(z, f, Path(name) / f.relative_to(folder))
        # MIT requires the copyright and license notice in every copy.
        add(z, ROOT / "plugins" / name / "LICENSE.md", Path(name) / "LICENSE.md")
    return data.getvalue()


def main():
    check = "--check" in sys.argv
    stale = []
    (ROOT / "dist").mkdir(exist_ok=True)
    for name in SKILLS:
        out = ROOT / "dist" / f"{name}-skill.zip"
        content = build(name)
        if out.exists() and out.read_bytes() == content:
            print(f"Up to date: {out.relative_to(ROOT)}")
        elif check:
            stale.append(str(out.relative_to(ROOT)))
        else:
            out.write_bytes(content)
            print(f"Wrote {out.relative_to(ROOT)}")
    if stale:
        sys.exit("Out of date (run python3 scripts/build_skill_zip.py): " + ", ".join(stale))


if __name__ == "__main__":
    main()
