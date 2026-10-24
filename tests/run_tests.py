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
                       PLUGINS / "competitor-research/skills/competitor-research/competitor-research.md"]:
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
            env = {**os.environ, **{f"CLAUDE_PLUGIN_OPTION_{k.upper()}": str(v.get("default", ""))
                                    for k, v in options.items()}}
            for event, groups in json.loads(hf.read_text())["hooks"].items():
                for group in groups:
                    for hook in group["hooks"]:
                        if hook.get("type") == "command":
                            cmd = hook["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(root))
                            r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, env=env, timeout=30)
                            assert r.returncode == 0, f"{root.name} {event} hook failed: {r.stderr[-300:]}"

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


def main() -> None:
    fast = "--fast" in sys.argv
    check_structure()
    with tempfile.TemporaryDirectory(prefix="sfy_scripts_") as tmp:
        check_scripts(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_research_") as tmp:
        check_research(Path(tmp))
    with tempfile.TemporaryDirectory(prefix="sfy_memory_") as tmp:
        check_memory(Path(tmp))
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
