#!/usr/bin/env python3
"""Build dist/<skill>-skill.zip for each tool that works on claude.ai.

These are the files people upload to claude.ai as custom skills. Run this
after changing any skill. Economy mode is left out because it needs Claude
Code's subagents.
"""

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
    "ai-visuals",
]

(ROOT / "dist").mkdir(exist_ok=True)
for name in SKILLS:
    folder = ROOT / "plugins" / name / "skills" / name
    out = ROOT / "dist" / f"{name}-skill.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, Path(name) / f.relative_to(folder))
        # The license's Required Notice must travel with every copy.
        z.write(ROOT / "plugins" / name / "LICENSE.md", Path(name) / "LICENSE.md")
    print(f"Wrote {out.relative_to(ROOT)}")
