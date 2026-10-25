#!/usr/bin/env python3
"""ig.py - post Reels to the founder's own Instagram account and read its numbers, through
Instagram's official API (Instagram API with Instagram Login). No passwords, no scraping.

    python3 ig.py whoami
    python3 ig.py publish --video <public https link or Google Drive share link> --caption-file caption.txt
        [--caption "text"] [--cover-ms 1500] [--no-feed] [--dry-run]
    python3 ig.py status <container_id>
    python3 ig.py media [--limit 10]
    python3 ig.py insights <media_id>
    python3 ig.py audience
    python3 ig.py refresh

The access token is read from the IG_ACCESS_TOKEN environment variable and is never printed.
IG_USER_ID is optional (looked up with whoami). IG_API_BASE overrides https://graph.instagram.com.
Instagram fetches the video itself, so --video must be a public https link: a Google Drive file
shared as "Anyone with the link" works (its share link is turned into a direct download link).
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Windows pipes default to a legacy code page: print ₹, Hindi and emoji as UTF-8 instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BASE = os.environ.get("IG_API_BASE", "https://graph.instagram.com").rstrip("/")
MAX_CAPTION, MAX_TAGS, MAX_MENTIONS = 2200, 30, 20   # Instagram's caption limits (check: they change)


def token():
    t = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not t:
        sys.exit("IG_ACCESS_TOKEN isn't set. Add the token in the environment settings (never paste it "
                 "into a chat), then start a new session so it is picked up.")
    return t


def call(method, path, params=None, timeout=60):
    params = dict(params or {})
    params["access_token"] = token()
    data = urllib.parse.urlencode(params).encode()
    url = f"{BASE}/{path.lstrip('/')}"
    if method == "GET":
        url, data = url + "?" + data.decode(), None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode()).get("error", {})
            msg = err.get("error_user_msg") or err.get("message") or str(e)
        except (ValueError, AttributeError):
            msg = str(e)
        sys.exit(f"Instagram said no ({e.code}): {scrub(msg)}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        sys.exit(f"can't reach {BASE}: {getattr(e, 'reason', e)}. Is graph.instagram.com in the allowed domains?")
    except ValueError:
        sys.exit("Instagram sent back something that isn't JSON; try again in a minute")


def scrub(text):
    t = os.environ.get("IG_ACCESS_TOKEN", "")
    return str(text).replace(t, "<token>") if t else str(text)


def user_id():
    uid = os.environ.get("IG_USER_ID", "").strip()
    if uid:
        return uid
    me = call("GET", "me", {"fields": "user_id,username"})
    uid = str(me.get("user_id") or me.get("id") or "")
    if not uid:
        sys.exit("couldn't find the account id; check the token's permissions")
    return uid


def direct_link(url):
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=download&)?id=)([\w-]{10,})", url)
    if m:
        return f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
    return url


def check_caption(text):
    problems = []
    if len(text) > MAX_CAPTION:
        problems.append(f"caption is {len(text)} characters; Instagram allows {MAX_CAPTION}")
    tags = re.findall(r"(?<!\w)#\w+", text)
    if len(tags) > MAX_TAGS:
        problems.append(f"{len(tags)} hashtags; Instagram allows {MAX_TAGS}")
    mentions = re.findall(r"(?<!\w)@[\w.]+", text)
    if len(mentions) > MAX_MENTIONS:
        problems.append(f"{len(mentions)} @mentions; Instagram allows {MAX_MENTIONS}")
    return problems


def wait_ready(cid, tries=60, pause=5.0):
    for _ in range(tries):
        st = call("GET", cid, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return st
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram couldn't process the video ({code}): {st.get('status', 'no detail')}. "
                     "Check the link opens the video file for anyone, and the video is 3 s to 15 min, 9:16, MP4.")
        time.sleep(pause)
    sys.exit(f"still processing after {int(tries * pause)} s; check later with: ig.py status {cid}")


def take(a, flag, default=None):
    if flag not in a:
        return default
    i = a.index(flag)
    if i + 1 >= len(a):
        sys.exit(f"{flag} needs a value")
    v = a[i + 1]
    del a[i:i + 2]
    return v


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if a else 1)
    cmd, a = a[0], a[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    out = None
    if cmd == "whoami":
        me = call("GET", "me", {"fields": "user_id,username,account_type,media_count,followers_count"})
        uid = str(me.get("user_id") or me.get("id") or "")
        try:
            quota = call("GET", f"{uid}/content_publishing_limit", {"fields": "quota_usage,config"})
            q = (quota.get("data") or [{}])[0]
            me["posts_left_today"] = (q.get("config", {}).get("quota_total", 0) or 0) - (q.get("quota_usage", 0) or 0)
        except SystemExit:
            me["posts_left_today"] = "unknown"
        out = me
    elif cmd == "publish":
        video = take(a, "--video")
        cap_file = take(a, "--caption-file")
        caption = take(a, "--caption", "")
        cover = take(a, "--cover-ms")
        feed = "--no-feed" not in a
        dry = "--dry-run" in a
        if not video:
            sys.exit("publish needs --video with a public https link (a Google Drive link shared with anyone works)")
        if not re.match(r"https?://", video):
            sys.exit("Instagram fetches the video itself, so --video must be a public https link, not a file "
                     "on this machine. Upload it to Google Drive, share as 'Anyone with the link', pass that link.")
        if cap_file:
            try:
                raw = open(cap_file, "rb").read()
            except OSError as e:
                sys.exit(f"can't read {cap_file}: {e.strerror}")
            if b"\x00" in raw:
                sys.exit(f"{cap_file} isn't a text file")
            caption = raw.decode("utf-8", errors="replace").strip()
        problems = check_caption(caption)
        if problems:
            sys.exit("caption refused: " + "; ".join(problems))
        if cover is not None and not cover.isdigit():
            sys.exit("--cover-ms is the cover frame's time in milliseconds, e.g. 1500")
        params = {"media_type": "REELS", "video_url": direct_link(video), "caption": caption,
                  "share_to_feed": "true" if feed else "false"}
        if cover is not None:
            params["thumb_offset"] = cover
        if dry:
            out = {"dry_run": True, "video_url": params["video_url"], "caption_chars": len(caption),
                   "share_to_feed": feed, "cover_ms": cover}
        else:
            uid = user_id()
            cid = call("POST", f"{uid}/media", params).get("id")
            if not cid:
                sys.exit("Instagram didn't return a container id")
            wait_ready(cid)
            mid = call("POST", f"{uid}/media_publish", {"creation_id": cid}).get("id")
            link = call("GET", mid, {"fields": "permalink"}).get("permalink", "") if mid else ""
            out = {"published": bool(mid), "media_id": mid, "permalink": link, "container_id": cid}
    elif cmd == "status":
        if not a:
            sys.exit("status needs the container id")
        out = call("GET", a[0], {"fields": "status_code,status"})
    elif cmd == "media":
        lim = take(a, "--limit", "10")
        if not lim.isdigit() or not 1 <= int(lim) <= 50:
            sys.exit("--limit is a number from 1 to 50")
        out = call("GET", f"{user_id()}/media", {"fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
                                                 "limit": lim}).get("data", [])
    elif cmd == "insights":
        if not a:
            sys.exit("insights needs the media id (from publish or media)")
        res = call("GET", f"{a[0]}/insights", {"metric": "views,reach,likes,comments,shares,saved,total_interactions"})
        out = {m.get("name"): (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value"))
               for m in res.get("data", [])}
    elif cmd == "audience":
        res = call("GET", f"{user_id()}/insights", {"metric": "follower_demographics", "period": "lifetime",
                                                   "metric_type": "total_value", "breakdown": "country"})
        rows = []
        for m in res.get("data", []):
            for b in (m.get("total_value", {}).get("breakdowns") or []):
                for r in b.get("results", []):
                    rows.append((r.get("dimension_values", ["?"])[0], r.get("value", 0)))
        total = sum(v for _, v in rows) or 0
        rows.sort(key=lambda x: -x[1])
        tier1 = sum(v for c, v in rows if c in ("US", "GB", "CA", "AU"))
        out = {"followers_counted": total, "top_countries": rows[:10],
               "us_uk_ca_au_share": round(100 * tier1 / total, 1) if total else None,
               "note": "Instagram only shows follower countries once the account has enough followers (about 100)."}
    elif cmd == "refresh":
        res = call("GET", "refresh_access_token", {"grant_type": "ig_refresh_token"})
        days = int(res.get("expires_in", 0)) // 86400
        same = res.get("access_token") == os.environ.get("IG_ACCESS_TOKEN")
        out = {"refreshed": bool(res.get("access_token")), "valid_for_days": days,
               "action": "nothing to do" if same else "Instagram issued a new token: generate it again in the developer "
                                                     "dashboard and replace IG_ACCESS_TOKEN in the environment settings."}
    else:
        sys.exit(f"unknown command {cmd!r}; see ig.py --help")
    if as_json:
        print(scrub(json.dumps(out, ensure_ascii=False, indent=1)))
    elif isinstance(out, dict):
        for k, v in out.items():
            print(f"  {k}: {scrub(v)}")
    else:
        for row in out or []:
            print("  " + scrub(json.dumps(row, ensure_ascii=False)))


if __name__ == "__main__":
    main()
