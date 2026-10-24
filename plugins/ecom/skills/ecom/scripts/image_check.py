#!/usr/bin/env python3
"""Measure product images, so image reviews start from facts, not impressions.

Usage:
  python3 image_check.py IMAGE [IMAGE ...] --out OUT_DIR [--main IMAGE]
        [--min-side 1000] [--white-threshold 250]

For every image: size, aspect ratio, file size and format; the background
colour (the most common border colour); how much of the border is pure white
(RGB 255) or near white; and how much of the frame the product fills (the
bounding box of pixels that differ from the background). --main marks the main
image, which is checked against white-background and fill rules.
It also writes OUT_DIR/thumbs_<size>.png: all images side by side at phone
search-result sizes (100, 160 and 300 px), to judge what a shopper sees.
Needs ffmpeg and ffprobe. Standard library only.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ANALYSE_SIDE = 600  # analysed at this size with nearest-neighbour scaling, so pure white stays pure
BG_TOLERANCE = 16   # a pixel within this of the background colour on every channel counts as background


def run(cmd, binary=False):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"{' '.join(cmd[:3])} failed: {r.stderr.decode(errors='replace')[-400:]}")
    return r.stdout if binary else r.stdout.decode()


def probe(path):
    info = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height,codec_name,pix_fmt", "-of", "json", str(path)]))
    s = (info.get("streams") or [{}])[0]
    if not s.get("width") or not s.get("height"):
        sys.exit(f"{path} isn't an image ffmpeg can read")
    return int(s["width"]), int(s["height"]), s.get("codec_name"), s.get("pix_fmt")


def pixels(path, w, h):
    scale = min(1.0, ANALYSE_SIDE / max(w, h))
    sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
    raw = run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
               f"scale={sw}:{sh}:flags=neighbor,format=rgb24", "-frames:v", "1",
               "-f", "rawvideo", "-"], binary=True)
    if len(raw) < sw * sh * 3:
        sys.exit(f"{path} couldn't be decoded as an image")
    return raw, sw, sh


def analyse(path, white_threshold, min_side):
    w, h, codec, pix_fmt = probe(path)
    raw, sw, sh = pixels(path, w, h)

    def px(x, y):
        i = (y * sw + x) * 3
        return raw[i], raw[i + 1], raw[i + 2]

    border = [(x, 0) for x in range(sw)] + [(x, sh - 1) for x in range(sw)] + \
             [(0, y) for y in range(sh)] + [(sw - 1, y) for y in range(sh)]
    pure = sum(1 for x, y in border if px(x, y) == (255, 255, 255))
    near = sum(1 for x, y in border if min(px(x, y)) >= white_threshold)
    counts = {}
    for x, y in border:
        c = tuple(v // 4 * 4 for v in px(x, y))  # group near-identical colours (JPEG noise)
        counts[c] = counts.get(c, 0) + 1
    bg_key, bg_count = max(counts.items(), key=lambda kv: kv[1])
    bg_pixels = [px(x, y) for x, y in border if tuple(v // 4 * 4 for v in px(x, y)) == bg_key]
    bg = tuple(round(sum(p[i] for p in bg_pixels) / len(bg_pixels)) for i in range(3))
    bg_share = bg_count / len(border) * 100

    xs, ys = [], []
    for y in range(sh):
        row = raw[y * sw * 3:(y + 1) * sw * 3]
        for x in range(sw):
            r, g, b = row[x * 3], row[x * 3 + 1], row[x * 3 + 2]
            if max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2])) > BG_TOLERANCE:
                xs.append(x)
                ys.append(y)
    if xs:
        bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        fill_long = max(bw / sw, bh / sh) * 100
        fill_area = bw * bh / (sw * sh) * 100
    else:
        fill_long = fill_area = 0.0
    return {
        "file": str(path), "width": w, "height": h, "aspect": round(w / h, 3),
        "format": codec, "pixel_format": pix_fmt, "kb": round(Path(path).stat().st_size / 1024, 1),
        "background": "#%02X%02X%02X" % bg,
        "background_border_share_pct": round(bg_share, 1),
        "border_pure_white_pct": round(pure / len(border) * 100, 1),
        "border_near_white_pct": round(near / len(border) * 100, 1),
        "product_fill_longest_side_pct": round(fill_long, 1),
        "product_box_area_pct": round(fill_area, 1),
        "meets_min_side": max(w, h) >= min_side,
    }


def thumbs(paths, out_dir):
    made = []
    for size in (100, 160, 300):
        inputs = []
        for p in paths:
            inputs += ["-i", str(p)]
        chains = [f"[{i}:v]scale={size}:{size}:force_original_aspect_ratio=decrease,"
                  f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=#EAEDED,setsar=1[t{i}]"
                  for i in range(len(paths))]
        if len(paths) > 1:
            chains.append("".join(f"[t{i}]" for i in range(len(paths)))
                          + f"hstack=inputs={len(paths)}[out]")
            last = "[out]"
        else:
            last = "[t0]"
        out = Path(out_dir) / f"thumbs_{size}.png"
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains),
             "-map", last, "-frames:v", "1", str(out)])
        made.append(out.name)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--main")
    ap.add_argument("--min-side", type=int, default=1000, dest="min_side")
    ap.add_argument("--white-threshold", type=int, default=250, dest="white_threshold")
    args = ap.parse_args()
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("this needs ffmpeg: install it (Mac: brew install ffmpeg; Windows: winget install ffmpeg; "
                 "Linux: sudo apt install ffmpeg), then run it again")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [Path(p) for p in args.images]
    if args.main and Path(args.main) not in paths:
        paths.insert(0, Path(args.main))
    for p in paths:
        if not p.is_file():
            sys.exit(f"not a file: {p}")

    results = [analyse(p, args.white_threshold, args.min_side) for p in paths]
    lines = ["# Image measurements", "",
             "Background = the most common border colour. Product fill = the bounding box of "
             "pixels that differ from it, on the longest side. If the background covers less than "
             "about 60% of the border (busy lifestyle shots), the fill figure means little. Check "
             "these numbers against the marketplace's current image rules; they are measurements, "
             "not a verdict.", "",
             "| Image | Size | Aspect | KB | Background | Border pure white | Border near white | Product fill (longest side) | Long side ≥ "
             f"{args.min_side} |", "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {Path(r['file']).name} | {r['width']}×{r['height']} | {r['aspect']} | {r['kb']} | "
                     f"{r['background']} ({r['background_border_share_pct']}% of border) | "
                     f"{r['border_pure_white_pct']}% | {r['border_near_white_pct']}% | "
                     f"{r['product_fill_longest_side_pct']}% | {'yes' if r['meets_min_side'] else 'NO'} |")
    if args.main:
        m = next(r for r in results if Path(r["file"]) == Path(args.main))
        lines += ["", f"## Main image: {Path(args.main).name}", ""]
        lines.append(f"- Background: {m['border_pure_white_pct']}% of the border is pure white (255, 255, 255)"
                     + ("" if m["border_pure_white_pct"] >= 99 else
                        " — marketplaces that require a pure white main image will see this as not white"))
        lines.append(f"- Product fills {m['product_fill_longest_side_pct']}% of the frame on its longest side")
        lines.append(f"- Long side {max(m['width'], m['height'])} px"
                     + ("" if m["meets_min_side"] else f", below {args.min_side} px"))
    made = thumbs(paths, out_dir)
    lines += ["", "Phone-size previews: " + ", ".join(f"`{n}`" for n in made)
              + ". Look at them: can a shopper tell what it is, and read any text?"]
    (out_dir / "images.json").write_text(json.dumps(results, indent=2))
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
