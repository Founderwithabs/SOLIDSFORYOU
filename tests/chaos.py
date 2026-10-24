#!/usr/bin/env python3
"""Chaos tests: fire hostile inputs at every SOLIDS FOR YOU script and fail on any crash or hang.

Empty, binary, wrong-shape and Windows (cp1252) files; semicolon and tab exports; nulls, NaN,
negatives and huge values; paths with spaces, quotes and accents; parallel writes; and, for the
media tools, fake media, silence, surround sound, truncated video and a machine without ffmpeg.
A script may refuse an input, but only with a plain message: a Python traceback, a hang or a lost
memory row is a failure. run_tests.py runs this in full mode; run it alone with:

  python3 tests/chaos.py            text, data and media tools
  python3 tests/chaos.py --no-media text and data tools only
"""
import csv, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "plugins"
P = sys.executable
results = []


def run(label, cmd, timeout=240, env=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=W,
                           env={**os.environ, **(env or {})}, errors="replace")
        out = (r.stdout + r.stderr).strip()
        results.append(("CRASH" if "Traceback" in out else "ok", r.returncode, label,
                        out.splitlines()[-1][:160] if out else ""))
    except subprocess.TimeoutExpired:
        results.append(("HANG", None, label, ""))


def f(name, data, enc="utf-8"):
    p = W / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode(enc))
    return str(p)


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def text_tools():
    S = R / "social-media/skills/social-media/scripts"
    E = R / "ecom/skills/ecom/scripts"
    C = R / "competitor-research/skills/competitor-research/scripts"
    M = R / "economy-mode/skills/economy-mode/scripts/memory.py"
    A = R / "ai-visuals/skills/ai-visuals/scripts"
    T = R / "master/skills/master/scripts/transcript_edit.py"
    # ---- shared hostile files
    empty = f("empty.txt", "")
    binary = f("binary.bin", bytes(range(256)) * 20)
    latin = f("latin1.csv", "channel,title,views\nCafé,Crème brûlée,1200\n", "latin-1")
    header_only = f("header.csv", "channel,title,views\n")
    missing = str(W / "does-not-exist.csv")
    spaced_dir = W / "my folder ünïcode 'q'"; spaced_dir.mkdir()

    # ---- transcripts
    srts = {
     "empty.srt": "",
     "bom_crlf.srt": "﻿1\r\n00:00:00,000 --> 00:00:02,000\r\nHello\r\n\r\n2\r\n00:00:05,000 --> 00:00:07,000\r\nWorld\r\n",
     "bad_ts.srt": "1\n00:00:xx,000 --> 00:00:02,000\nHello\n",
     "dot_ms.srt": "1\n00:00:00.000 --> 00:00:02.500\nHello\n\n2\n00:00:04.000 --> 00:00:06.000\nThere\n",
     "overlap.srt": "1\n00:00:00,000 --> 00:00:05,000\nA\n\n2\n00:00:03,000 --> 00:00:04,000\nB\n",
     "backwards.srt": "1\n00:00:05,000 --> 00:00:01,000\nA\n",
     "hours.srt": "1\n100:00:00,000 --> 100:00:02,000\nlong\n",
     "one_cue.srt": "1\n00:00:00,000 --> 00:00:02,000\nonly\n",
     "no_text.srt": "1\n00:00:00,000 --> 00:00:02,000\n\n2\n00:00:03,000 --> 00:00:04,000\n\n",
     "styled.vtt": "WEBVTT\nKind: captions\n\nSTYLE\n::cue { color: red }\n\nNOTE hi\n\nid1\n00:00.000 --> 00:02.000 align:start\n<v Bob>Hello <b>there</b>\n\n00:05.000 --> 00:07.000\nAgain\n",
     "whisper.json": json.dumps({"segments": [{"start": 0, "end": 2, "text": " hi"}, {"start": 5, "end": 6, "text": "yo"}]}),
     "whisper_list.json": json.dumps([{"start": 0, "end": 2, "text": "hi"}]),
     "whisper_bad.json": "{not json",
     "whisper_nulls.json": json.dumps({"segments": [{"start": None, "end": 2, "text": None}]}),
    }
    for n, d in srts.items():
        p = f(n, d)
        run(f"transcript_edit {n}", [P, str(T), p])
        run(f"chapters {n}", [P, str(S / "chapters.py"), p, "--target", "4"])
    run("transcript_edit missing", [P, str(T), missing])
    run("transcript_edit binary", [P, str(T), binary])
    run("transcript_edit --floor -1", [P, str(T), str(W / "bom_crlf.srt"), "--floor", "-1"])
    run("transcript_edit --floor abc", [P, str(T), str(W / "bom_crlf.srt"), "--floor", "abc"])
    run("transcript_edit apply non-video", [P, str(T), str(W / "bom_crlf.srt"), "--apply", binary, str(W / "o.mp4")])
    run("transcript_edit apply missing", [P, str(T), str(W / "bom_crlf.srt"), "--apply", missing, str(W / "o.mp4")])

    # chapters --check
    chk = {"ch_empty.txt": "", "ch_garbage.txt": "hello\nworld\n", "ch_hours.txt": "0:00 A\n1:00:00 B\n1:10:00 C\n",
           "ch_unsorted.txt": "0:00 A\n0:50 B\n0:20 C\n", "ch_dup.txt": "0:00 A\n0:00 B\n0:30 C\n", "ch_crlf.txt": "0:00 A\r\n0:30 B\r\n1:00 C\r\n",
           "ch_dash.txt": "00:00 - Intro\n00:30 – Part\n01:00 | End\n"}
    for n, d in chk.items():
        run(f"chapters --check {n}", [P, str(S / "chapters.py"), "--check", f(n, d), "--duration", "120"])
    run("chapters --check no duration", [P, str(S / "chapters.py"), "--check", str(W / "ch_crlf.txt")])
    run("chapters --check duration 0", [P, str(S / "chapters.py"), "--check", str(W / "ch_crlf.txt"), "--duration", "0"])
    run("chapters --target 0", [P, str(S / "chapters.py"), str(W / "bom_crlf.srt"), "--target", "0"])
    run("chapters --target 1000", [P, str(S / "chapters.py"), str(W / "bom_crlf.srt"), "--target", "1000"])
    run("chapters no args", [P, str(S / "chapters.py")])

    # hookscore / package_check
    for n, d in {"hk_empty.txt": "", "hk_blank_lines.txt": "\n\n  \n", "hk_emoji.txt": "🔥🔥🔥\n", "hk_hindi.txt": "क्या आप जानते हैं?\n",
                 "hk_long.txt": ("word " * 5000) + "\n", "hk_bin": bytes(range(256))}.items():
        p = f(n, d)
        run(f"hookscore {n}", [P, str(S / "hookscore.py"), p])
        run(f"package_check {n}", [P, str(S / "package_check.py"), p])
    run("hookscore --hook ''", [P, str(S / "hookscore.py"), "--hook", ""])
    run("hookscore --format weird", [P, str(S / "hookscore.py"), "--format", "weird", "--hook", "x"])
    run("hookscore missing", [P, str(S / "hookscore.py"), missing])
    run("package_check --title '' ", [P, str(S / "package_check.py"), "--title", ""])
    run("package_check --thumb only", [P, str(S / "package_check.py"), "--thumb", "HI"])
    run("package_check --desktop abc", [P, str(S / "package_check.py"), "--title", "x", "--desktop", "abc"])

    # outliers
    for n, d in {"o_empty.json": "", "o_obj.json": "{}", "o_str.json": '"hi"', "o_nulls.json": json.dumps([{"channel": None, "title": None, "views": None}]),
                 "o_strviews.json": json.dumps([{"channel": "a", "title": f"t{i}", "views": v} for i, v in enumerate(["1.2K", "3M", "n/a", "1,000", "-5"])]),
                 "o_zero.json": json.dumps([{"channel": "a", "title": f"t{i}", "views": 0} for i in range(5)]),
                 "o_semicolon.csv": "channel;title;views\na;b;1\n", "o_noviews.csv": "channel,title\na,b\n"}.items():
        run(f"outliers {n}", [P, str(S / "outliers.py"), f(n, d)])
    run("outliers latin1", [P, str(S / "outliers.py"), latin])
    run("outliers header only", [P, str(S / "outliers.py"), header_only])
    run("outliers binary", [P, str(S / "outliers.py"), binary])
    run("outliers missing", [P, str(S / "outliers.py"), missing])
    run("outliers --min abc", [P, str(S / "outliers.py"), str(W / "o_zero.json"), "--min", "abc"])

    # retention
    for n, d in {"r_empty.csv": "", "r_header.csv": "a,b\n", "r_few.csv": "0,100\n1,90\n", "r_text.csv": "a,b\nx,y\n" * 10,
                 "r_neg.csv": "\n".join(f"{i},{-i}" for i in range(20)), "r_flat.csv": "\n".join(f"{i},50" for i in range(20)),
                 "r_semicolon.csv": "\n".join(f"{i};{100-i}" for i in range(20)), "r_eu.csv": "\n".join(f'"{i},5";"{100-i},2"' for i in range(20)),
                 "r_dup_x.csv": "\n".join(f"5,{100-i}" for i in range(20)), "r_nan.csv": "\n".join(f"{i},nan" for i in range(20)),
                 "r_inf.csv": "\n".join(f"{i},inf" for i in range(20))}.items():
        run(f"retention {n}", [P, str(S / "retention.py"), f(n, d), "--duration", "60"])
    run("retention duration 0", [P, str(S / "retention.py"), str(W / "r_flat.csv"), "--duration", "0"])
    run("retention duration abc", [P, str(S / "retention.py"), str(W / "r_flat.csv"), "--duration", "abc"])
    run("retention duration missing value", [P, str(S / "retention.py"), str(W / "r_flat.csv"), "--duration"])
    run("retention binary", [P, str(S / "retention.py"), binary])
    run("retention bad transcript", [P, str(S / "retention.py"), str(W / "r_flat.csv"), "--duration", "60", "--transcript", str(W / "bad_ts.srt")])

    # content_log
    run("content_log template", [P, str(S / "content_log.py"), "template"])
    for n, d in {"posts_empty.csv": "", "posts_header.csv": "", "posts_bin": bytes(range(256)), "posts_latin": "date,platform\nCafé,ig\n".encode("latin-1")}.items():
        run(f"content_log analyze {n}", [P, str(S / "content_log.py"), "analyze", f(n, d)])
    run("content_log analyze missing", [P, str(S / "content_log.py"), "analyze", missing])
    run("content_log score letters", [P, str(S / "content_log.py"), "score", "a", "b"])
    run("content_log score none", [P, str(S / "content_log.py"), "score"])
    run("content_log score negatives", [P, str(S / "content_log.py"), "score"] + ["-5"] * 14)
    run("content_log score huge", [P, str(S / "content_log.py"), "score"] + ["1e9"] * 14)

    # read_sections
    for rs in [S / "read_sections.py", C / "read_sections.py", E / "read_sections.py"]:
        run(f"read_sections {rs.parent.parent.name} missing section", [P, str(rs), str(R / "social-media/skills/social-media/social-media.md"), "99"])
        run(f"read_sections {rs.parent.parent.name} no sections file", [P, str(rs), empty, "1"])
        run(f"read_sections {rs.parent.parent.name} missing file", [P, str(rs), missing, "1"])
        run(f"read_sections {rs.parent.parent.name} binary", [P, str(rs), binary, "--list"])
        break

    # ledger
    run("ledger check missing folder", [P, str(C / "ledger.py"), "check", missing])
    run("ledger tables empty folder", [P, str(C / "ledger.py"), "tables", str(spaced_dir)])
    lf = W / "lg"; run("ledger init", [P, str(C / "ledger.py"), "init", str(lf)])
    run("ledger init again", [P, str(C / "ledger.py"), "init", str(lf)])
    run("ledger tables fresh", [P, str(C / "ledger.py"), "tables", str(lf)])
    run("ledger sample fresh", [P, str(C / "ledger.py"), "sample", str(lf)])
    run("ledger merge fresh", [P, str(C / "ledger.py"), "merge", str(lf)])
    if (lf / "ledger.csv").exists():
        hdr = (lf / "ledger.csv").read_text().splitlines()[0]
        (lf / "ledger.csv").write_text(hdr + "\n" + ",".join(["garbage"] * len(hdr.split(","))) + "\n" + "short,row\n")
        run("ledger check garbage rows", [P, str(C / "ledger.py"), "check", str(lf)])
        run("ledger tables garbage rows", [P, str(C / "ledger.py"), "tables", str(lf)])
        (lf / "ledger.csv").write_bytes(bytes(range(256)))
        run("ledger check binary ledger", [P, str(C / "ledger.py"), "check", str(lf)])
        run("ledger tables binary ledger", [P, str(C / "ledger.py"), "tables", str(lf)])
    run("ledger sample --pct 0", [P, str(C / "ledger.py"), "sample", str(lf), "--pct", "0"])
    run("ledger sample --pct 500", [P, str(C / "ledger.py"), "sample", str(lf), "--pct", "500"])

    # ecom economics
    fees = {"fe_empty.json": "", "fe_bad.json": "{", "fe_obj.json": "{}", "fe_nofees.json": json.dumps({"channel": "x", "fees": []}),
            "fe_wrongtype.json": json.dumps({"channel": "x", "fees": [{"name": "r", "type": "percent", "value": "ten"}]}),
            "fe_unknowntype.json": json.dumps({"channel": "x", "fees": [{"name": "r", "type": "magic", "value": 5}]}),
            "fe_return100.json": json.dumps({"channel": "x", "fees": [], "returns": {"rate_pct": 100, "cost_per_return": 10, "unsellable_pct": 100}}),
            "fe_return150.json": json.dumps({"channel": "x", "fees": [], "returns": {"rate_pct": 150}}),
            "fe_fee100.json": json.dumps({"channel": "x", "fees": [{"name": "r", "type": "percent", "value": 100, "of": "price"}]}),
            "fe_exclusive.json": json.dumps({"channel": "x", "tax": {"mode": "exclusive", "rate_pct": 8}, "fees": []}),
            "fe_nulltiers.json": json.dumps({"channel": "x", "fees": [{"name": "r", "type": "percent_tiers", "of": "price", "tiers": []}]}),
            "fe_weight_noweight.json": json.dumps({"channel": "x", "fees": [{"name": "s", "type": "weight_tiers", "tiers": [{"up_to_g": 500, "value": 50}]}]}),
            "fe_ads_both.json": json.dumps({"channel": "x", "fees": [], "ads": {"tacos_pct": 10, "cost_per_order": 50}})}
    for n, d in fees.items():
        run(f"economics {n}", [P, str(E / "economics.py"), "unit", "--fees", f(n, d), "--price", "999", "--cost", "300", "--target-margin", "25"])
    good = str(W / "fe_obj.json")
    run("economics price 0", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "0", "--cost", "300"])
    run("economics price negative", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "-10", "--cost", "300"])
    run("economics price abc", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "abc", "--cost", "300"])
    run("economics target 100", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "999", "--cost", "300", "--target-margin", "100"])
    run("economics target 150", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "999", "--cost", "300", "--target-margin", "150"])
    run("economics sweep garbage", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "999", "--cost", "300", "--sweep", "a,,b"])
    run("economics sweep with 0", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "999", "--cost", "300", "--sweep", "0,100"])
    run("economics products missing sku", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "999", "--products", header_only, "--sku", "NOPE"])
    run("economics no cost", [P, str(E / "economics.py"), "unit", "--fees", str(W / "fe_nofees.json"), "--price", "999"])
    run("economics fees missing", [P, str(E / "economics.py"), "unit", "--fees", missing, "--price", "999", "--cost", "1"])

    # ecom ops
    for n, d in {"ads_empty.csv": "", "ads_header.csv": "Campaign,Spend,Sales\n", "ads_nomatch.csv": "a,b,c\n1,2,3\n",
                 "ads_zero.csv": "Campaign Name,Spend,Sales,Orders,Clicks,Impressions\nX,0,0,0,0,0\nY,100,0,0,0,0\n",
                 "ads_totals.csv": "Campaign Name,Spend,Sales,Orders,Clicks,Impressions\nX,100,500,5,50,1000\nTotal,100,500,5,50,1000\n",
                 "ads_neg.csv": "Campaign Name,Spend,Sales,Orders,Clicks,Impressions\nX,-100,500,5,50,1000\n",
                 "ads_text.csv": "Campaign Name,Spend,Sales,Orders,Clicks,Impressions\nX,N/A,--,,,\n",
                 "ads_semicolon.csv": "Campaign Name;Spend;Sales\nX;100;500\n",
                 "ads_bom_tsv.csv": "﻿Campaign Name\tSpend\tSales\nX\t100\t500\n"}.items():
        run(f"ops ads {n}", [P, str(E / "ops.py"), "ads", f(n, d), "--breakeven-acos", "30"])
    run("ops ads latin1", [P, str(E / "ops.py"), "ads", latin])
    run("ops ads binary", [P, str(E / "ops.py"), "ads", binary])
    run("ops returns empty", [P, str(E / "ops.py"), "returns", empty])
    run("ops returns noreason", [P, str(E / "ops.py"), "returns", f("ret_noreason.csv", "id,date\n1,2\n")])
    run("ops returns orders 0", [P, str(E / "ops.py"), "returns", f("ret_ok.csv", "id,reason\n1,size\n"), "--orders", "0"])
    run("ops returns more returns than orders", [P, str(E / "ops.py"), "returns", str(W / "ret_ok.csv"), "--orders", "0.5"])
    run("ops reorder zeros", [P, str(E / "ops.py"), "reorder", "--daily-sales", "0", "--lead-days", "0", "--on-hand", "0"])
    run("ops reorder negative", [P, str(E / "ops.py"), "reorder", "--daily-sales", "-5", "--lead-days", "30", "--on-hand", "10"])
    run("ops reorder huge", [P, str(E / "ops.py"), "reorder", "--daily-sales", "1e300", "--lead-days", "1e300", "--on-hand", "1"])
    run("ops reorder nan", [P, str(E / "ops.py"), "reorder", "--daily-sales", "nan", "--lead-days", "30", "--on-hand", "10"])

    # listing_check
    for n, d in {"l_empty.json": "", "l_bad.json": "{", "l_list.json": "[]", "l_str.json": '"title"', "l_nulls.json": json.dumps({"title": None, "bullets": None}),
                 "l_bullets_str.json": json.dumps({"title": "x", "bullets": "one bullet as a string"}),
                 "l_numbers.json": json.dumps({"title": 123, "bullets": [1, 2]}), "l_emoji.json": json.dumps({"title": "🔥" * 300})}.items():
        run(f"listing_check {n}", [P, str(E / "listing_check.py"), f(n, d)])
    run("listing_check bad limits", [P, str(E / "listing_check.py"), str(W / "l_emoji.json"), "--limits", "title=abc"])
    run("listing_check limits garbage", [P, str(E / "listing_check.py"), str(W / "l_emoji.json"), "--limits", "nonsense"])
    run("listing_check keywords binary", [P, str(E / "listing_check.py"), str(W / "l_emoji.json"), "--keywords", binary])
    run("listing_check keywords missing", [P, str(E / "listing_check.py"), str(W / "l_emoji.json"), "--keywords", missing])

    # memory
    mem = lambda *a, label=None, env=None: run(label or "memory " + " ".join(a)[:60], [P, str(M), "--file", str(W / "mem/memory.csv"), *a], env=env)
    mem("search", "x"); mem("pinned"); mem("recent"); mem("stats"); mem("brief"); mem("session-start")
    mem("add", "--topic", "t", "--text", "line1\nline2, \"quoted\", =SUM(A1)", label="memory add newline quote formula")
    mem("add", "--topic", "", "--text", "empty topic")
    mem("add", "--topic", "x" * 5000, "--text", "long topic")
    mem("add", "--topic", "t", "--text", "   ")
    mem("search", "")
    mem("search", "!!!")
    mem("update", "999", "--text", "x"); mem("forget", "abc"); mem("update", "1")
    mem("recent", "--n", "-5"); mem("search", "t", "--k", "0"); mem("brief", "--k", "-1", "--task", "t")
    (W / "mem2").mkdir(); (W / "mem2/memory.csv").write_bytes(bytes(range(256)))
    run("memory corrupted binary sheet search", [P, str(M), "--file", str(W / "mem2/memory.csv"), "search", "x"])
    run("memory corrupted binary sheet add", [P, str(M), "--file", str(W / "mem2/memory.csv"), "add", "--topic", "a", "--text", "b"])
    (W / "mem3").mkdir(); (W / "mem3/memory.csv").write_text("totally,different,columns\n1,2,3\n")
    run("memory foreign csv add", [P, str(M), "--file", str(W / "mem3/memory.csv"), "add", "--topic", "a", "--text", "b"])
    run("memory foreign csv brief", [P, str(M), "--file", str(W / "mem3/memory.csv"), "brief"])
    (W / "mem4").mkdir(); (W / "mem4/memory.csv").write_text("id,created,updated,type,topic,text,source,pinned,status\nabc,,,,t,x,,,active\n,,,,t2,y,,,\n")
    run("memory bad ids add", [P, str(M), "--file", str(W / "mem4/memory.csv"), "add", "--topic", "a", "--text", "b"])
    run("memory bad ids update abc", [P, str(M), "--file", str(W / "mem4/memory.csv"), "update", "abc", "--text", "z"])
    run("memory sheet path is a dir", [P, str(M), "--file", str(W / "mem4"), "search", "x"])
    run("memory env var sheet", [P, str(M), "stats"], env={"SFY_MEMORY_FILE": str(spaced_dir / "m.csv")})
    # concurrent adds
    procs = [subprocess.Popen([P, str(M), "--file", str(W / "conc/memory.csv"), "add", "--topic", f"t{i}", "--text", f"fact {i}"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(30)]
    for p in procs: p.wait()
    import csv
    rows = list(csv.DictReader(open(W / "conc/memory.csv", encoding="utf-8-sig")))
    results.append(("LOST" if len(rows) != 30 else "ok", 0, f"memory 30 parallel adds -> {len(rows)} rows, ids {sorted(set(r['id'] for r in rows))[:5]}...", ""))

    HZ = R / "humanizer/skills/humanizer/scripts/humanize.py"
    for name in ("empty.txt", "binary.bin", "hk_long.txt", "hk_emoji.txt", "hk_hindi.txt", "does-not-exist.csv"):
        run(f"humanize check {name}", [P, str(HZ), "check", str(W / name)])
        run(f"humanize profile {name}", [P, str(HZ), "profile", str(W / name)])
    run("humanize compare binary", [P, str(HZ), "compare", str(W / "binary.bin"), str(W / "hk_hindi.txt")])
    run("humanize compare empty", [P, str(HZ), "compare", str(W / "empty.txt"), str(W / "empty.txt")])
    run("humanize voice tiny samples", [P, str(HZ), "voice", str(W / "hk_emoji.txt"), "--draft", str(W / "hk_long.txt")])
    run("humanize voice huge", [P, str(HZ), "voice", str(W / "hk_long.txt"), "--draft", str(W / "binary.bin")])
    run("humanize no command", [P, str(HZ)])
    LC = R / "linkedin/skills/linkedin/scripts/linkedin_check.py"
    for name in ("empty.txt", "binary.bin", "hk_long.txt", "hk_emoji.txt", "hk_hindi.txt", "does-not-exist.csv"):
        for kind in ([], ["--headline"], ["--about"], ["--note"], ["--comment"]):
            run(f"linkedin_check {name} {' '.join(kind)}", [P, str(LC), str(W / name), *kind])
    run("linkedin_check no args", [P, str(LC)])
    run("linkedin_check two kinds", [P, str(LC), "--text", "hi", "--headline", "--note"])
    run("humanize bad channel", [P, str(HZ), "check", "--text", "hi", "--channel", "nope"])
    CL = R / "clipper/skills/clipper/scripts/clip.py"
    f("cl_nulls.json", json.dumps({"segments": [{"start": None, "end": None, "text": None, "words": None},
                                                {"start": 0, "end": 1e308, "text": "x"}, "junk", 7]}))
    f("cl_semi.json", json.dumps([{"start": 0, "end": 30, "text": "Why does this work?", "words": [{"start": "a"}]}]))
    for name in ("empty.txt", "binary.bin", "hk_long.txt", "hk_hindi.txt", "cl_nulls.json", "cl_semi.json", "does-not-exist.csv"):
        run(f"clip find {name}", [P, str(CL), "find", str(W / name)])
    for args in ([], ["nope"], ["find"], ["find", str(W / "cl_semi.json"), "--min", "50", "--max", "10"],
                 ["find", str(W / "cl_semi.json"), "--min", "nan"], ["find", str(W / "cl_semi.json"), "--top", "0"],
                 ["find", str(W / "cl_semi.json"), "--max", "inf"], ["render"], ["render", str(W / "missing.mp4")]):
        run("clip " + " ".join(Path(a).name for a in args[:4]), [P, str(CL), *args])

    # ai-visuals
    run("score none", [P, str(A / "score.py")]); run("score text", [P, str(A / "score.py")] + ["x"] * 8)
    run("score nan", [P, str(A / "score.py")] + ["nan"] * 8); run("score decimals", [P, str(A / "score.py")] + ["8.5"] * 8)
    run("prompt_diff empty both", [P, str(A / "prompt_diff.py"), empty, empty])
    run("prompt_diff identical", [P, str(A / "prompt_diff.py"), str(W / "hk_hindi.txt"), str(W / "hk_hindi.txt")])
    run("prompt_diff binary", [P, str(A / "prompt_diff.py"), binary, binary])
    run("prompt_diff missing", [P, str(A / "prompt_diff.py"), missing, empty])
    run("prompt_diff huge", [P, str(A / "prompt_diff.py"), str(W / "hk_long.txt"), str(W / "hk_emoji.txt")], timeout=60)
    run("generate empty prompt", [P, str(A / "generate_openai.py"), "--prompt-file", empty, "--out", "o.png"], env={"OPENAI_API_KEY": "sk-x"})
    run("generate unreachable", [P, str(A / "generate_openai.py"), "--prompt-file", str(W / "hk_hindi.txt"), "--out", "o.png", "--base-url", "http://127.0.0.1:9"], env={"OPENAI_API_KEY": "sk-x"})
    run("generate missing image", [P, str(A / "generate_openai.py"), "--prompt-file", str(W / "hk_hindi.txt"), "--out", "o.png", "--image", missing], env={"OPENAI_API_KEY": "sk-x"})
    run("generate n 0", [P, str(A / "generate_openai.py"), "--prompt-file", str(W / "hk_hindi.txt"), "--out", "o.png", "--n", "0", "--base-url", "http://127.0.0.1:9"], env={"OPENAI_API_KEY": "sk-x"})
    run("generate missing prompt file", [P, str(A / "generate_openai.py"), "--prompt-file", missing, "--out", "o.png"], env={"OPENAI_API_KEY": "sk-x"})



def media_tools():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe") and shutil.which("node")):
        print("SKIP media chaos: needs ffmpeg, ffprobe and node")
        return
    odd = W / "my clip 'ü' & (1)"; odd.mkdir()
    (W / "zero.mp3").write_bytes(b"")
    (W / "text.mp3").write_text("this is not audio")
    ff("-f", "lavfi", "-i", "sine=f=440:d=0.05", str(W / "tiny.wav"))
    ff("-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "3", str(W / "silence.wav"))
    ff("-f", "lavfi", "-i", "sine=f=440:d=3:sample_rate=8000", str(W / "mono8k.wav"))
    ff("-f", "lavfi", "-i", "sine=f=440:d=3", "-af", "pan=5.1|c0=c0|c1=c0|c2=c0|c3=c0|c4=c0|c5=c0", str(W / "surround.wav"))
    ff("-f", "lavfi", "-i", "sine=f=440:d=3:sample_rate=96000", "-c:a", "pcm_s24le", str(W / "hires.wav"))
    ff("-f", "lavfi", "-i", "sine=f=1000:d=3", "-af", "volume=30", str(W / "clipped.wav"))
    ff("-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(W / "noaudio.mp4"))
    ff("-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=4", "-f", "lavfi", "-i", "sine=d=4", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(odd / "clip.mp4"))
    data = (odd / "clip.mp4").read_bytes(); (W / "truncated.mp4").write_bytes(data[: len(data) // 3])
    ff("-f", "lavfi", "-i", "testsrc=s=1080x1920:r=30:d=0.2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(W / "short_vertical.mp4"))
    ff("-f", "lavfi", "-i", "color=black:s=64x64:r=1:d=3", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(W / "black.mp4"))
    ff("-f", "lavfi", "-i", "color=white:s=4000x4000", "-frames:v", "1", str(W / "huge.png"))
    ff("-f", "lavfi", "-i", "color=white:s=2x2", "-frames:v", "1", str(W / "dot.png"))
    ff("-f", "lavfi", "-i", "color=red@0.0:s=500x500,format=rgba", "-frames:v", "1", str(W / "transparent.png"))
    (W / "fake.jpg").write_text("not an image")
    ff("-f", "lavfi", "-i", "testsrc=s=800x800", "-frames:v", "1", str(odd / "img one.webp"))

    AN = R / "audio-review/skills/audio-review/analyze.py"
    for f in ["zero.mp3", "text.mp3", "tiny.wav", "silence.wav", "mono8k.wav", "surround.wav", "hires.wav", "clipped.wav", "noaudio.mp4", "truncated.mp4", str(odd / "clip.mp4"), "missing.wav"]:
        run(f"analyze {Path(f).name}", [P, str(AN), str(W / f) if not f.startswith("/") else f, "--out", str(W / "an" / Path(f).stem)])
    run("analyze on dir", [P, str(AN), str(W)])
    IV = R / "motion-design-taste/skills/motion-design-taste/scripts/inspect_video.py"
    for f in ["zero.mp3", "silence.wav", "noaudio.mp4", "truncated.mp4", "short_vertical.mp4", "black.mp4", str(odd / "clip.mp4"), "missing.mp4", "huge.png"]:
        run(f"inspect {Path(f).name}", [P, str(IV), str(W / f) if not f.startswith("/") else f, str(W / "iv" / Path(f).stem)])
    run("inspect --at beyond end", [P, str(IV), str(odd / "clip.mp4"), str(W / "iv/at"), "--at", "99,-1,abc"])
    run("inspect --zoom beyond end", [P, str(IV), str(odd / "clip.mp4"), str(W / "iv/zoom"), "--zoom", "3.9,50"])
    run("inspect --every 0", [P, str(IV), str(odd / "clip.mp4"), str(W / "iv/ev0"), "--every", "0"])
    run("inspect --every -1", [P, str(IV), str(odd / "clip.mp4"), str(W / "iv/evn"), "--every", "-1"])
    run("inspect out_dir is a file", [P, str(IV), str(odd / "clip.mp4"), str(W / "fake.jpg")])
    IC = R / "ecom/skills/ecom/scripts/image_check.py"
    for f in ["huge.png", "dot.png", "transparent.png", "fake.jpg", str(odd / "img one.webp"), "noaudio.mp4", "missing.png", "zero.mp3"]:
        run(f"image_check {Path(f).name}", [P, str(IC), str(W / f) if not f.startswith("/") else f, "--out", str(W / "ic" / Path(f).stem), "--main", str(W / f) if not f.startswith("/") else f])
    run("image_check --main not in list", [P, str(IC), str(W / "dot.png"), "--out", str(W / "ic/x"), "--main", str(W / "huge.png")])
    SFX = R / "master/skills/master/scripts/sfx_mix.py"
    cues = {"empty.json": "", "list.json": "[]", "bad.json": "{", "obj.json": "{}",
            "unknown.json": json.dumps([{"t": 0.5, "type": "laser"}]), "late.json": json.dumps([{"t": 99, "type": "whoosh"}]),
            "neg.json": json.dumps([{"t": -1, "type": "whoosh"}]), "nulls.json": json.dumps([{"t": None, "type": None}])}
    for n, d in cues.items():
        (W / n).write_text(d)
        run(f"sfx_mix cues {n}", [P, str(SFX), "--cues", str(W / n), "--duration", "3", "--out", str(W / "sfx" / (n + ".wav"))])
    run("sfx_mix duration 0", [P, str(SFX), "--cues", str(W / "list.json"), "--duration", "0", "--out", str(W / "sfx/d0.wav")])
    run("sfx_mix duration -3", [P, str(SFX), "--cues", str(W / "list.json"), "--duration", "-3", "--out", str(W / "sfx/dn.wav")])
    run("sfx_mix vo missing", [P, str(SFX), "--cues", str(W / "list.json"), "--duration", "3", "--vo", str(W / "missing.wav"), "--out", str(W / "sfx/vm.wav")])
    run("sfx_mix vo text", [P, str(SFX), "--cues", str(W / "list.json"), "--duration", "3", "--vo", str(W / "text.mp3"), "--out", str(W / "sfx/vt.wav")])
    run("sfx_mix vo silence", [P, str(SFX), "--cues", str(W / "list.json"), "--duration", "3", "--vo", str(W / "silence.wav"), "--out", str(W / "sfx/vs.wav")])
    run("sfx_mix out in odd dir", [P, str(SFX), "--cues", str(W / "list.json"), "--duration", "3", "--out", str(odd / "mix out.wav")])
    RV = R / "master/skills/master/scripts/render_html_video.cjs"; RI = R / "ecom/skills/ecom/scripts/render_image.cjs"
    (W / "err.html").write_text("<html><body><script>throw new Error('boom')</script></body></html>")
    (W / "nofn.html").write_text("<html><body>no renderFrame</body></html>")
    (W / "hang.html").write_text("<html><body><script>window.READY=false</script></body></html>")
    for h in ["err.html", "nofn.html", "missing.html"]:
        run(f"render_video {h}", ["node", str(RV), str(W / h), str(W / "rv" / (h + ".mp4")), "--from", "0", "--to", "0.2", "--width", "64", "--height", "64"])
    run("render_video zero size", ["node", str(RV), str(R / "master/skills/master/templates/scene-template.html"), str(W / "rv/zero.mp4"), "--from", "0", "--to", "0.2", "--width", "0", "--height", "0"])
    run("render_video to<from", ["node", str(RV), str(R / "master/skills/master/templates/scene-template.html"), str(W / "rv/back.mp4"), "--from", "2", "--to", "1", "--width", "64", "--height", "64"])
    run("render_video odd size", ["node", str(RV), str(R / "master/skills/master/templates/scene-template.html"), str(odd / "out v.mp4"), "--from", "0", "--to", "0.3", "--width", "101", "--height", "77"])
    for h in ["err.html", "hang.html", "missing.html"]:
        run(f"render_image {h}", ["node", str(RI), str(W / h), str(W / "ri" / (h + ".png")), "--width", "200", "--height", "200"], timeout=90)
    run("render_image bad ext", ["node", str(RI), str(R / "ecom/skills/ecom/templates/comparison-chart.html"), str(W / "ri/x.gif"), "--width", "200", "--height", "200"])
    run("render_image width abc", ["node", str(RI), str(R / "ecom/skills/ecom/templates/comparison-chart.html"), str(W / "ri/y.png"), "--width", "abc"])
    # no ffmpeg on PATH
    GS = R / "master/skills/master/scripts/get_sounds.py"
    for args in (["fetch", "nope"], ["fetch", "sfx-kit", "--category", "nope", "--dest", str(W / "s")],
                 ["fetch", "sfx-kit", "--category", "money", "--dest", str(W / "fake.jpg")], ["find"],
                 ["credits", str(W / "missing.wav")], ["list", "--category", "nope"]):
        run("get_sounds " + " ".join(args[:3]), [P, str(GS), *args])
    nobin = W / "nobin"  # python and node, but no ffmpeg
    nobin.mkdir()
    for tool in (P, shutil.which("node")):
        (nobin / Path(tool).name).symlink_to(tool)
    nopath = {"PATH": str(nobin)}
    run("analyze without ffmpeg", [str(nobin / Path(P).name), str(AN), str(W / "silence.wav")], env=nopath)
    run("inspect without ffmpeg", [P, str(IV), str(odd / "clip.mp4"), str(W / "iv/nf")], env=nopath)
    run("image_check without ffmpeg", [P, str(IC), str(W / "dot.png"), "--out", str(W / "ic/nf")], env=nopath)
    (W / "x.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n\n2\n00:00:03,000 --> 00:00:04,000\nyo\n")
    run("get_sounds fetch without git", [P, str(GS), "fetch", "sfx-kit", "--category", "time", "--dest", str(W / "s2")], env=nopath)
    CL = R / "clipper/skills/clipper/scripts/clip.py"
    for label, args in (("clip render no audio", [str(W / "noaudio.mp4"), str(W / "x.srt"), "--spans", "0-3"]),
                        ("clip render truncated", [str(W / "truncated.mp4"), str(W / "x.srt"), "--spans", "0-3"]),
                        ("clip render odd path crop", [str(odd / "clip.mp4"), str(W / "x.srt"), "--spans", "0.5-3.5", "--frame", "crop", "--x", "1"]),
                        ("clip render beyond end", [str(odd / "clip.mp4"), str(W / "x.srt"), "--spans", "50-60"]),
                        ("clip render bad spans", [str(odd / "clip.mp4"), str(W / "x.srt"), "--spans", "3-1,abc"]),
                        ("clip render odd size", [str(odd / "clip.mp4"), str(W / "x.srt"), "--spans", "0-2", "--width", "101"]),
                        ("clip render text as video", [str(W / "text.mp3"), str(W / "x.srt"), "--spans", "0-2"]),
                        ("clip render hook braces", [str(odd / "clip.mp4"), str(W / "x.srt"), "--spans", "0-2", "--hook", "{\\b1}hi\\N\nthere"]),
                        ("clip render transcript binary", [str(odd / "clip.mp4"), str(W / "binary.bin"), "--spans", "0-2"])):
        run(label, [P, str(CL), "render", *args, "--out-dir", str(W / "cl" / label.replace(" ", "_"))])
    run("clip render without ffmpeg", [P, str(CL), "render", str(odd / "clip.mp4"), str(W / "x.srt"), "--spans", "0-2", "--out-dir", str(W / "cl/nf")], env=nopath)
    run("transcript_edit apply without ffmpeg", [P, str(R / "master/skills/master/scripts/transcript_edit.py"), str(W / "x.srt"), "--apply", str(odd / "clip.mp4"), str(W / "o.mp4")], env=nopath)


def main():
    global W
    with tempfile.TemporaryDirectory(prefix="sfy_chaos_") as tmp:
        W = Path(tmp)
        text_tools()
        if "--no-media" not in sys.argv:
            media_tools()
    bad = [r for r in results if r[0] != "ok"]
    for r in bad:
        print(*r[:3], "|", r[3])
    print(f"chaos: {len(results) - len(bad)} ok, {len(bad)} failed, {len(results)} runs")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
