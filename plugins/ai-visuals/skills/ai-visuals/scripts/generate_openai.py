#!/usr/bin/env python3
"""Generate or edit an image with the OpenAI Images API (optional; needs the founder's key).

Usage:
  python3 generate_openai.py --prompt-file prompt.txt --out out.png
        [--size 1024x1536] [--quality high] [--n 1] [--background transparent]
        [--image product.png [--image style.png ...]] [--mask mask.png]
        [--model gpt-image-1] [--base-url https://api.openai.com/v1]

Reads the key from the OPENAI_API_KEY environment variable only; never pass it
on the command line or write it to a file. Without --image it calls
/images/generations; with --image it calls /images/edits (the images are the
things to edit or the references to use; --mask limits the edit to the mask's
transparent area). Every call costs money on the founder's OpenAI account.

Model names, sizes, quality levels and prices change: check OpenAI's current
image documentation and pass --model, --size and --quality to match.
Writes out.png (and out-2.png ... for --n above 1). Standard library only.
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def multipart(fields, files):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for name, path in files:
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        head = (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                f'filename="{Path(path).name}"\r\nContent-Type: {mime}\r\n\r\n').encode()
        parts.append(head + Path(path).read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt-image-1")
    ap.add_argument("--size", default="auto")
    ap.add_argument("--quality", default="auto")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--background")
    ap.add_argument("--image", action="append", default=[])
    ap.add_argument("--mask")
    ap.add_argument("--base-url", default="https://api.openai.com/v1")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set. Ask the founder to set it in their environment "
                 "(never paste it into the chat), or paste the prompt into the tool by hand.")
    if args.n < 1:
        sys.exit("--n is how many images to make: 1 or more")
    try:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeDecodeError) as e:
        sys.exit(f"can't read the prompt file {args.prompt_file}: {e}")
    if not prompt:
        sys.exit("the prompt file is empty")
    for p in args.image + ([args.mask] if args.mask else []):
        if not Path(p).is_file():
            sys.exit(f"not a file: {p}")

    fields = {"model": args.model, "prompt": prompt, "n": str(args.n),
              "size": args.size, "quality": args.quality}
    if args.background:
        fields["background"] = args.background
    headers = {"Authorization": f"Bearer {key}"}
    if args.image:
        url = args.base_url.rstrip("/") + "/images/edits"
        files = [("image[]" if len(args.image) > 1 else "image", p) for p in args.image]
        if args.mask:
            files.append(("mask", args.mask))
        body, ctype = multipart(fields, files)
    else:
        url = args.base_url.rstrip("/") + "/images/generations"
        payload = dict(fields, n=args.n)
        body, ctype = json.dumps(payload).encode(), "application/json"
    headers["Content-Type"] = ctype

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("error", {}).get("message", detail)
        except (ValueError, AttributeError):
            pass
        sys.exit(f"OpenAI returned {e.code}: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"could not reach {url}: {e.reason}")

    images = data.get("data") or []
    if not images:
        sys.exit(f"no image in the response: {json.dumps(data)[:400]}")
    out = Path(args.out)
    written = []
    for i, item in enumerate(images, 1):
        if not item.get("b64_json"):
            sys.exit("the response had no image data (b64_json); check the model and options")
        path = out if i == 1 else out.with_name(f"{out.stem}-{i}{out.suffix}")
        path.write_bytes(base64.b64decode(item["b64_json"]))
        written.append(str(path))
        if item.get("revised_prompt"):
            print(f"note: the API revised the prompt to: {item['revised_prompt']}")
    print(json.dumps({"endpoint": url.rsplit("/", 1)[-1], "model": args.model, "written": written,
                      "usage": data.get("usage")}))


if __name__ == "__main__":
    main()
