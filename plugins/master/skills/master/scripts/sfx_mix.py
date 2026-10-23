#!/usr/bin/env python3
"""Synthesize sound effects, place them on cue times, mix under the
voiceover and normalize loudness for web and social delivery.

Usage:
  python3 sfx_mix.py --cues cues.json --duration 102.5 --out mix.wav [--vo vo.mp3]

cues.json is a list of {"t": seconds, "sfx": name or file path, "gain": 0..1}:
  [{"t": 0.0, "sfx": "whoosh", "gain": 0.3},
   {"t": 64.5, "sfx": "thump", "gain": 0.35},
   {"t": 87.17, "sfx": "ding", "gain": 0.3}]
Built-in sounds: whoosh, pop, tick, thump, ding, riser.
Gain is relative to the voiceover (about 0.2 to 0.35 sits under a voice).
The mix is normalized to -14 LUFS integrated, -1.5 dBTP true peak.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

SOUNDS = {
    # Band-limited noise burst that swells and falls.
    "whoosh": ("anoisesrc=color=pink:d=0.5:a=0.8,highpass=f=500,lowpass=f=5000,"
               "afade=t=in:d=0.28:curve=exp,afade=t=out:st=0.28:d=0.22,volume=3"),
    # Short pitched blip that drops in pitch.
    "pop": "aevalsrc=0.9*sin(2*PI*(500+1800*exp(-t*40))*t)*exp(-t*30):d=0.15",
    # Tiny click for small UI elements.
    "tick": "aevalsrc=0.8*sin(2*PI*2600*t)*exp(-t*140):d=0.05",
    # Low punch for emphasis ("Ruko!", "Galat").
    "thump": "aevalsrc=1.0*sin(2*PI*(50+90*exp(-t*22))*t)*exp(-t*8):d=0.6",
    # Bell with harmonics for answers and success moments.
    "ding": ("aevalsrc=(0.6*sin(2*PI*1320*t)+0.25*sin(2*PI*2640*t)"
             "+0.1*sin(2*PI*3960*t))*exp(-t*3.5):d=1.4"),
    # Rising tone to build into a reveal.
    "riser": "aevalsrc=0.5*sin(2*PI*(180+500*t*t)*t)*(t/1.2):d=1.2,afade=t=out:st=1.1:d=0.1",
}


TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.5, 11.0


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + r.stderr[-2000:])
    return r


def normalize(src, out):
    """Two-pass loudnorm: measure first, then correct with the measured values.

    One-pass loudnorm guesses as it goes and can miss the target by more than
    1 LU on short or sparse mixes; the second pass lands on it.
    """
    target = f"I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", src,
             "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"])
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    if m["input_i"] in ("-inf", "inf"):
        run(["ffmpeg", "-y", "-i", src, "-ar", "48000", out])  # silent mix: nothing to do
        return
    run(["ffmpeg", "-y", "-i", src, "-af",
         f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
         f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
         f"offset={m['target_offset']}:linear=true",
         "-ar", "48000", out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cues", required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vo")
    args = ap.parse_args()
    with open(args.cues) as f:
        cues = json.load(f)

    tmp = tempfile.mkdtemp(prefix="sfx_")
    paths = {}
    for cue in cues:
        name = cue["sfx"]
        if name in paths:
            continue
        if name in SOUNDS:
            path = os.path.join(tmp, name + ".wav")
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", SOUNDS[name],
                 "-ar", "48000", "-ac", "1", path])
            paths[name] = path
        elif os.path.isfile(name):
            paths[name] = name
        else:
            sys.exit(f"unknown sound '{name}': use {', '.join(SOUNDS)} or a file path")

    inputs, chains, labels = [], [], []
    if args.vo:
        inputs += ["-i", args.vo]
        chains.append("[0:a]aformat=sample_rates=48000:channel_layouts=stereo[vo]")
        labels.append("[vo]")
    for i, cue in enumerate(cues):
        idx = len(inputs) // 2
        inputs += ["-i", paths[cue["sfx"]]]
        ms = max(0, round(float(cue["t"]) * 1000))
        gain = float(cue.get("gain", 0.25))
        chains.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                      f"volume={gain},adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    if not labels:
        sys.exit("nothing to mix")
    chains.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,"
                  f"apad=whole_dur={args.duration},atrim=0:{args.duration}[out]")
    raw = os.path.join(tmp, "raw_mix.wav")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(chains),
         "-map", "[out]", "-ar", "48000", "-c:a", "pcm_f32le", raw])
    normalize(raw, args.out)
    print(f"wrote {args.out}: {len(cues)} effects"
          + (" over the voiceover" if args.vo else "") + f", {args.duration} s")


if __name__ == "__main__":
    main()
