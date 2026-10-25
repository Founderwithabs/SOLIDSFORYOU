#!/usr/bin/env python3
"""Download, search and credit the free sound effects and music listed in
sounds/library.json (next to this script's folder).

Usage:
  python3 get_sounds.py list [--category transition]
  python3 get_sounds.py fetch sfx-kit [--category transition riser] [--dest DIR]
  python3 get_sounds.py fetch all --category transition logo-sting
  python3 get_sounds.py find whoosh soft [--category transition]
  python3 get_sounds.py credits file1.wav file2.mp3 ...

Only the folders asked for are downloaded, from the commit pinned in the
library, with git's sparse checkout (no audio is stored in SOLIDS FOR YOU).
After each download the source's licence file must still contain the text
the library expects, or the download is deleted and refused.
Files land in DIR/<source id>/ (default: $CLAUDE_PLUGIN_DATA/sounds, else
~/.cache/solidsforyou-sounds). `credits` prints the credit lines a video
description needs for the files used (CC0 files need none).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIBRARY = os.path.join(os.path.dirname(HERE), "sounds", "library.json")
STATE = ".solidsforyou-sounds.json"
AUDIO = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aiff", ".aif", ".opus")


def load_library():
    with open(LIBRARY, encoding="utf-8") as f:
        return json.load(f)


def default_dest():
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data:
        return os.path.join(data, "sounds")
    return os.path.join(os.path.expanduser("~"), ".cache", "solidsforyou-sounds")


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def patterns_for(src, categories):
    """Sparse-checkout patterns (gitignore style) for the chosen categories."""
    pats = ["/" + src["license_file"]]
    for extra in src.get("extras", []):
        pats.append("/" + extra + ("/" if "." not in os.path.basename(extra) else ""))
    for cat in categories:
        for path in src["categories"][cat]:
            pats.append("/" + path + ("" if path.endswith("*") else "/"))
    for path in src.get("exclude", []):
        pats.append("!/" + path + ("" if os.path.splitext(path)[1] else "/"))
    return pats


def fetch(src, categories, dest):
    root = os.path.join(dest, src["id"])
    state_path = os.path.join(root, STATE)
    done = []
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            done = json.load(f).get("categories", [])
    wanted = sorted(set(done) | set(categories))
    if wanted == done:
        print("%-16s already downloaded  %s" % (src["id"], root))
        return
    # Start clean each time: git's copy of the audio is deleted after
    # checkout (it would double the disk use), so adding categories re-fetches.
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    url = "https://github.com/%s.git" % src["repo"]
    for args in (["init", "-q"], ["remote", "add", "origin", url],
                 ["config", "core.sparseCheckout", "true"]):
        git(args, root)
    with open(os.path.join(root, ".git", "info", "sparse-checkout"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(patterns_for(src, wanted)) + "\n")
    r = git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin",
             src["commit"]], root)
    if r.returncode != 0:
        shutil.rmtree(root, ignore_errors=True)  # no half-downloaded folder left behind
        sys.exit("Couldn't download %s from GitHub:\n%s\nIf github.com is blocked "
                 "by this environment's network settings, allow it there; don't "
                 "work around the block." % (src["repo"], r.stderr.strip()))
    r = git(["checkout", "-q", "--force", src["commit"]], root)
    if r.returncode != 0:
        shutil.rmtree(root, ignore_errors=True)  # no half-downloaded folder left behind
        sys.exit("Checkout failed for %s:\n%s" % (src["repo"], r.stderr.strip()))
    lic = os.path.join(root, src["license_file"])
    text = open(lic, encoding="utf-8", errors="replace").read() if os.path.exists(lic) else ""
    if src["license_check"] not in text:
        shutil.rmtree(root, ignore_errors=True)
        sys.exit("Refused %s: its licence file %s no longer says %r. Re-check the "
                 "licence before using it." % (src["repo"], src["license_file"],
                                                src["license_check"]))
    shutil.rmtree(os.path.join(root, ".git"), ignore_errors=True)
    for path in src.get("exclude", []):  # never keep an excluded file
        full = os.path.join(root, path)
        if os.path.isdir(full):
            shutil.rmtree(full)
        elif os.path.exists(full):
            os.remove(full)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump({"id": src["id"], "repo": src["repo"], "commit": src["commit"],
                   "license": src["license"], "categories": wanted}, f, indent=2)
    count = sum(1 for _ in audio_files(root))
    print("%-16s %4d files  %-12s %s" % (src["id"], count, src["license"].split(" ")[0], root))


def audio_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in sorted(filenames):
            if name.lower().endswith(AUDIO):
                yield os.path.join(dirpath, name)


def source_of(path, lib):
    """The library source a downloaded file belongs to, and its path inside it."""
    d = os.path.dirname(os.path.abspath(path))
    while True:
        state = os.path.join(d, STATE)
        if os.path.exists(state):
            sid = json.load(open(state, encoding="utf-8"))["id"]
            src = next((s for s in lib["sources"] if s["id"] == sid), None)
            return src, os.path.relpath(os.path.abspath(path), d).replace(os.sep, "/")
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def category_of(src, rel):
    for cat, paths in src["categories"].items():
        for p in paths:
            if rel.startswith(p.rstrip("*")):
                return cat
    return "-"


def cmd_list(lib, args):
    for src in lib["sources"]:
        cats = [c for c in src["categories"] if not args.category or c in args.category]
        if not cats:
            continue
        print("%s  (%s, %s)  github.com/%s" % (src["id"], src["license"], src["format"], src["repo"]))
        print("    " + src["origin"])
        print("    categories: " + ", ".join(cats))
    print("\nRejected sources and why: see 'rejected' in sounds/library.json.")


def cmd_fetch(lib, args):
    ids = [s["id"] for s in lib["sources"]] if args.source == "all" else [args.source]
    for sid in ids:
        src = next((s for s in lib["sources"] if s["id"] == sid), None)
        if not src:
            sys.exit("Unknown source %r. Run: get_sounds.py list" % sid)
        cats = list(src["categories"]) if not args.category else \
            [c for c in args.category if c in src["categories"]]
        if not cats:
            if args.source != "all":
                sys.exit("%s has none of those categories: %s" % (sid, ", ".join(src["categories"])))
            continue
        fetch(src, cats, args.dest)


def cmd_find(lib, args):
    words = [w.lower() for w in args.words]
    hits = 0
    if not os.path.isdir(args.dest):
        sys.exit("Nothing downloaded yet in %s. Run fetch first." % args.dest)
    for sid in sorted(os.listdir(args.dest)):
        root = os.path.join(args.dest, sid)
        src, _ = source_of(os.path.join(root, "x"), lib)
        if not src:
            continue
        for f in audio_files(root):
            rel = os.path.relpath(f, root).replace(os.sep, "/")
            cat = category_of(src, rel)
            if args.category and cat not in args.category:
                continue
            if all(w in rel.lower() for w in words):
                credit = " (credit needed)" if credit_line(src, rel) else ""
                print("%s\t%s\t%s%s" % (f, cat, src["license"].split(" ")[0], credit))
                hits += 1
    if not hits:
        print("No downloaded file matches. Try fewer words, or fetch more categories.")


def credit_line(src, rel):
    for prefix, line in (src.get("credit") or {}).items():
        if rel.startswith(prefix):
            return line
    return None


def cmd_credits(lib, args):
    lines, unknown = [], []
    for f in args.files:
        src, rel = source_of(f, lib)
        if not src:
            unknown.append(f)
            continue
        line = credit_line(src, rel)
        if line and line not in lines:
            lines.append(line)
    if lines:
        print("Put these in the video description (CC BY 4.0 requires them):")
        for line in lines:
            print("  " + line)
    elif len(unknown) < len(args.files):
        print("No credit required: every library file here is CC0.")
    if unknown:
        print("Not from the library (check their licence yourself):")
        for f in unknown:
            print("  " + f)
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dest", default=default_dest(), help="where downloads go")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list", parents=[common])
    s.add_argument("--category", nargs="+")
    s = sub.add_parser("fetch", parents=[common])
    s.add_argument("source", help="a source id, or 'all'")
    s.add_argument("--category", nargs="+")
    s = sub.add_parser("find", parents=[common])
    s.add_argument("words", nargs="*")
    s.add_argument("--category", nargs="+")
    s = sub.add_parser("credits", parents=[common])
    s.add_argument("files", nargs="+")
    args = p.parse_args()
    if os.path.exists(args.dest) and not os.path.isdir(args.dest):
        sys.exit(f"--dest {args.dest} is a file; give a folder for the sounds")
    if args.cmd == "fetch" and not shutil.which("git"):
        sys.exit("downloading sounds needs git: install it (Mac: xcode-select --install; Windows: winget "
                 "install Git.Git; Linux: apt install git), or use sfx_mix.py's built-in sounds")
    lib = load_library()
    {"list": cmd_list, "fetch": cmd_fetch, "find": cmd_find, "credits": cmd_credits}[args.cmd](lib, args)


if __name__ == "__main__":
    main()
