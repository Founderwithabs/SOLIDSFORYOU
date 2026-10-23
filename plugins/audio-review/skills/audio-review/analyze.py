#!/usr/bin/env python3
"""Measure an audio file the way an audio designer listens to it.

Claude cannot hear audio directly, so this script turns a file into the
evidence a designer relies on: loudness and dynamics, frequency balance,
stereo image, noise and artifacts, plus spectrogram and waveform pictures.
review.py (or the audio-review Claude Code skill) hands that evidence to
Claude to judge.

Usage:
    python plugins/audio-review/skills/audio-review/analyze.py song.wav --out out/song
    python plugins/audio-review/skills/audio-review/analyze.py song.mp3 --out out/song --no-images

Needs ffmpeg/ffprobe on PATH and numpy.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

# Analysis sample rate cap. Higher-rate files are resampled down; 48 kHz still
# shows everything up to 24 kHz, which covers lossy-codec cutoffs and "air".
MAX_ANALYSIS_RATE = 48000
SILENCE_DBFS = -60.0
CHUNK_SAMPLES = 1 << 20  # about 22 s at 48 kHz per chunk of measurements
EPS = 1e-12

# Frequency bands named the way designers talk about them.
BANDS = [
    ("sub", 20, 60),
    ("bass", 60, 250),
    ("low_mid", 250, 500),
    ("mid", 500, 2000),
    ("high_mid", 2000, 4000),
    ("presence", 4000, 6000),
    ("brilliance", 6000, 12000),
    ("air", 12000, 20000),
]

# Common delivery targets: integrated loudness (LUFS) and max true peak (dBTP).
DELIVERY_TARGETS = {
    "spotify": {"lufs": -14.0, "true_peak": -1.0, "tolerance": 1.0},
    "apple_music": {"lufs": -16.0, "true_peak": -1.0, "tolerance": 1.0},
    "youtube": {"lufs": -14.0, "true_peak": -1.0, "tolerance": 1.0},
    "podcast": {"lufs": -16.0, "true_peak": -1.0, "tolerance": 1.0},
    "broadcast_ebu_r128": {"lufs": -23.0, "true_peak": -1.0, "tolerance": 0.5},
    "broadcast_atsc_a85": {"lufs": -24.0, "true_peak": -2.0, "tolerance": 2.0},
    "game_console": {"lufs": -24.0, "true_peak": -1.0, "tolerance": 2.0},
    "game_mobile": {"lufs": -18.0, "true_peak": -1.0, "tolerance": 2.0},
    "social_ads": {"lufs": -14.0, "true_peak": -1.0, "tolerance": 1.0},
}


def db(x: float | np.ndarray) -> float | np.ndarray:
    """Amplitude to dB, floored at -120 dB."""
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-6))


def power_db(x: float | np.ndarray) -> float | np.ndarray:
    return 10.0 * np.log10(np.maximum(x, EPS))


def r(x: float, nd: int = 2) -> float | None:
    """Round for JSON; map non-finite values to None."""
    x = float(x)
    return round(x, nd) if np.isfinite(x) else None


# --------------------------------------------------------------------------
# Decoding and file info
# --------------------------------------------------------------------------

def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", "-select_streams", "a:0", str(path)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(out.stdout)
    if not info.get("streams"):
        raise ValueError(f"No audio stream found in {path}")
    s = info["streams"][0]
    fmt = info.get("format", {})
    bit_rate = s.get("bit_rate") or fmt.get("bit_rate")
    return {
        "file": path.name,
        "codec": s.get("codec_name"),
        "sample_rate": int(s["sample_rate"]),
        "channels": int(s["channels"]),
        "channel_layout": s.get("channel_layout"),
        "bit_depth": s.get("bits_per_raw_sample") or s.get("bits_per_sample") or None,
        "bit_rate_kbps": round(int(bit_rate) / 1000) if bit_rate else None,
        "duration_s": r(float(fmt.get("duration") or s.get("duration") or 0), 3),
    }


def decode(path: Path, rate: int, channels: int, duration_s: float | None = None) -> np.ndarray:
    """Decode to float32, shape (channels, samples). Surround folds to stereo.

    The result is a view on ffmpeg's output buffer (no copy), and the
    measurements below work through it in chunks, so memory stays close to
    one copy of the decoded audio even for hour-long podcasts.
    """
    ch = 1 if channels == 1 else 2
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn",
         "-ac", str(ch), "-ar", str(rate), "-f", "f32le", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    # Read straight into one growing buffer instead of letting subprocess
    # collect pieces and join them (which briefly holds two copies).
    expected = int((duration_s or 0) * rate * ch * 4 * 1.01) + (1 << 20)
    buf = bytearray(expected)
    view, filled = memoryview(buf), 0
    while True:
        if filled == len(buf):
            view.release()
            buf.extend(bytes(len(buf)))  # double the capacity
            view = memoryview(buf)
        got = proc.stdout.readinto(view[filled:])
        if not got:
            break
        filled += got
    view.release()
    err = proc.stderr.read()
    if proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, "ffmpeg", stderr=err)
    usable = filled - filled % (4 * ch)
    del buf[usable:]
    return np.frombuffer(buf, dtype="<f4").reshape(-1, ch).T


def chunks(n: int, size: int):
    """(start, end) pairs covering n samples, size samples at a time."""
    for start in range(0, n, size):
        yield start, min(start + size, n)


# --------------------------------------------------------------------------
# Loudness (EBU R128 via ffmpeg, which implements BS.1770 exactly)
# --------------------------------------------------------------------------

def loudness(path: Path) -> dict:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-v", "verbose", "-i", str(path), "-vn",
         "-af", "ebur128=peak=true:framelog=verbose", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    log = proc.stderr

    def grab(label: str) -> float | None:
        m = re.findall(rf"{label}:\s+(-?[\d.]+|-inf)", log)
        if not m or m[-1] == "-inf":
            return None
        return float(m[-1])

    # Short-term (3 s) loudness over time, sampled once per second.
    timeline = []
    for t, s in re.findall(r"t:\s*([\d.]+)\s+TARGET.*?\bS:\s*(-?[\d.]+|-inf)", log):
        t = float(t)
        if s != "-inf" and (not timeline or t - timeline[-1][0] >= 1.0):
            timeline.append((t, float(s)))
    st = np.array([v for _, v in timeline]) if timeline else np.array([])
    st = st[st > -70]

    return {
        "integrated_lufs": grab("I"),
        "loudness_range_lu": grab("LRA"),
        "true_peak_dbtp": grab("Peak"),
        "short_term_max_lufs": r(st.max()) if st.size else None,
        "short_term_p10_lufs": r(np.percentile(st, 10)) if st.size else None,
        "short_term_p90_lufs": r(np.percentile(st, 90)) if st.size else None,
        "short_term_timeline": [[r(t, 1), r(v, 1)] for t, v in timeline],
    }


def delivery_check(lufs: float | None, tp: float | None) -> dict:
    if lufs is None:
        return {}
    result = {}
    for name, t in DELIVERY_TARGETS.items():
        diff = lufs - t["lufs"]
        result[name] = {
            "target_lufs": t["lufs"],
            "offset_lu": r(diff, 1),
            "loudness_ok": abs(diff) <= t["tolerance"],
            "true_peak_ok": tp is not None and tp <= t["true_peak"],
        }
    return result


# --------------------------------------------------------------------------
# Level, dynamics, noise and artifacts
# --------------------------------------------------------------------------

def frame_rms(audio: np.ndarray, size: int) -> np.ndarray:
    """RMS per window across all channels (power-summed, so out-of-phase
    channels don't cancel the way an L+R fold would)."""
    n = audio.shape[1] // size
    if n == 0:
        return np.array([np.sqrt(np.mean(np.square(audio, dtype=np.float64)) + EPS)])
    per_block = max(1, CHUNK_SAMPLES // size)
    out = []
    for f0 in range(0, n, per_block):
        f1 = min(f0 + per_block, n)
        frames = audio[:, f0 * size : f1 * size].reshape(audio.shape[0], f1 - f0, size)
        out.append(np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=(0, 2)) + EPS))
    return np.concatenate(out)


def levels(audio: np.ndarray, rate: int) -> dict:
    nch, n = audio.shape
    peak, sq_sum = 0.0, 0.0
    ch_sum = np.zeros(nch)
    clipped_runs = 0
    click_times: list[float] = []
    for s0, s1 in chunks(n, CHUNK_SAMPLES):
        block = audio[:, s0:s1]
        peak = max(peak, float(np.max(np.abs(block))))
        sq_sum += float(np.sum(np.square(block, dtype=np.float64)))
        ch_sum += block.sum(axis=1, dtype=np.float64)

        # Clipping: runs of 3+ consecutive samples pinned at full scale. Look
        # one sample back and two ahead so runs across chunk edges count once.
        lo = max(s0 - 1, 0)
        hot = np.abs(audio[:, lo : min(s1 + 2, n)]) >= 0.999
        first = s0 - lo
        for h in hot:
            run3 = h[:-2] & h[1:-1] & h[2:]
            prev = np.r_[False, h[:-1]][: len(run3)]
            clipped_runs += int(np.count_nonzero((run3 & ~prev)[first : first + (s1 - s0)]))

        # Clicks/pops: second-difference outliers far beyond the local spread
        # (median taken per chunk, so a loud section doesn't hide a click in a
        # quiet one).
        seg = audio[:, lo : min(s1 + 1, n)]
        if seg.shape[1] > 2:
            d2 = np.abs(np.diff(seg, n=2, axis=1)).max(axis=0)
            mad = np.median(d2) + EPS
            for idx in np.flatnonzero((d2 > 40 * mad) & (d2 > 0.1)):
                t = (lo + idx + 1) / rate
                if not click_times or t - click_times[-1] > 0.05:
                    click_times.append(t)
    rms = np.sqrt(sq_sum / max(audio.size, 1))

    # Leading/trailing silence and the noise floor, from 50 ms windows.
    win = int(0.05 * rate)
    fr_db = db(frame_rms(audio, win))
    loud = np.flatnonzero(fr_db > SILENCE_DBFS)
    lead = loud[0] * 0.05 if loud.size else len(fr_db) * 0.05
    trail = (len(fr_db) - 1 - loud[-1]) * 0.05 if loud.size else 0.0
    active = fr_db[fr_db > -100]  # ignore digital silence
    noise_floor = np.percentile(active, 5) if active.size else -120.0
    program = np.percentile(active, 95) if active.size else -120.0

    # Dynamics: how much the 400 ms level swings once quiet gaps are removed.
    fr400 = db(frame_rms(audio, int(0.4 * rate)))
    fr400 = fr400[fr400 > SILENCE_DBFS]
    macro_dr = np.percentile(fr400, 95) - np.percentile(fr400, 10) if fr400.size else 0.0

    return {
        "sample_peak_dbfs": r(db(peak)),
        "rms_dbfs": r(db(rms)),
        "crest_factor_db": r(db(peak) - db(rms)),
        "macro_dynamics_db": r(macro_dr),
        "clipped_runs": clipped_runs,
        "dc_offset": [r(float(x / max(n, 1)), 5) for x in ch_sum],
        "noise_floor_dbfs": r(noise_floor),
        "signal_to_noise_db": r(program - noise_floor),
        "leading_silence_s": r(lead),
        "trailing_silence_s": r(trail),
        "possible_clicks": len(click_times),
        "possible_click_times_s": [r(t, 2) for t in click_times[:20]],
    }


# --------------------------------------------------------------------------
# Spectrum: tonal balance, resonances, hum, sibilance, bandwidth
# --------------------------------------------------------------------------

def avg_spectrum(audio: np.ndarray, rate: int, weights=None, nfft: int = 8192) -> tuple[np.ndarray, np.ndarray]:
    """Welch-style average power spectrum over non-silent frames.

    audio is (channels, samples) or a 1-D signal. weights mixes the channels
    frame by frame (e.g. [0.5, 0.5] for mid, [0.5, -0.5] for side), so no
    full-length mixed copy is ever made.
    """
    if audio.ndim == 1:
        audio = audio[np.newaxis, :]
    w = np.asarray(weights if weights is not None else [1.0] * audio.shape[0], dtype=np.float64)
    n = audio.shape[1]
    hop = nfft // 2
    window = np.hanning(nfft)
    total, count = np.zeros(nfft // 2 + 1), 0
    for start in range(0, max(n - nfft, 1), hop):
        seg = w @ audio[:, start : start + nfft]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        if db(np.sqrt(np.mean(seg ** 2))) > SILENCE_DBFS:
            total += np.abs(np.fft.rfft(seg * window)) ** 2
            count += 1
    return np.fft.rfftfreq(nfft, 1 / rate), total / max(count, 1)


def band_power(freqs: np.ndarray, psd: np.ndarray, lo: float, hi: float) -> float:
    mask = (freqs >= lo) & (freqs < hi)
    return float(psd[mask].sum()) if mask.any() else 0.0


def smooth_octave(freqs: np.ndarray, spec_db: np.ndarray, fraction: float) -> np.ndarray:
    """Smooth a dB spectrum over a +/- fraction-of-an-octave window."""
    out = np.empty_like(spec_db)
    k = 2 ** (fraction / 2)
    for i, f in enumerate(freqs):
        if f <= 0:
            out[i] = spec_db[i]
            continue
        lo, hi = np.searchsorted(freqs, [f / k, f * k])
        out[i] = spec_db[lo : max(hi, lo + 1)].mean()
    return out


def spectrum(audio: np.ndarray, rate: int) -> dict:
    # Average the channels' power spectra rather than analysing L+R.
    spectra = [avg_spectrum(ch, rate) for ch in audio]  # rows are views
    freqs = spectra[0][0]
    psd = np.mean([p for _, p in spectra], axis=0)
    total = psd[(freqs >= 20) & (freqs <= 20000)].sum() + EPS

    bands = {
        name: r(power_db(band_power(freqs, psd, lo, hi) / total), 1)
        for name, lo, hi in BANDS
        if lo < rate / 2
    }

    centroid = float((freqs * psd).sum() / (psd.sum() + EPS))
    spec_db = power_db(psd)

    # Tilt in dB/octave between 100 Hz and 10 kHz. Most finished music sits
    # near -3 to -6 dB/oct; flatter reads bright, steeper reads dark.
    sel = (freqs >= 100) & (freqs <= min(10000, rate / 2))
    tilt = np.polyfit(np.log2(freqs[sel]), spec_db[sel], 1)[0] if sel.sum() > 2 else 0.0

    # Effective bandwidth: highest frequency still within 50 dB of the
    # 1-10 kHz median. A hard edge near 16-20 kHz suggests lossy encoding or
    # a low-sample-rate source.
    ref = np.median(spec_db[(freqs >= 1000) & (freqs <= 10000)])
    alive = np.flatnonzero((spec_db > ref - 50) & (freqs > 1000))
    bandwidth = float(freqs[alive[-1]]) if alive.size else 0.0

    # Resonances: narrow peaks standing above a 1/3-octave smoothed baseline.
    smooth = smooth_octave(freqs, spec_db, 1 / 3)
    excess = spec_db - smooth
    region = (freqs >= 80) & (freqs <= 10000)
    peaks = []
    for i in np.flatnonzero(region):
        if 0 < i < len(excess) - 1 and excess[i] > 6 and excess[i] >= excess[i - 1] and excess[i] >= excess[i + 1]:
            peaks.append((float(excess[i]), float(freqs[i])))
    peaks.sort(reverse=True)
    resonances = [{"freq_hz": round(f), "above_baseline_db": r(e, 1)} for e, f in peaks[:6]]

    # Mains hum: 50/60 Hz fundamentals and harmonics poking above neighbours.
    hum = {}
    for base in (50, 60):
        prominences = []
        for h in range(1, 5):
            f = base * h
            i = int(np.argmin(np.abs(freqs - f)))
            neigh = np.r_[spec_db[max(i - 12, 0) : max(i - 3, 0)], spec_db[i + 4 : i + 13]]
            prominences.append(spec_db[i] - np.median(neigh) if neigh.size else 0.0)
        hum[f"{base}hz_prominence_db"] = r(max(prominences), 1)

    # Sibilance proxy: 5-9 kHz energy against 1-4 kHz.
    sib = power_db(band_power(freqs, psd, 5000, 9000) / (band_power(freqs, psd, 1000, 4000) + EPS))

    return {
        "band_balance_db_rel_total": bands,
        "spectral_centroid_hz": round(centroid),
        "spectral_tilt_db_per_octave": r(tilt),
        "effective_bandwidth_hz": round(bandwidth),
        "narrow_resonances": resonances,
        "hum": hum,
        "sibilance_ratio_db": r(sib, 1),
    }


# --------------------------------------------------------------------------
# Stereo image
# --------------------------------------------------------------------------

def stereo(audio: np.ndarray) -> dict:
    if audio.shape[0] < 2:
        return {"mono": True}
    # Accumulate sums chunk by chunk; mid and side energies follow from them:
    # mid^2 = (L^2 + R^2 + 2LR) / 4, side^2 = (L^2 + R^2 - 2LR) / 4.
    n = audio.shape[1]
    sl = sr = sll = srr = slr = 0.0
    for s0, s1 in chunks(n, CHUNK_SAMPLES):
        left = audio[0, s0:s1].astype(np.float64)
        right = audio[1, s0:s1].astype(np.float64)
        sl += left.sum(); sr += right.sum()
        sll += left @ left; srr += right @ right; slr += left @ right
    ll, rr, lr = sll / n, srr / n, slr / n
    var_l, var_r = ll - (sl / n) ** 2, rr - (sr / n) ** 2
    cov = lr - (sl / n) * (sr / n)
    corr = cov / np.sqrt(var_l * var_r) if var_l > EPS and var_r > EPS else 1.0
    mid2 = max((ll + rr + 2 * lr) / 4, 0.0)
    side2 = max((ll + rr - 2 * lr) / 4, 0.0)
    side_ratio = db(np.sqrt(side2)) - db(np.sqrt(mid2))
    lr_balance = db(np.sqrt(ll)) - db(np.sqrt(rr))
    # Level lost when folded to mono, relative to the stereo average.
    mono_loss = db(np.sqrt(mid2)) - db(np.sqrt((ll + rr) / 2))
    return {
        "mono": False,
        "correlation": r(float(np.clip(corr, -1, 1))),
        "side_to_mid_db": r(np.clip(side_ratio, -120, 120), 1),
        "left_right_balance_db": r(lr_balance, 1),
        "mono_fold_loss_db": r(mono_loss, 1),
    }


def stereo_low_end(audio: np.ndarray, rate: int) -> float | None:
    """Side/mid energy below 150 Hz; bass should usually sit close to mono."""
    if audio.shape[0] < 2:
        return None
    f, pm = avg_spectrum(audio[:2], rate, weights=[0.5, 0.5])
    _, ps = avg_spectrum(audio[:2], rate, weights=[0.5, -0.5])
    m = band_power(f, pm, 20, 150)
    s = band_power(f, ps, 20, 150)
    return r(np.clip(power_db((s + EPS) / (m + EPS)), -120, 120), 1)


# --------------------------------------------------------------------------
# Timeline: how the piece develops section by section
# --------------------------------------------------------------------------

def sections(audio: np.ndarray, rate: int, count: int = 12) -> list[dict]:
    length = audio.shape[1]
    size = max(length // count, rate)
    out = []
    for start in range(0, length, size):
        seg = audio[:, start : start + size]
        n = seg.shape[1]
        if n < rate // 4:
            break
        nfft = min(8192, 1 << (n.bit_length() - 1))
        per_ch = [avg_spectrum(c, rate, nfft=nfft) for c in seg]
        fr, spec = per_ch[0][0], np.mean([p for _, p in per_ch], axis=0)
        out.append({
            "start_s": r(start / rate, 1),
            "end_s": r((start + n) / rate, 1),
            "rms_dbfs": r(db(np.sqrt(np.mean(np.square(seg, dtype=np.float64))))),
            "peak_dbfs": r(db(np.max(np.abs(seg)))),
            "centroid_hz": round(float((fr * spec).sum() / (spec.sum() + EPS))),
        })
    return out


# --------------------------------------------------------------------------
# Pictures for Claude to look at
# --------------------------------------------------------------------------

def render_images(path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = {
        "spectrogram": (out_dir / "spectrogram.png",
                        "showspectrumpic=s=1600x800:legend=1:scale=log:fscale=log:color=intensity:drange=100"),
        "spectrogram_linear": (out_dir / "spectrogram_linear.png",
                               "showspectrumpic=s=1600x600:legend=1:scale=log:fscale=lin:drange=100"),
        "waveform": (out_dir / "waveform.png",
                     "[0:a]showwavespic=s=1600x400:split_channels=1:scale=lin:draw=full:colors=0x4fa3ff|0xffa64f[w];"
                     "color=c=0x101418:s=1600x400[bg];[bg][w]overlay=format=auto"),
    }
    made = {}
    for name, (target, graph) in jobs.items():
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(path), "-lavfi", graph, "-frames:v", "1", str(target)],
            capture_output=True, text=True,
        )
        if proc.returncode == 0 and target.exists():
            made[name] = str(target)
        else:
            print(f"warning: could not render {name}: {proc.stderr.strip()[:200]}", file=sys.stderr)
    return made


# --------------------------------------------------------------------------
# Plain-language flags a designer would raise first
# --------------------------------------------------------------------------

def flags(report: dict) -> list[str]:
    f = []
    L, lv, sp, st = report["loudness"], report["levels"], report["spectrum"], report["stereo"]
    tp = L.get("true_peak_dbtp")
    if tp is not None and tp > -1.0:
        f.append(f"True peak {tp} dBTP is above -1 dBTP: risk of intersample clipping after lossy encoding.")
    if lv["clipped_runs"]:
        f.append(f"{lv['clipped_runs']} runs of clipped samples (3+ samples at full scale).")
    if L.get("loudness_range_lu") is not None and L["loudness_range_lu"] < 3:
        f.append(f"Loudness range {L['loudness_range_lu']} LU: very little macro-dynamics, likely heavily limited.")
    if lv["crest_factor_db"] is not None and lv["crest_factor_db"] < 8:
        f.append(f"Crest factor {lv['crest_factor_db']} dB: transients likely squashed.")
    # A floor close to the programme level means dense material, not hiss.
    if lv["noise_floor_dbfs"] is not None and lv["noise_floor_dbfs"] > -55 and 15 < lv["signal_to_noise_db"] < 45:
        f.append(f"Noise floor around {lv['noise_floor_dbfs']} dBFS: audible hiss or room noise in quiet parts.")
    if any(abs(x or 0) > 0.005 for x in lv["dc_offset"]):
        f.append(f"DC offset present {lv['dc_offset']}.")
    if lv["possible_clicks"]:
        f.append(f"{lv['possible_clicks']} possible clicks/pops (heuristic) near {lv['possible_click_times_s'][:5]} s.")
    for base in (50, 60):
        p = sp["hum"].get(f"{base}hz_prominence_db") or 0
        if p > 12:
            f.append(f"Possible {base} Hz mains hum ({p} dB above neighbouring bins).")
    bw = sp["effective_bandwidth_hz"]
    nyq = report["file"]["sample_rate"] / 2
    if bw and bw < min(nyq, 20000) - 1500 and bw < 17500:
        f.append(f"Content stops near {bw} Hz: likely lossy encode, low-rate source, or heavy low-pass.")
    # Pink noise sits near -3.7 dB here; finished vocals and mixes usually well below.
    if sp["sibilance_ratio_db"] is not None and sp["sibilance_ratio_db"] > -3:
        f.append(f"Strong 5-9 kHz energy (sibilance ratio {sp['sibilance_ratio_db']} dB): check esses/harshness.")
    for res in sp["narrow_resonances"][:3]:
        if res["above_baseline_db"] and res["above_baseline_db"] > 10:
            f.append(f"Narrow resonance at {res['freq_hz']} Hz (+{res['above_baseline_db']} dB over local average).")
    if not st.get("mono"):
        if st["correlation"] is not None and st["correlation"] < 0:
            f.append(f"Negative L/R correlation ({st['correlation']}): phase problems, will collapse in mono.")
        if st["mono_fold_loss_db"] is not None and st["mono_fold_loss_db"] < -3:
            f.append(f"Loses {st['mono_fold_loss_db']} dB when folded to mono.")
        if st.get("low_end_side_to_mid_db") is not None and st["low_end_side_to_mid_db"] > -10:
            f.append(f"Wide low end (side/mid below 150 Hz {st['low_end_side_to_mid_db']} dB): bass not centred.")
        if abs(st["left_right_balance_db"] or 0) > 1.5:
            f.append(f"Left/right level imbalance of {st['left_right_balance_db']} dB.")
    if lv["leading_silence_s"] and lv["leading_silence_s"] > 1.0:
        f.append(f"{lv['leading_silence_s']} s of silence before the audio starts.")
    if lv["trailing_silence_s"] and lv["trailing_silence_s"] > 3.0:
        f.append(f"{lv['trailing_silence_s']} s of silence at the end.")
    return f


# --------------------------------------------------------------------------

def analyze(path: str | Path, out_dir: str | Path | None = None, images: bool = True) -> dict:
    path = Path(path)
    info = probe(path)
    rate = min(info["sample_rate"], MAX_ANALYSIS_RATE)
    audio = decode(path, rate, info["channels"], info["duration_s"])
    if audio.size == 0:
        raise ValueError(f"{path} decoded to no samples")

    st = stereo(audio)
    st["low_end_side_to_mid_db"] = stereo_low_end(audio, rate)

    L = loudness(path)
    report = {
        "file": info,
        "loudness": L,
        "delivery_targets": delivery_check(L["integrated_lufs"], L["true_peak_dbtp"]),
        "levels": levels(audio, rate),
        "spectrum": spectrum(audio, rate),
        "stereo": st,
        "sections": sections(audio, rate),
    }
    report["flags"] = flags(report)

    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        report["images"] = render_images(path, out) if images else {}
        (out / "metrics.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", help="audio or video file (anything ffmpeg can decode)")
    ap.add_argument("--out", help="directory for metrics.json and images (default: print JSON only)")
    ap.add_argument("--no-images", action="store_true", help="skip spectrogram/waveform rendering")
    args = ap.parse_args()

    report = analyze(args.audio, args.out, images=not args.no_images)
    summary = {k: v for k, v in report.items() if k != "loudness"}
    summary["loudness"] = {k: v for k, v in report["loudness"].items() if k != "short_term_timeline"}
    print(json.dumps(summary, indent=2))
    if args.out:
        print(f"\nWrote {Path(args.out) / 'metrics.json'}", file=sys.stderr)


if __name__ == "__main__":
    main()
