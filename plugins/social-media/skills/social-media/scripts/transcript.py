#!/usr/bin/env python3
"""Read a timestamped transcript (.srt, .vtt or Whisper .json) into cues.

Shared by chapters.py and retention.py. Adapted from deadair.py in
youtube-agent-skill by Jake Schincariol (MIT; see THIRD_PARTY_NOTICES.md).

  load(path) -> [(start_seconds, end_seconds, text), ...]
"""
import json
import re


def parse_ts(s):
    s = s.strip().replace(",", ".")
    parts = s.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def load(path):
    try:
        raw = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError as e:
        raise SystemExit(f"can't read {path}: {e.strerror}")
    if path.lower().endswith(".json"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise SystemExit(f"{path} isn't valid JSON; give Whisper's .json, an .srt or a .vtt")
        segs = data.get("segments", []) if isinstance(data, dict) else data
        cues = []
        for s in segs if isinstance(segs, list) else []:
            try:
                cues.append((float(s["start"]), float(s["end"]), (s.get("text") or "").strip()))
            except (TypeError, KeyError, ValueError):
                continue  # a segment without times can't be placed
        return cues
    cues, cur = [], None
    for line in raw.splitlines():
        m = re.match(r"\s*(\d[\d:.,]*)\s*-->\s*(\d[\d:.,]*)", line)
        if m:
            try:
                cur = [parse_ts(m.group(1)), parse_ts(m.group(2)), []]
            except ValueError:
                cur = None  # an unreadable timestamp: skip that cue
                continue
            cues.append(cur)
        elif cur is not None and line.strip() and not line.strip().isdigit() \
                and not line.startswith(("WEBVTT", "NOTE")):
            cur[2].append(re.sub(r"<[^>]+>", "", line.strip()))
    return [(a, b, " ".join(t)) for a, b, t in cues if t]
