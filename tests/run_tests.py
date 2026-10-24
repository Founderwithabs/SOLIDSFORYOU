#!/usr/bin/env python3
"""Test the whole SOLIDS FOR YOU toolkit: structure, docs and every script.

  python3 tests/run_tests.py           run everything that can run here
  python3 tests/run_tests.py --fast    structure and docs only (no media)

Media tests build their own synthetic audio and video with ffmpeg, so no test
files are stored in the repo. A test whose tool is missing (ffmpeg, node with
Playwright, the claude CLI) is reported as SKIP, not as a pass. CI installs
all of them, so nothing is skipped there.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
ALLOWED_FRONTMATTER = {"name", "description"}  # what claude.ai skill uploads accept
RESULTS: list[tuple[str, str, str]] = []


class Skip(Exception):
    pass


def test(fn):
    """Run fn now and record PASS, FAIL or SKIP."""
    name = fn.__name__.removeprefix("test_").replace("_", " ")
    try:
        fn()
        RESULTS.append(("PASS", name, ""))
    except Skip as e:
        RESULTS.append(("SKIP", name, str(e)))
    except Exception as e:  # noqa: BLE001 - every failure is reported, none hidden
        detail = str(e) or traceback.format_exc(limit=2)
        RESULTS.append(("FAIL", name, detail))
    return fn


def need(*tools: str) -> None:
    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        raise Skip("missing " + ", ".join(missing))


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise AssertionError(f"{' '.join(map(str, cmd))} exited {r.returncode}:\n{(r.stderr or r.stdout)[-1500:]}")
    return r


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.relative_to(ROOT)}: no frontmatter"
    block = text[4 : text.index("\n---", 4)]
    out = {}
    for line in block.splitlines():
        if line and not line.startswith(" "):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


def plugin_names() -> list[str]:
    return sorted(p.name for p in PLUGINS.iterdir() if (p / ".claude-plugin" / "plugin.json").exists())


# ---------------------------------------------------------------- structure

def check_structure() -> None:
    @test
    def test_catalog_lists_every_plugin():
        catalog = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        listed = {e["name"]: e for e in catalog["plugins"]}
        assert sorted(listed) == plugin_names(), f"catalog {sorted(listed)} vs folders {plugin_names()}"
        for name, entry in listed.items():
            assert entry["source"] == f"./plugins/{name}", f"{name}: source {entry['source']}"

    @test
    def test_plugin_manifests_are_complete_and_branded():
        problems = []
        for name in plugin_names():
            m = json.loads((PLUGINS / name / ".claude-plugin/plugin.json").read_text())
            if m.get("name") != name:
                problems.append(f"{name}: manifest name is {m.get('name')!r}")
            if not str(m.get("displayName", "")).endswith("by SOLIDS FOR YOU"):
                problems.append(f"{name}: displayName {m.get('displayName')!r}")
            if not str(m.get("description", "")).startswith("SOLIDS FOR YOU"):
                problems.append(f"{name}: description should start 'SOLIDS FOR YOU'")
            if m.get("author", {}).get("name") != "SOLIDS FOR YOU":
                problems.append(f"{name}: author")
            if "version" in m:
                problems.append(f"{name}: has a version (founders then miss updates)")
            if m.get("license") != "MIT":
                problems.append(f"{name}: license is {m.get('license')!r}, must be 'MIT'")
            lic = PLUGINS / name / "LICENSE.md"
            if not lic.exists():
                problems.append(f"{name}: no LICENSE.md")
            elif lic.read_text() != (ROOT / "LICENSE.md").read_text():
                problems.append(f"{name}: LICENSE.md differs from the root LICENSE.md")
        assert not problems, "\n".join(problems)

    @test
    def test_skills_have_claude_ai_safe_frontmatter():
        problems = []
        for name in plugin_names():
            for skill in (PLUGINS / name / "skills").glob("*/SKILL.md"):
                fm = frontmatter(skill)
                extra = set(fm) - ALLOWED_FRONTMATTER
                if extra:
                    problems.append(f"{skill.relative_to(ROOT)}: claude.ai rejects {sorted(extra)}")
                if fm.get("name") != skill.parent.name:
                    problems.append(f"{skill.relative_to(ROOT)}: name {fm.get('name')!r} != folder")
                if len(fm.get("description", "")) < 40:
                    problems.append(f"{skill.relative_to(ROOT)}: description too short to trigger well")
        assert not problems, "\n".join(problems)

    @test
    def test_descriptions_stay_short():
        # Every installed skill's and helper's description is in every session.
        problems = []
        for name in plugin_names():
            for f in (PLUGINS / name).glob("skills/*/SKILL.md"):
                words = len(frontmatter(f)["description"].split())
                if words > 55:
                    problems.append(f"{f.relative_to(ROOT)}: {words} words (max 55)")
            for f in (PLUGINS / name).glob("agents/*.md"):
                words = len(frontmatter(f)["description"].split())
                if words > 40:
                    problems.append(f"{f.relative_to(ROOT)}: {words} words (max 40)")
        assert not problems, "\n".join(problems)

    @test
    def test_section_reader_is_lossless_and_finds_steps():
        readers = list(PLUGINS.glob("*/skills/*/scripts/read_sections.py"))
        if not readers:
            raise Skip("no read_sections.py")
        first = readers[0].read_bytes()
        assert all(r.read_bytes() == first for r in readers), "the read_sections.py copies differ"
        reader = readers[0]
        for prompt in [PLUGINS / "social-media/skills/social-media/social-media.md",
                       PLUGINS / "competitor-research/skills/competitor-research/competitor-research.md",
                       PLUGINS / "ecom/skills/ecom/marketplaces.md"]:
            if not prompt.exists():
                continue
            listing = run([sys.executable, str(reader), str(prompt), "--list"]).stdout
            tops = [l[1:l.index("]")] for l in listing.splitlines() if l[1:l.index("]")].isdigit()]
            joined = run([sys.executable, str(reader), str(prompt), *tops]).stdout
            text = prompt.read_text(encoding="utf-8")
            assert joined == text[text.index("\n## ") + 1:], f"{prompt.name}: sections don't rejoin to the file"
        method = PLUGINS / "competitor-research/skills/competitor-research/competitor-research.md"
        if method.exists():
            one = run([sys.executable, str(reader), str(method), "1"]).stdout
            assert "### Step" not in one, "section 1 must not pull in the steps"
            step = run([sys.executable, str(reader), str(method), "step3"]).stdout
            assert step.startswith("### Step 3.") and "### Step 4." not in step, step[:80]
        # Every section list a skill or helper asks for must exist.
        calls = re.compile(r'read_sections\.py" "SKILL_DIR/([\w.-]+)" ([\w. ]+)`')
        for doc in list(PLUGINS.glob("*/skills/*/SKILL.md")) + list(PLUGINS.glob("*/agents/*.md")):
            for target, keys in calls.findall(doc.read_text(encoding="utf-8")):
                path = next((PLUGINS / doc.relative_to(PLUGINS).parts[0]).glob(f"skills/*/{target}"))
                run([sys.executable, str(reader), str(path), *keys.split()])

    @test
    def test_repo_pointer_skills_match_plugins():
        problems = []
        for name in plugin_names():
            for skill in (PLUGINS / name / "skills").glob("*/SKILL.md"):
                pointer = ROOT / ".claude/skills" / skill.parent.name / "SKILL.md"
                if not pointer.exists():
                    problems.append(f"missing pointer {pointer.relative_to(ROOT)}")
                elif frontmatter(pointer) != frontmatter(skill):
                    problems.append(f"{pointer.relative_to(ROOT)}: frontmatter differs from the plugin's")
        assert not problems, "\n".join(problems)

    @test
    def test_bundled_files_referenced_by_skills_exist():
        # Paths written as SKILL_DIR/... or ${CLAUDE_SKILL_DIR}/... must exist
        # next to the SKILL.md, or the installed tool breaks.
        pattern = re.compile(r"(?:\$\{CLAUDE_SKILL_DIR\}|SKILL_DIR)/([\w./-]+\w)")
        problems = []
        for name in plugin_names():
            for skill_dir in (PLUGINS / name / "skills").iterdir():
                for doc in skill_dir.rglob("*.md"):
                    for rel in pattern.findall(doc.read_text(encoding="utf-8")):
                        if "<" in rel or "*" in rel:
                            continue
                        if not (skill_dir / rel).exists():
                            problems.append(f"{doc.relative_to(ROOT)} -> SKILL_DIR/{rel} does not exist")
        assert not problems, "\n".join(problems)

    @test
    def test_workflow_registry_paths_exist():
        problems, tables = [], 0
        for md in PLUGINS.glob("*/skills/*/**/*.md"):
            text = md.read_text(encoding="utf-8")
            if "<!-- REGISTRY" not in text:
                continue
            tables += 1
            table = text[text.index("<!-- REGISTRY"):].split("\n\n")[0]
            paths = re.findall(r"`(plugins/[^`]+)`", table)
            if not paths:
                problems.append(f"{md.relative_to(ROOT)}: registry table has no paths")
            problems += [f"{md.relative_to(ROOT)} -> {p}" for p in paths if not (ROOT / p).exists()]
        if not tables:
            raise Skip("no registry tables")
        assert not problems, "\n".join(problems)

    @test
    def test_relative_links_in_docs_resolve():
        problems = []
        docs = [ROOT / "README.md", ROOT / "CLAUDE.md", ROOT / "prompts/README.md"]
        docs += list(PLUGINS.glob("*/skills/*/README.md"))
        for doc in docs:
            if not doc.exists():
                continue
            for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", doc.read_text(encoding="utf-8")):
                if re.match(r"[a-z]+:", target):
                    continue
                if not (doc.parent / target).resolve().exists():
                    problems.append(f"{doc.relative_to(ROOT)} -> {target}")
        assert not problems, "broken links:\n" + "\n".join(problems)

    @test
    def test_raw_github_links_point_at_real_files():
        problems = []
        prefix = "https://raw.githubusercontent.com/Founderwithabs/SOLIDSFORYOU/main/"
        for doc in [ROOT / "README.md", ROOT / "prompts/README.md"]:
            for path in re.findall(re.escape(prefix) + r"([\w./-]+\w)", doc.read_text(encoding="utf-8")):
                if not (ROOT / path).exists():
                    problems.append(f"{doc.relative_to(ROOT)} -> {path}")
        assert not problems, "\n".join(problems)

    @test
    def test_readme_installs_every_plugin():
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        missing = [n for n in plugin_names() if f"/plugin install {n}@solidsforyou" not in readme]
        assert not missing, f"README has no install line for {missing}"

    @test
    def test_generated_files_are_up_to_date():
        run([sys.executable, "scripts/build_skill_zip.py", "--check"], cwd=ROOT)
        if (ROOT / "scripts/build_bundle.py").exists():
            run([sys.executable, "scripts/build_bundle.py", "--check"], cwd=ROOT)

    @test
    def test_no_bash_only_or_old_license_text_ships():
        # NODE_PATH=$(...) only works in bash; scripts find Playwright themselves.
        bad = {"NODE_PATH=$(": "bash-only NODE_PATH prefix", "PolyForm": "old license",
               "Noncommercial": "old license"}
        problems = []
        for f in list(PLUGINS.rglob("*")) + [ROOT / "README.md", ROOT / "prompts/README.md"]:
            if f.is_file() and f.suffix in {".md", ".py", ".cjs", ".json", ".html"}:
                text = f.read_text(encoding="utf-8")
                problems += [f"{f.relative_to(ROOT)}: {why}" for s, why in bad.items() if s in text]
        assert not problems, "\n".join(problems)

    @test
    def test_python_and_node_scripts_compile():
        for py in list(ROOT.glob("**/*.py")):
            if ".git" not in py.parts:
                compile(py.read_text(encoding="utf-8"), str(py), "exec")
        if shutil.which("node"):
            for js in ROOT.glob("plugins/**/*.cjs"):
                run(["node", "--check", str(js)])

    @test
    def test_plugin_hooks_run():
        hook_files = list(PLUGINS.glob("*/hooks/hooks.json"))
        if not hook_files:
            raise Skip("no plugin hooks")
        need("sh")
        for hf in hook_files:
            root = hf.parent.parent
            options = json.loads((root / ".claude-plugin/plugin.json").read_text()).get("userConfig", {})
            # Run each hook once with every option at its default, as a new user has it.
            env = {**{k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_DATA"},
                   **{f"CLAUDE_PLUGIN_OPTION_{k.upper()}": str(v.get("default", "")) for k, v in options.items()}}
            for event, groups in json.loads(hf.read_text())["hooks"].items():
                for group in groups:
                    for hook in group["hooks"]:
                        if hook.get("type") == "command":
                            cmd = hook["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(root))
                            r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, env=env, timeout=30)
                            assert r.returncode == 0, f"{root.name} {event} hook failed: {r.stderr[-300:]}"

    @test
    def test_every_tool_is_connected_to_master_and_its_neighbours():
        master = PLUGINS / "master/skills/master"
        if not master.exists():
            raise Skip("no master plugin")
        registry = (master / "master.md").read_text(encoding="utf-8").split("<!-- REGISTRY")[1].split("\n\n")[0]
        router = (master / "toolbox.md").read_text(encoding="utf-8")
        routing = (master / "master.md").read_text(encoding="utf-8").split("## 4.")[1].split("## 5.")[0]
        heads = {f.stem: f.read_text(encoding="utf-8") for f in sorted((master / "heads").glob("*.md"))}
        problems = []
        if not heads:
            problems.append("no head files in plugins/master/skills/master/heads/")
        # Master -> heads: every head is routed to, registered and described.
        for head, text in heads.items():
            title = head.capitalize()
            if not re.search(rf"\| {title} \(", router):
                problems.append(f"the {title} head has no row in toolbox.md")
            if f"heads/{head}.md" not in registry or f"heads/{head}.md" not in routing:
                problems.append(f"the {title} head is missing from master.md's registry or section 4")
            for section in ["## 1. When it runs", "## 2. Sub-skills", "## 3. Workflow", "## 4. Hand-offs", "## 5. Done when"]:
                if section not in text:
                    problems.append(f"heads/{head}.md has no '{section}'")
            # Heads load on every task they own, so keep them short.
            if len(text.split()) > 450:
                problems.append(f"heads/{head}.md is {len(text.split())} words; keep heads under 450")
            for other in text.split("## 4. Hand-offs")[-1].split("## 5.")[0].split("- ")[1:]:
                named = re.match(r"(\w+) head", other)
                if named and named.group(1).lower() not in heads:
                    problems.append(f"heads/{head}.md hands off to a head that doesn't exist: {named.group(1)}")
        # Heads -> sub-skills: every tool is registered and called by at least one head.
        for name in plugin_names():
            if name == "master":
                continue
            if not re.search(rf"\b{re.escape(name)}\b", registry):
                problems.append(f"{name} is missing from master.md's registry")
            if not any(re.search(rf"\b{re.escape(name)}\b", t) for t in heads.values()):
                problems.append(f"no head calls {name}")
        # Links between tools that save the founder paying or answering twice.
        links = [("harsh-buyer-review/skills/harsh-buyer-review/harsh-buyer-reviewer.md", "research/<name>-<date>/",
                  "the buyer reuses saved competitor research"),
                 ("master/skills/master/workflows/video.md", "ecom", "product videos follow the marketplace's video rules"),
                 ("master/skills/master/workflows/video.md", "memory/memory.csv", "videos check the memory sheet"),
                 ("master/skills/master/master.md", "memory/memory.csv", "every tool checks the memory sheet"),
                 ("competitor-research/skills/competitor-research/SKILL.md", "memory sheet", "research checks the memory sheet")]
        for rel, needle, why in links:
            f = PLUGINS / rel
            if f.exists() and needle not in f.read_text(encoding="utf-8"):
                problems.append(f"{rel}: lost the link that makes {why}")
        assert not problems, "\n".join(problems)

    @test
    def test_master_welcomes_the_founder_once():
        hooks = PLUGINS / "master/hooks/hooks.json"
        if not hooks.exists():
            raise Skip("no master plugin")
        need("sh")
        cmd = next(h["command"] for g in json.loads(hooks.read_text())["hooks"]["SessionStart"]
                   for h in g["hooks"] if "welcome" in h["command"])
        cmd = cmd.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGINS / "master"))
        with tempfile.TemporaryDirectory() as data:
            def start(**env):
                full = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_DATA"}
                return subprocess.run(["sh", "-c", cmd], capture_output=True, text=True,
                                      env={**full, **env}, timeout=30).stdout
            first = json.loads(start(CLAUDE_PLUGIN_DATA=data))
            assert "Oh my god, this is gold." in first["hookSpecificOutput"]["additionalContext"], first
            assert start(CLAUDE_PLUGIN_DATA=data) == "", "the welcome must only come once"
            assert start() == "", "without a plugin data folder there is nowhere to remember it: say nothing"

    @test
    def test_master_is_on_by_default_cheap_and_switchable():
        root = PLUGINS / "master"
        if not root.exists():
            raise Skip("no master plugin")
        need("sh")
        mode = json.loads((root / ".claude-plugin/plugin.json").read_text())["userConfig"]["mode"]
        assert mode["default"] == "always-on", mode
        assert set(mode["options"]) == {"task-specific", "always-on"}, mode
        cmd = json.loads((root / "hooks/hooks.json").read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        cmd = cmd.replace("${CLAUDE_PLUGIN_ROOT}", str(root))

        def session_start(value):
            env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_OPTION_MODE"}
            if value is not None:
                env["CLAUDE_PLUGIN_OPTION_MODE"] = value
            return subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, env=env, timeout=30).stdout

        router = session_start("always-on")
        assert "SOLIDS FOR YOU Master" in router, "always-on must load the router"
        assert session_start(None) == router, "an unset mode must behave as the always-on default"
        assert session_start("task-specific") == "", "task-specific mode must add nothing to the session"
        # Both are paid for in every session, so keep them small.
        assert len(router.split()) <= 400, f"router is {len(router.split())} words; keep it under 400"
        description = frontmatter(root / "skills/master/SKILL.md")["description"]
        assert len(description.split()) <= 70, f"master description is {len(description.split())} words"

    @test
    def test_claude_plugin_validate():
        need("claude")
        r = run(["claude", "plugin", "validate", "."], cwd=ROOT)
        out = r.stdout + r.stderr
        warnings = [l.strip() for l in out.splitlines() if l.strip().startswith(">")]
        unexpected = [w for w in warnings if "No version specified" not in w]
        assert not unexpected, "unexpected warnings:\n" + "\n".join(unexpected)


# -------------------------------------------------------------------- media

def ffmpeg(*args: str) -> None:
    run(["ffmpeg", "-v", "error", "-y", *args])


def check_media(tmp: Path) -> None:
    audio_dir = PLUGINS / "audio-review/skills/audio-review"
    analyze = audio_dir / "analyze.py"

    def analyse(path: Path) -> dict:
        out = tmp / (path.stem + "_out")
        run([sys.executable, str(analyze), str(path), "--out", str(out)])
        return json.loads((out / "metrics.json").read_text())

    @test
    def test_audio_review_measures_a_clean_stereo_file():
        need("ffmpeg")
        f = tmp / "clean.wav"
        ffmpeg("-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.1:d=8", "-ac", "2", "-ar", "44100", str(f))
        m = analyse(f)
        assert m["loudness"]["integrated_lufs"] is not None
        assert set(m["images"]) == {"spectrogram", "spectrogram_linear", "waveform"}, m["images"]
        assert all(Path(p).stat().st_size > 1000 for p in m["images"].values())
        assert m["levels"]["clipped_runs"] == 0
        assert not any("hum" in f.lower() for f in m["flags"]), m["flags"]

    @test
    def test_audio_review_catches_hum_lossy_cutoff_and_phase():
        need("ffmpeg")
        f = tmp / "dirty.mp3"
        ffmpeg("-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.3:d=10", "-f", "lavfi", "-i", "sine=60:d=10",
               "-filter_complex", "[0][1]amix=2:weights=1 0.5,pan=stereo|c0=c0|c1=-1*c0",
               "-ar", "44100", "-b:a", "96k", str(f))
        m = analyse(f)
        flags = " ".join(m["flags"])
        assert "60 Hz" in flags, flags
        assert m["spectrum"]["effective_bandwidth_hz"] < 17500, m["spectrum"]["effective_bandwidth_hz"]
        assert m["stereo"]["correlation"] < -0.9, m["stereo"]

    @test
    def test_audio_review_counts_clipping():
        need("ffmpeg")
        f = tmp / "clipped.wav"
        ffmpeg("-f", "lavfi", "-i", "sine=200:d=3,volume=16", "-ar", "48000", "-c:a", "pcm_s16le", str(f))
        m = analyse(f)
        assert m["levels"]["clipped_runs"] > 100, m["levels"]["clipped_runs"]

    @test
    def test_audio_review_survives_silence_mono_and_tiny_files():
        need("ffmpeg")
        cases = {
            "silent.wav": ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "3"],
            "mono.wav": ["-f", "lavfi", "-i", "sine=440:d=3", "-ac", "1"],
            "tiny.wav": ["-f", "lavfi", "-i", "sine=440:d=0.3"],
        }
        for name, args in cases.items():
            f = tmp / name
            ffmpeg(*args, str(f))
            m = analyse(f)
            assert "flags" in m, name
        assert analyse(tmp / "mono.wav")["stereo"]["mono"] is True

    @test
    def test_audio_review_reads_audio_from_video_files():
        need("ffmpeg")
        f = tmp / "with_sound.mp4"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=320x240:d=3", "-f", "lavfi", "-i", "sine=440:d=3",
               "-shortest", "-pix_fmt", "yuv420p", str(f))
        assert analyse(f)["loudness"]["integrated_lufs"] is not None

    @test
    def test_audio_review_api_script_builds_its_request():
        need("ffmpeg")
        f = tmp / "clean.wav"
        if not f.exists():
            raise Skip("clean.wav not built")
        r = run([sys.executable, str(audio_dir / "review.py"), str(f), "--dry-run",
                 "--out", str(tmp / "dry"), "--context", "podcast"])
        assert "DRY RUN" in r.stdout and r.stdout.count("[image]") == 3, r.stdout[-400:]

    inspect = PLUGINS / "motion-design-taste/skills/motion-design-taste/scripts/inspect_video.py"

    @test
    def test_motion_taste_inspects_a_video_with_sound():
        need("ffmpeg", "ffprobe")
        f = tmp / "cut.mp4"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=3", "-f", "lavfi", "-i",
               "color=c=navy:s=640x360:r=30:d=3", "-f", "lavfi", "-i", "sine=440:d=6",
               "-filter_complex", "[0][1]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-map", "2",
               "-shortest", "-pix_fmt", "yuv420p", str(f))
        out = tmp / "cut_inspect"
        r = run([sys.executable, str(inspect), str(f), str(out), "--zoom", "1", "--at", "2"])
        assert "Hard cuts (scene score >= 0.3): 1" in r.stdout, r.stdout
        assert "LUFS integrated" in r.stdout and "dBTP" in r.stdout, r.stdout
        for img in ["hook.png", "sheet_01.png", "zoom_1.00.png", "at_2.00.png", "report.md"]:
            assert (out / img).exists(), img

    @test
    def test_motion_taste_inspects_a_silent_vertical_video():
        need("ffmpeg", "ffprobe")
        f = tmp / "vertical.mp4"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=360x640:r=25:d=2", "-pix_fmt", "yuv420p", str(f))
        r = run([sys.executable, str(inspect), str(f), str(tmp / "vertical_inspect")])
        assert "Audio: NONE" in r.stdout, r.stdout

    vm = PLUGINS / "master/skills/master"  # the video build tools

    @test
    def test_video_sound_mix_hits_minus_14_lufs():
        need("ffmpeg")
        if not vm.exists():
            raise Skip("no master skill")
        cues = tmp / "cues.json"
        cues.write_text(json.dumps([{"t": t, "sfx": s, "gain": 0.3} for t, s in
                                    [(0.1, "whoosh"), (1, "pop"), (2, "ding"), (3, "thump"), (4, "riser"), (5, "tick")]]))
        vo = tmp / "vo.wav"
        ffmpeg("-f", "lavfi", "-i", "sine=200:d=8,volume=0.2", str(vo))
        mix = tmp / "mix.wav"
        run([sys.executable, str(vm / "scripts/sfx_mix.py"), "--cues", str(cues),
             "--duration", "8", "--vo", str(vo), "--out", str(mix)])
        log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mix), "-af", "ebur128=peak=true",
                              "-f", "null", "-"], capture_output=True, text=True).stderr
        lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", log)[-1])
        peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)[-1])
        assert abs(lufs + 14) <= 1.0, f"integrated {lufs} LUFS, target -14 +/- 1"
        assert peak <= -1.0, f"true peak {peak} dBTP"

    @test
    def test_video_renderer_renders_the_scene_template():
        need("ffmpeg", "ffprobe", "node")
        if not vm.exists():
            raise Skip("no master skill")
        probe = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        if probe.returncode != 0 and not (Path(root) / "playwright").exists():
            raise Skip("playwright not installed")
        out = tmp / "template.mp4"
        run(["node", str(vm / "scripts/render_html_video.cjs"), str(vm / "templates/scene-template.html"),
             str(out), "--from", "0", "--to", "1", "--width", "640", "--height", "360"], timeout=300)
        frames = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                      "stream=nb_read_frames,width,height", "-of", "csv=p=0", str(out)]).stdout.strip()
        assert frames == "640,360,30", frames


def check_scripts(tmp: Path) -> None:
    log = PLUGINS / "social-media/skills/social-media/scripts/content_log.py"

    @test
    def test_social_media_scorecard_totals_and_ship_rule():
        if not log.exists():
            raise Skip("no social-media")
        ok = run([sys.executable, str(log), "score", *"8 8 8 9 6 9 8 8 8 10".split()]).stdout
        assert "Total: 81/100. Ready to ship." in ok, ok
        bad = run([sys.executable, str(log), "score", *"10 10 10 10 10 10 10 10 10 9".split()]).stdout
        assert "Not ready" in bad and "compliance" in bad, bad
        wrong = subprocess.run([sys.executable, str(log), "score", "1", "2"], capture_output=True, text=True)
        assert wrong.returncode != 0, "accepted too few scores"

    @test
    def test_social_media_analytics_on_a_messy_export():
        if not log.exists():
            raise Skip("no social-media")
        header = run([sys.executable, str(log), "template"]).stdout.strip()
        rows = [
            "2026-09-01,Instagram,reel,fit,reach,result,A,,12000,,400,30,50,80,20,5,,42%",
            "2026-09-03,instagram,carousel,fabric,trust,mistake,B,,5000,,150,12,10,90,6,3,,",
            '2026-09-05,instagram,reel,fit,reach,relatable,C,,"30,000",,900,60,200,150,70,12,,55%',
            "2026-09-07,instagram,reel,offer,convert,result,D,,8000,,120,8,2,10,1,40,,",
            "2026-09-09,instagram,carousel,fabric,trust,mistake,E,,1.2K,,40,4,3,30,2,1,,",
            "2026-09-10,linkedin,text,founder,trust,contrarian,F,,,,50,10,2,1,4,2,,",
        ]
        csv_path = tmp / "posts.csv"
        csv_path.write_text("\ufeff" + header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
        out = tmp / "report.md"
        run([sys.executable, str(log), "analyze", str(csv_path), "--out", str(out)])
        report = out.read_text()
        assert "| instagram | 5 | 8,000 |" in report, report  # "30,000" and "1.2K" both parsed
        assert "lines 7." in report, report  # only the row with no views or reach
        assert "too few posts to rank" in report and "## By pillar" in report, report


def check_research(tmp: Path) -> None:
    skill = PLUGINS / "competitor-research/skills/competitor-research"
    ledger = skill / "scripts/ledger.py"

    @test
    def test_competitor_research_ledger_pipeline():
        if not ledger.exists():
            raise Skip("no competitor-research")
        import csv
        folder = tmp / "research"
        run([sys.executable, str(ledger), "init", str(folder)])
        with open(folder / "competitors.csv", "a", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["us", "Our Joggers", "Us", "amazon", "https://ex.com/us", ""])
            w.writerow(["c1", "Rival", "R", "amazon", "https://ex.com/c1", "Direct"])
            w.writerow(["c2", "Two Pack", "T", "flipkart", "https://ex.com/c2", "Price challenger"])
        cols = ["id", "competitor_id", "field", "value", "unit", "source_url", "captured_at",
                "method", "quote", "confidence", "verified"]
        facts = {
            "us": [("price_selling", "999", "INR"), ("pack_qty", "1", "piece"), ("rating", "4.3", "stars"),
                   ("ratings_count", "120", ""), ("claim", "Soft | Stretchy", "")],
            "c1": [("price_selling", "899", "INR"), ("pack_qty", "1", "piece"), ("rating", "4.1", "stars"),
                   ("ratings_count", "2400", ""), ("claim", "Cotton | Zip pockets", "")],
            "c2": [("price_selling", "1199", "INR"), ("pack_qty", "2", "piece"), ("rating", "blocked", ""),
                   ("ratings_count", "not found", "")],
        }
        for cid, rows in facts.items():  # each collector writes its own part file
            with open(folder / "parts" / f"ledger-{cid}.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, cols)
                w.writeheader()
                for i, (field, value, unit) in enumerate(rows, 1):
                    w.writerow(dict(id=f"{cid}-{i:03}", competitor_id=cid, field=field, value=value, unit=unit,
                                    source_url=f"https://ex.com/{cid}", captured_at="2026-10-23 10:00",
                                    method="page", quote=value if field == "claim" else "",
                                    confidence="high", verified=""))
        run([sys.executable, str(ledger), "merge", str(folder)])
        run([sys.executable, str(ledger), "check", str(folder)])
        run([sys.executable, str(ledger), "sample", str(folder)])
        run([sys.executable, str(ledger), "tables", str(folder)])
        tables = (folder / "tables.md").read_text()
        assert "| Two Pack | 1,199 INR | — | — | 2 piece | 599.50 | 1 |" in tables, tables[:900]
        claim = next(l for l in tables.splitlines() if l.startswith("| Main claim"))
        assert claim.count("\\|") == 2 and len(re.split(r"(?<!\\)\|", claim)) == 6, claim
        # A bad row must be caught.
        with open(folder / "ledger.csv", "a", newline="") as fh:
            csv.writer(fh).writerow(["c1-099", "c1", "price_selling", "1,299", "INR", "", "", "page", "", "high", ""])
        bad = subprocess.run([sys.executable, str(ledger), "check", str(folder)], capture_output=True, text=True)
        assert bad.returncode == 1 and "plain number" in bad.stdout and "source_url" in bad.stdout, bad.stdout

    @test
    def test_competitor_research_fetches_pages_and_reports_blocks():
        fetch = skill / "scripts/fetch_page.cjs"
        if not fetch.exists():
            raise Skip("no competitor-research")
        need("node")
        probe = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        if probe.returncode != 0 and not (Path(root) / "playwright").exists():
            raise Skip("playwright not installed")
        import http.server
        import threading
        site = tmp / "site"
        site.mkdir()
        (site / "product.html").write_text(
            '<html><head><meta charset="utf-8"><title>Rival</title><script type="application/ld+json">'
            '{"@type":"Product","name":"Rival","offers":{"price":"899","priceCurrency":"INR"},'
            '"aggregateRating":{"ratingValue":"4.1","ratingCount":"2400"}}</script></head>'
            '<body>₹899 M.R.P.: ₹1,299 500+ bought in past month</body></html>', encoding="utf-8")
        (site / "captcha.html").write_text("<p>Enter the characters you see below</p>")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=str(site), **k)

            def do_GET(self):
                if self.path == "/forbidden":
                    self.send_response(403)
                    self.end_headers()
                    return
                super().do_GET()

            def log_message(self, *a):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            results = {}
            for page in ["product.html", "captcha.html", "forbidden"]:
                out = tmp / "fetched" / page
                run(["node", str(fetch), f"{base}/{page}", str(out), "--wait", "200"], timeout=120)
                results[page] = json.loads((out / "meta.json").read_text())
        finally:
            server.shutdown()
        product = results["product.html"]
        assert product["blocked"] is False and product["products"][0]["price"] == "899", product
        assert "₹899" in product["hints"]["prices"], product["hints"]
        assert (tmp / "fetched/product.html/screenshot.png").exists()
        assert results["captcha.html"]["blocked"] is True, "captcha page not reported as blocked"
        assert results["forbidden"]["blocked"] is True and results["forbidden"]["status"] == 403


def check_memory(tmp: Path) -> None:
    memory = PLUGINS / "economy-mode/skills/economy-mode/scripts/memory.py"

    @test
    def test_memory_sheet_adds_searches_and_survives_sessions():
        if not memory.exists():
            raise Skip("no memory.py")
        sheet = tmp / "memory" / "memory.csv"
        env = {**os.environ, "SFY_MEMORY_FILE": str(sheet)}

        def mem(*args, ok=True):
            r = subprocess.run([sys.executable, str(memory), *args], capture_output=True, text=True, env=env)
            assert (r.returncode == 0) == ok, f"memory {args}: {r.stdout}{r.stderr}"
            return r.stdout

        assert mem("session-start") == "", "a project without a sheet must get nothing at session start"
        mem("add", "--type", "decision", "--topic", "pricing", "--text", "Joggers stay at ₹999 until Diwali")
        mem("add", "--type", "preference", "--topic", "voice", "--text", "No emojis on LinkedIn", "--pin")
        mem("add", "--type", "fact", "--topic", "supplier", "--text", "Fabric is 220 GSM cotton from Tiruppur")
        assert "already remembered" in mem("add", "--topic", "voice", "--text", "No emojis on LinkedIn")
        assert mem("search", "jogger price").splitlines()[0].startswith("#1 "), "price search must find #1"
        assert "#3" in mem("search", "fabric gsm")
        assert "nothing in memory matches" in mem("search", "quantum")
        mem("update", "1", "--text", "Joggers stay at ₹999 until 15 Nov")
        assert "15 Nov" in mem("search", "jogger price")
        mem("forget", "3")
        assert "nothing in memory matches" in mem("search", "fabric gsm"), "forgotten rows must not be found"
        start = mem("session-start")
        assert "No emojis" in start and "Joggers" not in start, start  # only pinned rows at session start
        mem("add", "--topic", "x", "--text", "a" * 600, ok=False)  # one memory per row
        raw = sheet.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), "the sheet needs a BOM so Excel shows ₹ correctly"
        import csv as _csv
        rows = list(_csv.DictReader(sheet.open(encoding="utf-8-sig")))
        assert len(rows) == 3 and rows[2]["status"] == "forgotten", rows  # forgotten rows stay in the sheet

    @test
    def test_memory_helper_section_briefs_helpers():
        if not memory.exists():
            raise Skip("no memory.py")
        sheet = tmp / "helpers" / "memory.csv"
        sheet.parent.mkdir()
        # a sheet made before the helpers column existed must still load and upgrade
        sheet.write_text("id,created,updated,type,topic,text,source,pinned,status\n"
                         "1,2026-10-01 10:00,2026-10-01 10:00,fact,brand,We sell cotton joggers,,,active\n",
                         encoding="utf-8-sig")

        def mem(*args):
            r = subprocess.run([sys.executable, str(memory), "--file", str(sheet), *args],
                               capture_output=True, text=True)
            assert r.returncode == 0, f"memory {args}: {r.stdout}{r.stderr}"
            return r.stdout

        assert "nothing for helpers" in mem("brief")
        mem("update", "1", "--helpers")
        mem("add", "--type", "number", "--topic", "returns", "--text", "Return rate 8% in September")
        mem("add", "--type", "preference", "--topic", "voice", "--text", "No emojis on LinkedIn", "--pin")
        brief = mem("brief")
        assert "cotton joggers" in brief and "No emojis" in brief and "Return rate" not in brief, brief
        assert "REMEMBER:" in brief, "helpers must be told how to report new facts"
        assert "Return rate" in mem("brief", "--task", "return rate"), "rows matching the task are added"
        mem("update", "1", "--no-helpers")
        assert "cotton joggers" not in mem("brief")
        for i in range(60):
            mem("add", "--topic", f"t{i}", "--text", "x" * 200, "--helpers")
        brief = mem("brief")
        assert len(brief) < 4600 and "left out" in brief, "the brief must stay about 1,000 tokens"
        assert "helpers" in mem("session-start"), "session start must tell Claude to brief helpers"


def check_ecom(tmp: Path) -> None:
    ecom = PLUGINS / "ecom/skills/ecom"

    def py(script, *args, ok=True):
        r = subprocess.run([sys.executable, str(ecom / "scripts" / script), *map(str, args)],
                           capture_output=True, text=True)
        assert (r.returncode == 0) == ok, f"{script} {args}: {r.stdout}{r.stderr}"
        return r.stdout

    @test
    def test_ecom_marketplace_index_matches_the_guide():
        skill = ecom / "SKILL.md"
        if not skill.exists():
            raise Skip("no ecom")
        # SKILL.md lists the guide's sections by number so Claude reads only one marketplace.
        index = " ".join(skill.read_text(encoding="utf-8").split("Sections:", 1)[1].split("Always include")[0].split())
        listed = {int(n): name for n, name in re.findall(r"(\d+) ([^,.]+?)(?=,| \d+ |\.|$)", index)}
        headings = {int(n): t for n, t in re.findall(r"(?m)^## (\d+)\. (.+)$",
                                                     (ecom / "marketplaces.md").read_text(encoding="utf-8"))}
        assert sorted(listed) == sorted(headings), f"SKILL.md lists {sorted(listed)}, the guide has {sorted(headings)}"
        for n, name in listed.items():
            assert headings[n].lower().startswith(name.split()[0].lower()), f"section {n}: '{name}' vs '{headings[n]}'"

    @test
    def test_ecom_unit_economics_match_hand_maths():
        if not (ecom / "scripts/economics.py").exists():
            raise Skip("no ecom")
        assert json.loads(py("economics.py", "template"))["fees"], "the template must be a usable fee profile"
        fees = tmp / "fees.json"
        fees.write_text(json.dumps({
            "channel": "test", "currency": "INR", "source": "test", "checked_at": "2026-10-24",
            "tax": {"mode": "inclusive", "rate_pct": 12, "on_fees_pct": 18, "fees_tax_recoverable": True},
            "fees": [{"name": "referral", "type": "percent", "value": 10, "of": "price"},
                     {"name": "closing", "type": "fixed", "value": 20}],
            "returns": {"rate_pct": 10, "cost_per_return": 50, "unsellable_pct": 50},
            "ads": {"tacos_pct": 10, "cost_per_order": None}}))
        out = py("economics.py", "unit", "--fees", fees, "--price", 1120, "--cost", 300, "--target-margin", 20)
        # By hand, per order placed, 90% kept: revenue 0.9 x 1120/1.12 = 900; fees 0.9 x 132 = 118.80;
        # returns 0.1 x 50 = 5; product 300 x (0.9 + 0.1 x 0.5) = 285; ads 10% of 0.9 x 1120 = 100.80.
        for want in ["900.00 INR", "-118.80 INR", "-5.00 INR", "-285.00 INR", "-100.80 INR",
                     "**390.40 INR**", "Margin on revenue: 43.4%", "(TACoS): 48.7%",
                     "Break-even price: 493.93 INR", "20% margin: 665.4"]:
            assert want in out, f"missing {want!r} in:\n{out}"

    @test
    def test_ecom_ads_returns_and_reorder_reports():
        if not (ecom / "scripts/ops.py").exists():
            raise Skip("no ecom")
        ads = tmp / "ads.csv"
        ads.write_text("Campaign Name,Impressions,Clicks,Spend,7 Day Total Sales (₹),7 Day Total Orders (#)\n"
                       'Joggers Auto,"10,000",200,"₹2,000.00","₹10,000.00",10\n'
                       "Brand Exact,5000,100,1000,1000,1\n", encoding="utf-8")
        out = py("ops.py", "ads", ads, "--breakeven-acos", 36.7, "--total-sales", 50000)
        assert "| Joggers Auto | 2,000.00 | 10,000.00 | 20.0% | 5.00 |" in out, out  # ₹ and commas parsed
        assert "100.0% | 1.00 | 1 | 10.00 | 2.00% | 1.00% | above break-even" in out, out
        assert "27.3%" in out and "TACoS" in out and "6.0%" in out, out
        returns = tmp / "returns.csv"
        returns.write_text("order id,reason\n1,Size too small\n2,Size too small\n3,Defective\n")
        out = py("ops.py", "returns", returns, "--orders", 30)
        assert "10.0%" in out and "| Size too small | 2 | 66.7% |" in out, out
        out = py("ops.py", "reorder", "--daily-sales", 10, "--lead-days", 30, "--on-hand", 300,
                 "--safety-days", 14, "--cover-days", 60)
        # reorder point 10 x (30 + 14) = 440; order up to 10 x (30 + 14 + 60) = 1,040, minus 300 on hand
        assert "Reorder point: 440" in out and "Order now: yes" in out and "740 units" in out, out

    @test
    def test_ecom_listing_check_catches_limits_keywords_and_risky_words():
        if not (ecom / "scripts/listing_check.py").exists():
            raise Skip("no ecom")
        listing = tmp / "listing.json"
        listing.write_text(json.dumps({"title": "Solid Threads Cotton Joggers for Men – Best Quality Joggers",
                                       "bullets": ["Soft 220 GSM cotton", "100% guaranteed best"],
                                       "search_terms": "jogger track pant ₹"}, ensure_ascii=False),
                           encoding="utf-8")
        keywords = tmp / "keywords.txt"
        keywords.write_text("cotton joggers\ntrack pants\nslim fit\n")
        out = py("listing_check.py", listing, "--keywords", keywords,
                 "--limits", "title=50,bullet=500,search_terms=20", ok=False)  # over a limit: exit 1
        assert "| title | 59 | 61 | 50 | OVER by 9 |" in out, out
        assert "| search terms | 19 | 21 | 20 bytes | OVER by 1 |" in out, out  # ₹ is 3 bytes
        assert "Keywords covered: 1 of 3" in out and "slim fit" in out, out
        assert "'guaranteed' in bullet 2" in out and "'100%' in bullet 2" in out, out
        listing.write_text(json.dumps({"title": "Cotton joggers"}))
        py("listing_check.py", listing)  # within limits: exit 0

    @test
    def test_ecom_image_check_measures_background_and_fill():
        need("ffmpeg", "ffprobe")
        if not (ecom / "scripts/image_check.py").exists():
            raise Skip("no ecom")
        main, side = tmp / "main.png", tmp / "side.jpg"
        ffmpeg("-f", "lavfi", "-i", "color=white:s=1500x1500,drawbox=x=300:y=300:w=900:h=900:color=red:t=fill",
               "-frames:v", "1", str(main))
        ffmpeg("-f", "lavfi", "-i", "color=0xEEEEEE:s=800x600", "-frames:v", "1", str(side))
        out_dir = tmp / "images"
        out = py("image_check.py", main, side, "--out", out_dir, "--main", main)
        row = next(l for l in out.splitlines() if l.startswith("| main.png"))
        assert "1500×1500" in row and "#FFFFFF" in row and "60.0%" in row and row.rstrip().endswith("yes |"), row
        row = next(l for l in out.splitlines() if l.startswith("| side.jpg"))
        assert "800×600" in row and row.rstrip().endswith("NO |"), row  # long side under 1000
        for size in (100, 160, 300):
            assert (out_dir / f"thumbs_{size}.png").exists(), f"no phone preview at {size}px"

    @test
    def test_ecom_renders_the_image_templates():
        need("node")
        if not (ecom / "scripts/render_image.cjs").exists():
            raise Skip("no ecom")
        probe = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        if probe.returncode != 0 and not (Path(root) / "playwright").exists():
            raise Skip("playwright not installed")
        for template in sorted((ecom / "templates").glob("*.html")):
            out = tmp / (template.stem + ".png")
            run(["node", str(ecom / "scripts/render_image.cjs"), str(template), str(out),
                 "--width", "1200", "--height", "1200"], timeout=180)
            head = out.read_bytes()[:24]
            assert head[:8] == b"\x89PNG\r\n\x1a\n", f"{template.name}: not a PNG"
            assert (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")) == (1200, 1200)


def check_video_and_visual_tools(tmp: Path) -> None:
    social = PLUGINS / "social-media/skills/social-media/scripts"
    visuals = PLUGINS / "ai-visuals/skills/ai-visuals/scripts"
    edit = PLUGINS / "master/skills/master/scripts/transcript_edit.py"
    srt = tmp / "talk.srt"
    cues = [(0, 4, "Today I will show you how to price cotton joggers."), (4.2, 5, "um"),
            (5.1, 9, "First we look at fabric cost and GSM."),
            (12, 16, "First we look at fabric cost and GSM per metre."),
            (16.1, 30, "Fabric cost fabric GSM supplier Tiruppur cotton fabric weight."),
            (35, 50, "Marketplace fees referral closing shipping fees Amazon Flipkart fees."),
            (55, 70, "Pricing strategy discount psychology ninety nine pricing anchor."),
            (75, 90, "Final thoughts subscribe and comment your price below.")]

    def ts(t):
        return f"00:{int(t // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)):03d}"
    srt.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n" for i, (a, b, text) in enumerate(cues, 1)))

    def py(script, *args, ok=True):
        r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)
        assert (r.returncode == 0) == ok, f"{script.name} {args}: {r.stdout}{r.stderr}"
        return r.stdout

    @test
    def test_transcript_edit_finds_dead_air_filler_and_retakes():
        if not edit.exists():
            raise Skip("no transcript_edit.py")
        out = py(edit, srt)
        assert "FILLER" in out and "um" in out, out
        assert 'REPEAT' in out and 'first we look at fabric' in out, out  # the restarted sentence
        assert out.count("DEAD") == 4 and "20.90s removed" in out, out
        need("ffmpeg", "ffprobe")
        video = tmp / "talk.mp4"
        ffmpeg("-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=90", "-f", "lavfi", "-i", "sine=f=440:d=90",
               "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video))
        cut = tmp / "cut.mp4"
        py(edit, srt, "--apply", video, cut)
        streams = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration",
                       "-of", "csv=p=0", str(cut)]).stdout.split()
        lengths = {k: float(v) for k, v in (x.split(",") for x in streams)}
        assert abs(lengths["video"] - 69.1) < 0.2 and abs(lengths["audio"] - lengths["video"]) < 0.1, lengths

    @test
    def test_chapters_drafts_and_checks_youtube_rules():
        if not (social / "chapters.py").exists():
            raise Skip("no chapters.py")
        out = py(social / "chapters.py", srt, "--target", 4)
        assert "0:00 " in out and "4 chapters" in out, out
        good, bad = tmp / "good.txt", tmp / "bad.txt"
        good.write_text("0:00 Intro\n0:16 Fabric costs\n0:35 Marketplace fees\n0:55 Pricing\n")
        bad.write_text("0:05 Intro\n0:10 Fabric\n")
        assert "valid" in py(social / "chapters.py", "--check", good, "--duration", 90)
        out = py(social / "chapters.py", "--check", bad, "--duration", 90, ok=False)
        assert "at least 3" in out and "must start at 0:00" in out and "needs 10s" in out, out

    @test
    def test_hookscore_and_package_check():
        if not (social / "hookscore.py").exists():
            raise Skip("no hookscore.py")
        hooks = tmp / "hooks.txt"
        hooks.write_text("I lost ₹4,00,000 on joggers before I learned this one pricing rule.\n"
                         "In this video we will talk about some things.\n", encoding="utf-8")
        scored = json.loads(py(social / "hookscore.py", "--json", hooks))
        by = {h["hook"][:4]: h for h in scored}
        assert by["I lo"]["verdict"] > by["In t"]["verdict"], scored  # a specific hook beats a summary
        assert by["In t"]["formula"] == "Unclassified", scored
        assert json.loads(py(social / "hookscore.py", "--format", "short", "--hook", "Stop doing this", "--json"))
        out = py(social / "package_check.py", "--title",
                 "I Tested 7 Jogger Brands So You Don't Have To (The Winner Shocked Me)", "--thumb", "WINNER SHOCKED ME")
        assert "desktop search cuts near 60" in out and "duplicate" in out and "concrete figure (7)" in out, out

    @test
    def test_outliers_ranks_against_each_channels_own_median():
        if not (social / "outliers.py").exists():
            raise Skip("no outliers.py")
        items = [{"channel": "Big", "title": f"Video {i}", "views": v, "url": f"b{i}", "duration": 600}
                 for i, v in enumerate([1000000, 1100000, 900000, 1050000, 950000])]
        items += [{"channel": "Small", "title": t, "views": v, "url": t, "duration": d} for t, v, d in
                  [("I tried 7 joggers for 30 days", 400000, 700), ("vlog", 30000, 600), ("vlog 2", 28000, 600),
                   ("vlog 3", 32000, 600), ("short a", 900000, 40), ("short b", 31000, 600)]]
        items += [{"channel": "Thin", "title": "x", "views": 5, "url": "x"}]
        listing = tmp / "collected.json"
        listing.write_text(json.dumps(items))
        ytdlp = tmp / "yt.json"  # yt-dlp --flat-playlist -J output
        ytdlp.write_text(json.dumps({"channel": "YT", "entries": [
            {"title": f"T{i}", "view_count": v, "url": f"y{i}", "duration": 500, "channel": "YT"}
            for i, v in enumerate([100, 120, 110, 90, 5000])]}))
        out = py(social / "outliers.py", listing, ytdlp, "--min", 2)
        assert "45.45x" in out and "12.70x" in out and "31,500 median" in out, out
        assert "Big" not in out.split("skipped")[0], "no Big video beats its own median by 2x"
        assert "Thin (1)" in out, out
        out = py(social / "outliers.py", listing, "--split-shorts", "--min", 2)
        assert "12.90x" in out and "short a" not in out, out  # long-form median 31,000; one short is too few

    @test
    def test_retention_reads_long_and_short_videos():
        if not (social / "retention.py").exists():
            raise Skip("no retention.py")

        def export(name, header, points):
            f = tmp / name
            f.write_text(header + "\n" + "\n".join(f"{x},{y:.2f}" for x, y in points))
            return f

        def report(f, duration):
            return json.loads(py(social / "retention.py", f, "--duration", duration, "--json"))

        # A 90-second Short exported as YouTube does: position as a share (0-1), rewatch spike at 0,
        # a steady slide and one cliff at 50% (45 s).
        short = [(i / 100, 120 if i == 0 else (100 - 8 * i if i <= 5 else 60 - 0.2 * (i - 5)) - (15 if i >= 50 else 0))
                 for i in range(101)]
        r = report(export("short.csv", "Video position (%),Absolute audience retention (%)", short), 90)
        assert r["start"] == 100 and len(r["cliffs"]) == 1, r
        assert abs(r["cliffs"][0]["at_seconds"] - 44.1) < 0.2, "a Short's percentages must not be read as seconds"
        # Seconds on the axis, 60-second video, cliff at 40 s.
        secs = [(t, 100 - 0.3 * t - (20 if t >= 40 else 0)) for t in range(0, 61, 2)]
        r = report(export("secs.csv", "Time (s),Retention (%)", secs), 60)
        assert [c["at_seconds"] for c in r["cliffs"]] == [38], r
        # An even slide has no cliffs, however many points it has.
        slide = [(t, 80 - t / 10) for t in range(0, 600, 30)]
        assert report(export("slide.csv", "position,retention", slide), 600)["cliffs"] == []

    @test
    def test_ai_visuals_score_diff_and_generation():
        if not (visuals / "score.py").exists():
            raise Skip("no ai-visuals")
        assert "Total: 89.5/100. Ready." in py(visuals / "score.py", 9, 10, 8, 7, 10, 9, 10, 10)
        out = py(visuals / "score.py", 9, 10, 8, 7, 10, 9, 10, 4)
        assert "Not ready" in out and "Platform rules and disclosure must be 10" in out, out
        py(visuals / "score.py", 9, 10, 8, ok=False)
        old, new = tmp / "old.txt", tmp / "new.txt"
        old.write_text("A photo of cotton joggers on a wooden table, soft light, 4k, ultra realistic")
        new.write_text("A studio photo of grey cotton joggers on a white background, soft light, realistic")
        out = py(visuals / "prompt_diff.py", old, new)
        assert 'Replaced "wooden table" with "white background"' in out and 'Removed: "4k , ultra"' in out, out
        # Generation against a local stand-in for the OpenAI API: no key, no money, no network.
        import base64
        import http.server
        import threading
        png = base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode()
        seen = []

        class Api(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                seen.append((self.path, self.headers["Authorization"], self.headers["Content-Type"], body))
                code, reply = (401, {"error": {"message": "bad key"}}) if "wrong" in self.headers["Authorization"] \
                    else (200, {"data": [{"b64_json": png}, {"b64_json": png}]})
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(reply).encode())

            def log_message(self, *a):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Api)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}/v1"
        gen = visuals / "generate_openai.py"

        def generate(*args, key="sk-test", ok=True):
            env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
            if key:
                env["OPENAI_API_KEY"] = key
            r = subprocess.run([sys.executable, str(gen), "--prompt-file", str(new), "--base-url", base, *map(str, args)],
                               capture_output=True, text=True, env=env)
            assert (r.returncode == 0) == ok, r.stdout + r.stderr
            return r.stdout + r.stderr
        try:
            assert "OPENAI_API_KEY is not set" in generate("--out", tmp / "x.png", key=None, ok=False)
            out = generate("--out", tmp / "gen.png", "--n", 2)
            assert (tmp / "gen.png").read_bytes().startswith(b"\x89PNG") and (tmp / "gen-2.png").exists(), out
            path, auth, ctype, body = seen[-1]
            assert path == "/v1/images/generations" and auth == "Bearer sk-test" and ctype == "application/json"
            assert json.loads(body)["n"] == 2
            product = tmp / "product.png"
            product.write_bytes(b"\x89PNG\r\n\x1a\nproduct")
            generate("--out", tmp / "edit.png", "--image", product)
            path, _, ctype, body = seen[-1]
            assert path == "/v1/images/edits" and ctype.startswith("multipart/form-data") and b"product" in body
            out = generate("--out", tmp / "y.png", key="sk-wrong", ok=False)
            assert "401" in out and "bad key" in out and "sk-wrong" not in out, "errors must never print the key"
        finally:
            server.shutdown()


def check_transcriber(tmp: Path) -> None:
    script = PLUGINS / "transcriber/skills/transcriber/scripts/transcribe.py"
    # A stand-in for faster-whisper, so the test needs no model download: it "hears" two
    # sentences with a 2-second pause and a stretched first word.
    fake = tmp / "fake"
    (fake / "faster_whisper").mkdir(parents=True)
    (fake / "faster_whisper/__init__.py").write_text("""
import types
import numpy as np

def decode_audio(path, sampling_rate=16000):
    return np.zeros(sampling_rate * 6, dtype=np.float32)

class WhisperModel:
    def __init__(self, where, device="cpu", compute_type="int8"):
        self.where = where

    def transcribe(self, audio, **kw):
        W = lambda s, e, w: types.SimpleNamespace(start=s, end=e, word=w, probability=0.9)
        segs = [types.SimpleNamespace(start=0.0, end=5.0, text="Hello founders. Price your joggers.",
                                      words=[W(0.0, 0.6, "Hello"), W(0.6, 1.2, "founders."),
                                             W(3.2, 3.8, "Price"), W(3.8, 4.2, "your"), W(4.2, 5.0, "joggers.")])]
        return iter(segs), types.SimpleNamespace(language="en", language_probability=0.99, duration=6.0)
""")

    def transcribe(*args, env=None):
        full = {**os.environ, "PYTHONPATH": str(fake), "SOLIDSFORYOU_WHISPER_CACHE": str(tmp / "cache"), **(env or {})}
        return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, env=full)

    @test
    def test_transcriber_writes_captions_the_other_tools_read():
        if not script.exists():
            raise Skip("no transcriber")
        try:
            import numpy  # noqa: F401
        except ImportError:
            raise Skip("numpy not installed")
        need("ffmpeg")
        note = tmp / "note.wav"
        ffmpeg("-f", "lavfi", "-i", "sine=f=300:d=6", str(note))
        r = transcribe(note, "--out-dir", tmp / "out", "--model-dir", tmp, "--no-install")
        assert r.returncode == 0, r.stdout + r.stderr
        srt = (tmp / "out/note.srt").read_text()
        assert "00:00:00,000 --> " in srt and srt.count(" --> ") == 2, srt  # the 2 s pause starts a new cue
        assert (tmp / "out/note.vtt").read_text().startswith("WEBVTT")
        data = json.loads((tmp / "out/note.json").read_text())
        assert data["language"] == "en" and data["segments"][1]["text"] == "Price your joggers.", data
        assert (tmp / "out/note.txt").read_text().splitlines()[0] == "Hello founders."
        # The captions feed the editing tool: the pause between the cues is dead air.
        edit = PLUGINS / "master/skills/master/scripts/transcript_edit.py"
        if edit.exists():
            out = run([sys.executable, str(edit), str(tmp / "out/note.srt")]).stdout
            assert "DEAD" in out, out

    @test
    def test_transcriber_refuses_a_model_that_fails_its_hash():
        if not script.exists():
            raise Skip("no transcriber")
        import hashlib
        pkg = tmp / "fake/sfy_test_model"
        (pkg / "data").mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "data/model.bin.part0").write_bytes(b"first half ")
        (pkg / "data/model.bin.part1").write_bytes(b"second half")
        good = hashlib.sha256(b"first half second half").hexdigest()

        def registry(digest):
            f = tmp / f"models-{digest[:6]}.json"
            f.write_text(json.dumps({"default": "base", "models": {"base": {
                "published": True, "packages": [{"name": "sfy-test-model", "version": "1", "module": "sfy_test_model"}],
                "files": {"model.bin": digest}}}}))
            return {"SOLIDSFORYOU_WHISPER_REGISTRY": str(f), "SOLIDSFORYOU_WHISPER_CACHE": str(tmp / f"cache-{digest[:6]}")}
        note = tmp / "silence.wav"
        need("ffmpeg")
        ffmpeg("-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "1", str(note))
        r = transcribe(note, "--out-dir", tmp / "h1", "--no-install", env=registry(good))
        assert "SOLIDS FOR YOU package (verified)" in r.stderr, r.stderr  # parts joined in order, hash matches
        assert (tmp / f"cache-{good[:6]}/base/model.bin").read_bytes() == b"first half second half"
        r = transcribe(note, "--out-dir", tmp / "h2", "--no-install", env=registry("0" * 64))
        assert "failed its SHA-256 check" in r.stderr, r.stderr
        assert not any((tmp / "cache-000000/base").iterdir()), "a model that fails its hash must be deleted"


def check_chaos_regressions(tmp: Path) -> None:
    """The silent wrong answers chaos testing found, pinned so they can't come back."""
    E = PLUGINS / "ecom/skills/ecom/scripts"
    S = PLUGINS / "social-media/skills/social-media/scripts"
    M = PLUGINS / "economy-mode/skills/economy-mode/scripts/memory.py"

    def py(script, *args, ok=True, env=None):
        r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                           env={**os.environ, **(env or {})}, encoding="utf-8", errors="replace")
        assert (r.returncode == 0) == ok, f"{script.name} {args}: {r.stdout}{r.stderr}"
        assert "Traceback" not in r.stdout + r.stderr, r.stderr
        return r.stdout + r.stderr

    @test
    def test_economics_rejects_settings_that_give_wrong_profit():
        if not (E / "economics.py").exists():
            raise Skip("no ecom")
        base = {"channel": "t", "currency": "INR", "source": "s", "checked_at": "2026-10-20",
                "fees": [{"name": "ref", "type": "percent", "value": 10, "of": "price"}]}
        for extra, said in [({"tax": {"mode": "inclusiv", "rate_pct": 18}}, "tax mode"),
                            ({"returns": {"rate_pct": 150}}, "rate_pct"),
                            ({"fees": [{"name": "r", "type": "percent_tiers", "tiers": []}]}, "tiers"),
                            ({"fees": {"ref": 10}}, "list of fees")]:
            f = tmp / "fees.json"
            f.write_text(json.dumps({**base, **extra}))
            assert said in py(E / "economics.py", "unit", "--fees", f, "--price", 999, "--cost", 300, ok=False)
        f.write_text(json.dumps(base))
        assert "must be above 0" in py(E / "economics.py", "unit", "--fees", f, "--price", -10, "--cost", 300, ok=False)

    @test
    def test_ads_report_skips_its_total_row_and_reads_tab_exports():
        if not (E / "ops.py").exists():
            raise Skip("no ecom")
        f = tmp / "ads.tsv"
        f.write_text("Campaign Name\tSpend\tSales\nX\t100\t500\nTotal\t100\t500\n")
        out = py(E / "ops.py", "ads", f, "--total-sales", 1000)
        assert "| **Total** | 100.00 | 500.00 |" in out and "TACoS (ad spend ÷ all sales 1,000.00): 10.0%" in out, out
        assert "summary row (Total)" in out, out
        # Semicolons inside names don't change the separator, and a campaign that starts with "Total" stays.
        f = tmp / "ads.csv"
        f.write_text('Campaign Name,Spend,Sales\n"Joggers; Men",100,500\nTotal Wellness Joggers,50,100\nTotal,150,600\n')
        out = py(E / "ops.py", "ads", f)
        assert "| Joggers; Men | 100.00 |" in out and "| Total Wellness Joggers | 50.00 |" in out, out
        assert "| **Total** | 150.00 | 600.00 |" in out, out

    @test
    def test_excel_windows_csv_and_short_counts_are_read():
        if not (S / "outliers.py").exists():
            raise Skip("no social-media")
        f = tmp / "views.csv"
        rows = ["channel;title;views"] + [f"Café;Vidéo {i};{v}" for i, v in enumerate(["1.2K", "1K", "1.1K", "900", "9K"])]
        f.write_bytes("\n".join(rows).encode("cp1252"))  # what Excel on Windows saves
        out = json.loads(py(S / "outliers.py", f, "--json", "--min", 2))
        assert [r["title"] for r in out["outliers"]] == ["Vidéo 4"] and out["outliers"][0]["views"] == 9000, out

    @test
    def test_scripts_print_rupees_and_hindi_through_windows_pipes():
        if not M.exists():
            raise Skip("no memory.py")
        sheet = tmp / "win" / "memory.csv"
        py(M, "--file", sheet, "add", "--topic", "pricing", "--text", "Joggers ₹999, क्या")
        out = py(M, "--file", sheet, "search", "joggers", env={"PYTHONIOENCODING": "cp1252"})
        assert "₹999" in out and "क्या" in out, out

    @test
    def test_listing_bullet_given_as_text_is_one_bullet():
        if not (E / "listing_check.py").exists():
            raise Skip("no ecom")
        f = tmp / "listing.json"
        f.write_text(json.dumps({"title": "Joggers", "bullets": "Soft 220 GSM cotton"}))
        out = py(E / "listing_check.py", f)
        assert "| bullet 1 | 19 |" in out and "bullet 2" not in out, out

    @test
    def test_retention_reads_european_exports():
        if not (S / "retention.py").exists():
            raise Skip("no social-media")
        f = tmp / "eu.csv"
        f.write_text("Position;Rétention\n" + "\n".join(f'"{i},5";"{90 - i},5"' for i in range(20)))
        r = json.loads(py(S / "retention.py", f, "--duration", 60, "--json"))
        assert r["points"] == 20 and r["start"] == 90.5, r

    @test
    def test_economy_hook_works_where_python3_is_missing():
        hooks = PLUGINS / "economy-mode/hooks/hooks.json"
        if not hooks.exists():
            raise Skip("no economy-mode hooks")
        cmd = json.loads(hooks.read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        assert "|| python " in cmd, "Windows often has python but not python3"

    @test
    def test_sound_library_lists_fetches_and_credits():
        get = PLUGINS / "master/skills/master/scripts/get_sounds.py"
        if not get.exists():
            raise Skip("no sound library")
        assert "get_sounds.py" in (PLUGINS / "master/skills/master/workflows/video.md").read_text(encoding="utf-8"), \
            "the video workflow must tell Claude the sound library exists"
        try:
            lib = json.loads((PLUGINS / "master/skills/master/sounds/library.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise AssertionError(f"sounds/library.json doesn't parse: {e}")
        problems = []
        for src in lib["sources"]:
            sid = src.get("id", "?")
            if not re.fullmatch(r"[0-9a-f]{40}", src.get("commit") or ""):
                problems.append(f"{sid}: pin a full commit")
            if not src.get("license_check"):
                problems.append(f"{sid}: needs a license_check")
            cats = src.get("categories") or {}
            if not cats or not all(isinstance(p, list) and p for p in cats.values()):
                problems.append(f"{sid}: needs categories, each with at least one path")
            # An exclude removes a file inside a category, never a whole category.
            for ex in src.get("exclude", []):
                for cat, paths in cats.items():
                    for p in paths:
                        if ex.rstrip("/") == p.rstrip("/*") or p.startswith(ex.rstrip("/") + "/"):
                            problems.append(f"{sid}: exclude {ex!r} removes all of category {cat!r} ({p})")
        assert not problems, "\n".join(problems)
        assert all(src["id"] in py(get, "list") for src in lib["sources"])
        assert "Unknown source" in py(get, "fetch", "nope", ok=False)
        dest = tmp / "sounds"
        need("git")
        r = subprocess.run([sys.executable, str(get), "fetch", "sfx-kit", "--category", "money", "--dest", str(dest)],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise Skip("couldn't reach GitHub to download sounds")
        wavs = sorted(dest.rglob("*.wav"))
        assert wavs and all("money" in str(w) for w in wavs), wavs
        assert "coin" in py(get, "find", "coin", "--dest", dest)
        assert "No credit required" in py(get, "credits", wavs[0], "--dest", dest)
        out = py(get, "credits", tmp / "mine.wav", "--dest", dest, ok=False)  # unknown files: check them yourself
        assert "Not from the library" in out and "No credit required" not in out, out

    @test
    def test_no_audio_is_committed():
        # Sounds are downloaded on demand; the repo never carries audio.
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
        audio = [f for f in tracked if f.lower().endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aiff", ".aif", ".opus"))]
        assert not audio, "audio files in the repo: " + ", ".join(audio[:10])

    @test
    def test_no_script_crashes_or_hangs_on_hostile_input():
        if "--fast" in sys.argv:
            raise Skip("full mode only")
        chaos = ROOT / "tests/chaos.py"
        r = subprocess.run([sys.executable, str(chaos)], capture_output=True, text=True, timeout=1800)
        assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-1000:]


def main() -> None:
    fast = "--fast" in sys.argv
    check_structure()
    with tempfile.TemporaryDirectory(prefix="sfy_scripts_") as tmp:
        check_scripts(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_research_") as tmp:
        check_research(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_memory_") as tmp:
        check_memory(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_ecom_") as tmp:
        check_ecom(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_video_visual_") as tmp:
        check_video_and_visual_tools(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_transcriber_") as tmp:
        check_transcriber(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_chaos_regressions_") as tmp:
        check_chaos_regressions(Path(tmp))
    if not fast:
        with tempfile.TemporaryDirectory(prefix="sfy_tests_") as tmp:
            check_media(Path(tmp))
    width = max(len(n) for _, n, _ in RESULTS)
    for status, name, detail in RESULTS:
        print(f"{status:4}  {name:<{width}}  {detail.splitlines()[0] if detail and status != 'FAIL' else ''}")
        if status == "FAIL":
            print("      " + detail.replace("\n", "\n      "))
    counts = {s: sum(1 for r in RESULTS if r[0] == s) for s in ("PASS", "FAIL", "SKIP")}
    print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped")
    sys.exit(1 if counts["FAIL"] else 0)


if __name__ == "__main__":
    main()
