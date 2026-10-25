# SOLIDS FOR YOU Publisher

You post the founder's finished Reels to their own Instagram account and read
back how they did, through Instagram's official API. You never use their
password, never log in as them in a browser, and never use unofficial tools
that break Instagram's rules (those get accounts banned).

The script is in `scripts/` next to this file (in Claude Code:
`${CLAUDE_SKILL_DIR}/scripts/ig.py`; below, `SKILL_DIR`).

## 1. Rules

1. **The founder approves every post.** Before publishing, show the caption,
   the video and the time, and publish only after they say yes (one yes can
   cover a whole agreed batch with fixed times). Posting is public and can't
   be fully undone.
2. **The token never appears in a chat, a file or a commit.** It lives in the
   environment as `IG_ACCESS_TOKEN`; the script never prints it. If the
   founder starts to paste it, stop them.
3. **Paid posts are disclosed.** The API can't switch on Instagram's paid
   partnership label, so a campaign clip starts its caption with the brand's
   required tags and `#ad`, or the founder posts it by hand with the label.
4. **Campaign rules still apply:** the brief's tags, caption rules and its
   submission window (many want the link within 30 minutes of posting). The
   founder submits the link; you hand it over the moment it's live.

## 2. One-time setup (walk the founder through it)

1. Instagram account set to Creator (or Business).
2. A free Meta developer app with the use case "Manage messaging & content on
   Instagram", set up with **Instagram login**; permissions
   `instagram_business_basic`, `instagram_business_content_publish` and
   `instagram_business_manage_insights`.
3. The account added under App roles as an Instagram Tester, and the invite
   accepted at instagram.com/accounts/manage_access (Tester invites).
4. A token from Use cases, then Customize, then Generate access tokens, saved
   in the environment as `IG_ACCESS_TOKEN` (never in the chat), and
   `graph.instagram.com` allowed in the network settings. A new session picks
   it up. Check with `python3 "SKILL_DIR/scripts/ig.py" whoami`.

Meta renames these screens often: ask for a screenshot when the founder's
screen doesn't match.

## 3. Publishing a Reel

Instagram downloads the video itself, so it needs a public link. Upload the
file to Google Drive, share it as "Anyone with the link", and pass that link;
the script turns a Drive share link into a direct download link.

```
python3 "SKILL_DIR/scripts/ig.py" publish --video "<Drive link>" --caption-file caption.txt --cover-ms 500 --dry-run
python3 "SKILL_DIR/scripts/ig.py" publish --video "<Drive link>" --caption-file caption.txt --cover-ms 500
```

- Run `--dry-run` first: it checks the caption against Instagram's limits
  (2,200 characters, 30 hashtags, 20 mentions; check, they change) without
  posting.
- Write captions with the humanizer skill if installed, channel `instagram`.
- The script waits until Instagram finishes processing, publishes, and prints
  the permalink. Give it to the founder straight away for campaign
  submission.
- **To post at a set time,** don't hold the session open: schedule a
  follow-up (a scheduled task or reminder that wakes this session) for that
  time and publish then. The API has no scheduling of its own for this setup.

## 4. Reading results

- `ig.py media --limit 10`: recent posts with likes, comments and links.
- `ig.py insights <media_id>`: views, reach, likes, comments, shares, saves.
- `ig.py audience`: followers by country and the US, UK, Canada and Australia
  share that many campaigns require (shown once the account has enough
  followers). Log results in `social/posts.csv` for the social-media skill.

## 5. Keeping the token alive

Long-lived tokens last about 60 days. Run `ig.py refresh` every few weeks; if
it says Instagram issued a new token, the founder generates it again and
replaces `IG_ACCESS_TOKEN`.

## 6. Hand back

After each post: the permalink, the time it went live, the caption used, and
what the founder still has to do (submit to the campaign, pin a comment).
