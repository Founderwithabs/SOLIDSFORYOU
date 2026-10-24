#!/usr/bin/env python3
"""Build (and optionally publish) the SOLIDS FOR YOU Whisper model packages for PyPI.

Maintainer tool; founders never run it. It turns OpenAI's official Whisper
checkpoint (MIT) into faster-whisper's format and splits it into PyPI-sized
wheels that the transcriber skill installs and verifies automatically.

  python3 scripts/build_whisper_packages.py base                 # fetch, verify, convert, package
  python3 scripts/build_whisper_packages.py base --upload        # ...and publish with $PYPI_TOKEN
  python3 scripts/build_whisper_packages.py base --ct2-dir DIR   # package an already converted model

Steps:
  1. Download the official checkpoint from OpenAI's server (openaipublic.azureedge.net)
     and check it against the SHA-256 OpenAI publishes in the download URL.
  2. Convert it to Hugging Face format with transformers' convert_openai_to_hf.py, then
     to CTranslate2 (float16) for faster-whisper. Needs: pip install torch transformers
     tiktoken ctranslate2 (and network access to raw.githubusercontent.com).
  3. Split files above 90 MiB, pack them into wheels of at most 90 MiB each
     (solidsforyou-whisper-<size>-<n>), each carrying OpenAI's MIT license.
  4. Record every final file's SHA-256 and the package list in
     plugins/transcriber/skills/transcriber/scripts/models.json.
  5. With --upload, publish with twine using the PYPI_TOKEN environment variable
     (never on the command line). PyPI versions are permanent: bump --version to republish.
"""
import argparse
import base64
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "plugins/transcriber/skills/transcriber/scripts/models.json"
OFFICIAL = {  # from openai-whisper's whisper/__init__.py; the folder name is the file's SHA-256
    "base": "https://openaipublic.azureedge.net/main/whisper/models/"
            "ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
    "small": "https://openaipublic.azureedge.net/main/whisper/models/"
             "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
}
CONVERTER = ("https://raw.githubusercontent.com/huggingface/transformers/main/"
             "src/transformers/models/whisper/convert_openai_to_hf.py")
OPENAI_LICENSE = "https://raw.githubusercontent.com/openai/whisper/main/LICENSE"
LIMIT = 90 * 1024 * 1024  # PyPI's default limit is 100 MB per file; stay well under it
HOMEPAGE = "https://github.com/Founderwithabs/SOLIDSFORYOU"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, dest):
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=600) as r, open(dest, "wb") as out:
        shutil.copyfileobj(r, out, 1 << 20)


def checkpoint(size, work, pt):
    expected = OFFICIAL[size].split("/")[-2]
    path = Path(pt) if pt else work / f"{size}.pt"
    if not path.exists():
        fetch(OFFICIAL[size], path)
    got = sha256(path)
    if got != expected:
        sys.exit(f"{path} has SHA-256 {got}, but OpenAI publishes {expected}. Not using it.")
    print(f"verified OpenAI checkpoint {path.name} ({expected[:12]}...)")
    return path


def convert(pt, work):
    for mod in ("torch", "transformers", "tiktoken", "ctranslate2"):
        try:
            __import__(mod)
        except ImportError:
            sys.exit(f"missing {mod}: pip install torch transformers tiktoken ctranslate2")
    conv = work / "convert_openai_to_hf.py"
    if not conv.exists():
        fetch(CONVERTER, conv)
    hf = work / "hf"
    subprocess.run([sys.executable, str(conv), "--checkpoint_path", str(pt),
                    "--pytorch_dump_folder_path", str(hf), "--convert_preprocessor", "True"], check=True)
    import ctranslate2
    out = work / "ct2"
    copy = [f for f in ("tokenizer.json", "preprocessor_config.json") if (hf / f).exists()]
    ctranslate2.converters.TransformersConverter(str(hf), copy_files=copy).convert(
        str(out), quantization="float16", force=True)
    return out


def chunks(ct2):
    """[(name_in_package, bytes_path_or_data)] with files above LIMIT split into .partN."""
    out = []
    for f in sorted(p for p in ct2.iterdir() if p.is_file()):
        size = f.stat().st_size
        if size <= LIMIT:
            out.append((f.name, f, 0, size))
        else:
            for i, start in enumerate(range(0, size, LIMIT), 1):
                out.append((f"{f.name}.part{i}", f, start, min(LIMIT, size - start)))
    return out


def wheel(dist, name, version, module, files, license_text, size):
    tag = "py3-none-any"
    dist_info = f"{module}-{version}.dist-info"
    path = dist / f"{module}-{version}-{tag}.whl"
    records = []

    def add(z, arcname, data):
        z.writestr(arcname, data)
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        records.append((arcname, f"sha256={digest}", str(len(data))))

    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        add(z, f"{module}/__init__.py", b'"""Whisper model files for the SOLIDS FOR YOU transcriber."""\n')
        for arcname, src, start, length in files:
            with open(src, "rb") as f:
                f.seek(start)
                add(z, f"{module}/data/{arcname}", f.read(length))
        meta = (f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
                f"Summary: OpenAI Whisper {size} (MIT) converted for faster-whisper, part of the SOLIDS FOR YOU transcriber\n"
                f"Home-page: {HOMEPAGE}\nAuthor: SOLIDS FOR YOU\nLicense: MIT\nRequires-Python: >=3.8\n").encode()
        add(z, f"{dist_info}/METADATA", meta)
        add(z, f"{dist_info}/WHEEL", f"Wheel-Version: 1.0\nGenerator: solidsforyou\nRoot-Is-Purelib: true\nTag: {tag}\n".encode())
        add(z, f"{dist_info}/licenses/LICENSE", license_text.encode())
        add(z, f"{dist_info}/top_level.txt", f"{module}\n".encode())
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerows(records)
        w.writerow((f"{dist_info}/RECORD", "", ""))
        z.writestr(f"{dist_info}/RECORD", buf.getvalue())
    return path


def package(size, ct2, version, dist):
    dist.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(OPENAI_LICENSE, timeout=60) as r:
            openai_license = r.read().decode()
    except OSError:
        openai_license = "MIT License\n\nCopyright (c) 2022 OpenAI\n(see https://github.com/openai/whisper/blob/main/LICENSE)\n"
    license_text = ("This package contains OpenAI's Whisper model, converted for faster-whisper by "
                    "SOLIDS FOR YOU. The model is licensed by OpenAI under the MIT License:\n\n" + openai_license)
    groups = []  # first-fit decreasing: big pieces first, small files fill the gaps
    for item in sorted(chunks(ct2), key=lambda it: -it[3]):
        for g in groups:
            if sum(x[3] for x in g) + item[3] <= LIMIT:
                g.append(item)
                break
        else:
            groups.append([item])
    packages, wheels = [], []
    for i, files in enumerate(groups, 1):
        name = f"solidsforyou-whisper-{size}-{i}"
        module = name.replace("-", "_")
        wheels.append(wheel(dist, name, version, module, files, license_text, size))
        packages.append({"name": name, "version": version, "module": module})
    files = {f.name: sha256(f) for f in sorted(ct2.iterdir()) if f.is_file()}
    return packages, files, wheels


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("size", choices=sorted(OFFICIAL))
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument("--pt", help="an already downloaded official checkpoint")
    ap.add_argument("--ct2-dir", help="skip download and conversion: package this converted model")
    ap.add_argument("--work", default=str(ROOT / "build" / "whisper"))
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()
    work = Path(args.work) / args.size
    work.mkdir(parents=True, exist_ok=True)
    ct2 = Path(args.ct2_dir) if args.ct2_dir else convert(checkpoint(args.size, work, args.pt), work)
    packages, files, wheels = package(args.size, ct2, args.version, work / "dist")
    reg_path = Path(args.registry)
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    entry = reg["models"].setdefault(args.size, {})
    entry.update({"published": False, "packages": packages, "files": files})
    if args.ct2_dir:
        entry["source"] = f"packaged from {Path(args.ct2_dir).name} (not from the official checkpoint)"
    reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    print(f"built {len(wheels)} wheel(s) in {work / 'dist'}; recorded hashes in {reg_path}")
    for w in wheels:
        print(f"  {w.name}  {w.stat().st_size / 1e6:.1f} MB")
    if args.upload:
        token = os.environ.get("PYPI_TOKEN")
        if not token:
            sys.exit("PYPI_TOKEN is not set; nothing uploaded")
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "twine"], check=True)
        subprocess.run([sys.executable, "-m", "twine", "upload", "--non-interactive", "-u", "__token__",
                        *map(str, wheels)], check=True, env={**os.environ, "TWINE_PASSWORD": token})
        entry["published"] = True
        reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
        print("uploaded. Commit models.json so the transcriber trusts exactly these files.")


if __name__ == "__main__":
    main()
