#!/usr/bin/env python3
"""Have Claude review an audio file the way an audio designer would.

Runs analyze.py on the file (and on an optional reference track), then sends
the metrics, spectrograms and waveform to Claude with the audio-designer
rubric in designer_rubric.md. The review is printed and saved as review.md.

Usage:
    python plugins/audio-review/skills/audio-review/review.py mix.wav
    python plugins/audio-review/skills/audio-review/review.py mix.wav --context "podcast intro, Spotify"
    python plugins/audio-review/skills/audio-review/review.py mix.wav --reference pro_master.wav
    python plugins/audio-review/skills/audio-review/review.py mix.wav --dry-run   # no API call

Needs ANTHROPIC_API_KEY (or an `ant auth login` profile), ffmpeg, numpy and
the anthropic package.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import analyze  # noqa: E402

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
MODEL = "claude-opus-5-5"
IMAGE_ORDER = ["spectrogram", "spectrogram_linear", "waveform"]


def image_block(path: str) -> dict:
    data = base64.standard_b64encode(Path(path).read_bytes()).decode("utf-8")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}


def evidence_blocks(label: str, report: dict) -> list[dict]:
    """Metrics plus pictures for one file, labelled so Claude can tell A from B."""
    blocks: list[dict] = [{
        "type": "text",
        "text": f"## {label}: {report['file']['file']}\n\nmetrics.json:\n```json\n"
                + json.dumps({k: v for k, v in report.items() if k != "images"}, indent=1)
                + "\n```",
    }]
    for name in IMAGE_ORDER:
        if name in report.get("images", {}):
            blocks.append({"type": "text", "text": f"{label} - {name}.png:"})
            blocks.append(image_block(report["images"][name]))
    return blocks


def build_request(report: dict, reference: dict | None, context: str | None) -> list[dict]:
    content = evidence_blocks("Track under review", report)
    if reference:
        content += evidence_blocks("Reference track", reference)

    ask = ["Review the track under review using the rubric."]
    if context:
        ask.append(f"Intended use / brief from the client: {context}")
    if reference:
        ask.append("Also compare it against the reference track: say where it falls short or "
                   "goes further (loudness, balance, width, dynamics), and what to change to get closer.")
    content.append({"type": "text", "text": "\n\n".join(ask)})
    return content


def review(audio: str, out_dir: Path, reference: str | None = None,
           context: str | None = None, dry_run: bool = False) -> str:
    report = analyze(audio, out_dir)
    ref_report = analyze(reference, out_dir / "reference") if reference else None
    system = (HERE / "designer_rubric.md").read_text(encoding="utf-8")
    content = build_request(report, ref_report, context)

    if dry_run:
        text_only = [b["text"] if b["type"] == "text" else "[image]" for b in content]
        return "DRY RUN - would send:\n\n" + "\n\n".join(text_only)

    import anthropic

    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=system,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        # If a safety classifier declines, retry on Anthropic's recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": content}],
    ) as stream:
        message = stream.get_final_message()

    if message.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined to review this file: {message.stop_details}")
    text = "".join(b.text for b in message.content if b.type == "text")
    if message.stop_reason == "max_tokens":
        text += "\n\n_(Review was cut off at the token limit.)_"
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", help="audio or video file to review")
    ap.add_argument("--reference", help="a reference track to compare against")
    ap.add_argument("--context", help='intended use or brief, e.g. "podcast for Spotify"')
    ap.add_argument("--out", help="output directory (default: audio_reviews/<file name>)")
    ap.add_argument("--dry-run", action="store_true", help="analyse and show the prompt, but don't call Claude")
    args = ap.parse_args()

    out_dir = Path(args.out) if args.out else Path("audio_reviews") / Path(args.audio).stem
    text = review(args.audio, out_dir, args.reference, args.context, args.dry_run)
    print(text)
    if not args.dry_run:
        (out_dir / "review.md").write_text(text, encoding="utf-8")
        print(f"\nSaved {out_dir / 'review.md'}", file=sys.stderr)


if __name__ == "__main__":
    main()
