#!/usr/bin/env python3
"""Transcribe a voice note, podcast or video with OpenAI's Whisper, inside the chat's own sandbox.

Usage:
  python3 transcribe.py FILE [--size base|small] [--language auto|en|hi|...]
        [--prompt "words or names to expect"] [--translate] [--out-dir DIR]
        [--model-dir DIR] [--no-install]

Writes FILE's name with .txt, .srt, .vtt and .json (Whisper-style segments with
word timings) into --out-dir (default: next to the file), and prints the full
transcript. The .srt and .json work with the other SOLIDS FOR YOU tools
(transcript_edit.py, chapters.py, retention.py).

How it finds what it needs, with nothing for the founder to set up:
  1. the engine: faster-whisper (installed from PyPI automatically if missing);
  2. the model, first match wins:
     --model-dir; a verified copy cached earlier; the SOLIDS FOR YOU model
     packages on PyPI listed in models.json (every file checked against the
     SHA-256 recorded there); faster-whisper's own download (works where
     Hugging Face is reachable).
If none works, it says so and lists the no-code alternatives.
The audio never leaves the sandbox. Needs Python 3.9+. Audio is decoded with ffmpeg
when it's installed (most reliable), otherwise with faster-whisper's own decoder.
"""
import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = json.loads(Path(os.environ.get("SOLIDSFORYOU_WHISPER_REGISTRY", HERE / "models.json"))
                      .read_text(encoding="utf-8"))
CACHE = Path(os.environ.get("SOLIDSFORYOU_WHISPER_CACHE",
                            Path.home() / ".cache" / "solidsforyou-whisper"))

FALLBACK = """No speech model could be loaded here, so nothing was transcribed.
Ways to get a transcript without a computer:
  - iPhone: Voice Memos shows a transcript for recordings (copy it into the chat).
  - Android: the Recorder app (on many phones) transcribes as it records.
  - YouTube: upload as unlisted; YouTube Studio > Subtitles makes automatic captions.
  - Instagram and TikTok: turn on auto-captions and copy them.
Then paste the text (or the .srt file) into the chat."""


def log(msg):
    print(f"[transcriber] {msg}", file=sys.stderr, flush=True)


def pip_install(*pkgs):
    log("installing " + " ".join(pkgs) + " (first run only)")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                        *pkgs], capture_output=True, text=True)
    if r.returncode != 0:
        log("install failed: " + (r.stderr.strip().splitlines() or ["unknown error"])[-1])
        return False
    importlib.invalidate_caches()
    return True


def ensure_engine(allow_install):
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        if allow_install and pip_install("faster-whisper"):
            try:
                import faster_whisper  # noqa: F401
                return True
            except ImportError:
                pass
    return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verified(folder, expected):
    if not expected:
        return False
    for name, digest in expected.items():
        p = folder / name
        if not p.is_file() or sha256(p) != digest:
            return False
    return True


def from_packages(size, entry, allow_install):
    """Install the size's PyPI packages, join split files, check every hash, return the folder."""
    target = CACHE / size
    expected = entry.get("files", {})
    marker = target / ".verified"
    if marker.exists() and verified(target, expected):
        return target
    if not entry.get("published") or not entry.get("packages"):
        return None
    specs = [f"{p['name']}=={p['version']}" for p in entry["packages"]]
    missing = [p for p in entry["packages"] if importlib.util.find_spec(p["module"]) is None]
    if missing and not (allow_install and pip_install(*specs)):
        return None
    target.mkdir(parents=True, exist_ok=True)
    parts = {}
    for p in entry["packages"]:
        mod = importlib.import_module(p["module"])
        data = Path(mod.__file__).resolve().parent / "data"
        for f in sorted(data.iterdir()):
            parts.setdefault(f.name.split(".part")[0], []).append(f)
    for name, chunks in parts.items():
        chunks.sort(key=lambda f: int(f.name.rsplit(".part", 1)[1]) if ".part" in f.name else 0)
        with open(target / name, "wb") as out:
            for c in chunks:
                out.write(c.read_bytes())
    if not verified(target, expected):
        log("a model file failed its SHA-256 check; refusing to use it")
        for f in target.iterdir():
            f.unlink()
        return None
    marker.write_text("ok")
    return target


def load_model(args):
    from faster_whisper import WhisperModel
    entry = REGISTRY["models"].get(args.size)
    if entry is None:
        sys.exit(f"unknown --size {args.size}; choose from {', '.join(REGISTRY['models'])}")
    tried = []
    if args.model_dir:
        tried.append("--model-dir")
        return WhisperModel(args.model_dir, device="cpu", compute_type="int8"), "your folder"
    folder = from_packages(args.size, entry, not args.no_install)
    tried.append("SOLIDS FOR YOU packages")
    if folder:
        return WhisperModel(str(folder), device="cpu", compute_type="int8"), "SOLIDS FOR YOU package (verified)"
    try:
        tried.append("faster-whisper download")
        return WhisperModel(args.size, device="cpu", compute_type="int8"), "faster-whisper download"
    except Exception as e:  # network blocked, no disk, etc.
        log(f"faster-whisper download failed: {str(e).splitlines()[0][:160]}")
    print(FALLBACK)
    sys.exit(3)


def load_audio(path):
    """16 kHz mono float32 samples: ffmpeg if present, else faster-whisper's decoder."""
    import shutil
    import numpy as np
    if shutil.which("ffmpeg"):
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "f32le",
                            "-ac", "1", "-ar", "16000", "-"], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return np.frombuffer(r.stdout, dtype=np.float32).copy()
        log("ffmpeg could not read the file; trying the built-in decoder")
    from faster_whisper import decode_audio
    try:
        return decode_audio(str(path), sampling_rate=16000)
    except Exception as e:
        sys.exit(f"could not read the audio in {path}: {str(e).splitlines()[0][:200]}")


def tighten_words(segs, audio, sr=16000, frame=0.02):
    """Whisper often stretches a word across the silence before or after it. Trim each
    word's start and end to the loud frames inside it, so real pauses become visible."""
    import numpy as np
    n = int(sr * frame)
    if audio.size < n * 4:
        return
    frames = audio[: audio.size // n * n].reshape(-1, n)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1))
    floor, loud = np.percentile(rms, 10), np.percentile(rms, 90)
    if loud <= floor:
        return
    voiced = rms > floor + 0.1 * (loud - floor)
    for s in segs:
        for w in s["words"]:
            a, b = int(w["start"] / frame), max(int(w["start"] / frame) + 1, int(w["end"] / frame))
            idx = np.nonzero(voiced[a:b])[0]
            if idx.size:
                start, end = (a + idx[0]) * frame, (a + idx[-1] + 1) * frame
                if end - start >= 0.05:
                    w["start"], w["end"] = round(start, 3), round(min(end, w["end"]), 3)


def to_cues(segs, gap=0.5, max_s=7.0, max_chars=84):
    """Re-cut Whisper's segments into caption cues using word timings: a new cue at
    every pause longer than `gap`, after sentence-ending punctuation once a cue has
    some length, or when a cue gets too long. Pauses and restarts then show up as
    separate cues, which the editing, chapter and retention tools rely on."""
    words = [w for s in segs for w in s["words"]]
    if not words:
        return segs
    cues, cur = [], []
    for w in words:
        if cur:
            text_len = len(" ".join(x["word"] for x in cur))
            if (w["start"] - cur[-1]["end"] > gap or w["end"] - cur[0]["start"] > max_s
                    or text_len > max_chars
                    or (cur[-1]["word"][-1:] in ".?!" and w["end"] - cur[0]["start"] > 1.0)):
                cues.append(cur)
                cur = []
        cur.append(w)
    if cur:
        cues.append(cur)
    return [{"start": c[0]["start"], "end": c[-1]["end"],
             "text": " ".join(x["word"] for x in c).replace(" ,", ",").strip(), "words": c} for c in cues]


def ts(t, sep):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--size", default=REGISTRY.get("default", "base"))
    ap.add_argument("--language", default="auto")
    ap.add_argument("--prompt")
    ap.add_argument("--translate", action="store_true", help="translate the speech into English")
    ap.add_argument("--out-dir")
    ap.add_argument("--model-dir")
    ap.add_argument("--no-install", action="store_true")
    args = ap.parse_args()
    src = Path(args.file)
    if not src.is_file():
        sys.exit(f"not a file: {src}")
    if not ensure_engine(not args.no_install):
        print("The transcription engine (faster-whisper) couldn't be installed here.\n" + FALLBACK)
        sys.exit(3)
    model, how = load_model(args)
    log(f"model: {args.size} ({how})")
    audio = load_audio(src)
    if audio.size == 0:
        sys.exit("the file has no audio")
    segments, info = model.transcribe(
        audio, language=None if args.language == "auto" else args.language,
        task="translate" if args.translate else "transcribe", initial_prompt=args.prompt,
        word_timestamps=True, vad_filter=True)
    segs = []
    for s in segments:
        segs.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                     "words": [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip(),
                                "probability": round(w.probability, 3)} for w in (s.words or [])]})
    tighten_words(segs, audio)
    segs = to_cues(segs)
    out_dir = Path(args.out_dir) if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / src.stem
    text = "\n".join(s["text"] for s in segs)
    Path(f"{stem}.txt").write_text(text + "\n", encoding="utf-8")
    Path(f"{stem}.srt").write_text("".join(
        f"{i}\n{ts(s['start'], ',')} --> {ts(s['end'], ',')}\n{s['text']}\n\n" for i, s in enumerate(segs, 1)),
        encoding="utf-8")
    Path(f"{stem}.vtt").write_text("WEBVTT\n\n" + "".join(
        f"{ts(s['start'], '.')} --> {ts(s['end'], '.')}\n{s['text']}\n\n" for s in segs), encoding="utf-8")
    Path(f"{stem}.json").write_text(json.dumps(
        {"language": info.language, "language_probability": round(info.language_probability, 3),
         "duration": round(info.duration, 3), "model": args.size, "segments": segs},
        ensure_ascii=False, indent=1), encoding="utf-8")
    low = [w for s in segs for w in s["words"] if w["probability"] < 0.5]
    print(json.dumps({"language": info.language, "duration_s": round(info.duration, 1),
                      "segments": len(segs), "unsure_words": len(low),
                      "files": [f"{stem}.{e}" for e in ("txt", "srt", "vtt", "json")]}))
    print("\n" + text)


if __name__ == "__main__":
    main()
