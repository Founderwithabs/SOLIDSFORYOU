#!/usr/bin/env python3
"""Build dist/audio-review-skill.zip, the folder people upload to claude.ai as a custom skill."""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/audio-review/skills/audio-review"
OUT = ROOT / "dist/audio-review-skill.zip"

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(SKILL.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            z.write(f, Path("audio-review") / f.relative_to(SKILL))
print(f"Wrote {OUT.relative_to(ROOT)}")
