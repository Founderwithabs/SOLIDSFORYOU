# SOLIDS FOR YOU sound library

Free sound effects and background music for business videos, gathered from
GitHub repositories whose licence was checked file by file (24 October 2026).
No memes, no game sounds, nothing with unclear rights. The audio isn't stored
here: `scripts/get_sounds.py` downloads only the folders a video needs, from
the commit that was checked, and refuses a download if its licence file has
changed. `library.json` is the full list, and also says which repos were
rejected and why.

```
python3 "SKILL_DIR/scripts/get_sounds.py" list                       # sources and categories
python3 "SKILL_DIR/scripts/get_sounds.py" fetch all --category transition logo-sting
python3 "SKILL_DIR/scripts/get_sounds.py" find whoosh soft           # search downloaded files
python3 "SKILL_DIR/scripts/get_sounds.py" credits used1.wav used2.mp3
```

A file path works anywhere `sfx_mix.py` takes a built-in sound name
(`{"t": 1.2, "sfx": "/path/to/whoosh.wav", "gain": 0.3}`), and a music
track goes through the ducking command in `workflows/video.md`.

## The sources

| Id | What | Files | Licence |
|---|---|---|---|
| `sfx-kit` | 320 sounds made for motion graphics and interfaces: whooshes, risers, logo stings, pops, money, data, typing; `sounds.json` describes each one | WAV | CC0 |
| `alvana` | 731 levelled sound effects (UI, notification, whoosh, riser, camera, keyboard, money) and 108 music tracks by mood, each with a beat map | WAV effects, MP3 music | CC0; `music-corporate` is CC BY |
| `creator-pack` | 38 sound effects for creators (typing, shutter, success chime, logo sting) and 9 background beds (tech explainer, upbeat vlog, lo-fi focus, screen bed) | MP3 | CC0 |
| `kenney-interface` | Kenney's 100 interface sounds: clicks, switches, confirmations, errors | WAV | CC0 |
| `kenney-packs` | Kenney's UI, digital and impact packs (416 sounds) | OGG | CC0 |
| `kenney-jingles` | Kenney's short pizzicato and hit jingles, and digital beeps | OGG | CC0 |
| `motion-basics` | 38 motion-graphics sounds: passes, stingers, sub hits, risers, UI clicks | WAV | CC0 |
| `elements-sfx` | 17 starter sounds for video (whoosh, riser, boom, shutter, success) | MP3 | CC0 (source not named) |
| `oculus-pack` | Professional UI, whoosh, designed and musical-sting sounds from Oculus | OGG | CC BY: credit required |
| `aeris-music` | 13 ambient and cinematic instrumental tracks | MP3 | CC0 (small publisher) |

## What to use for each kind of business video

| Video | Sound effects (categories) | Music (categories) |
|---|---|---|
| Product reveal or ad | `riser` into `impact`, `transition`, `shimmer`, `logo-sting` at the end | `music-upbeat`, `music-corporate`, `music-beds` (bgm_hook_loop_8s for short ads) |
| Explainer, SaaS or app demo | `ui`, `pop`, `notification`, `typing`, `data`, soft `transition` | `music-calm`, `music-beds` (bgm_tech_explainer, bgm_screen_bed), `music-corporate` |
| Stats, numbers, results | `data`, `money`, `pop`, `success` | `music-corporate`, `music-tech` |
| Reel or short | `transition` on every cut, `pop` for text, one `impact` for the key line | `music-upbeat`, `music-lofi` |
| Logo intro or outro | `logo-sting`, `shimmer`, `riser` | none, or the sting alone |
| Brand story, founder video, testimonial | very few: soft `transition` only | `music-calm`, `music-emotional`, `aeris-music` |
| E-commerce, unboxing | `foley`, `camera`, `pop`, `money` | `music-lofi`, `music-upbeat` |
| Podcast or YouTube intro | `logo-sting`, `riser` | `music-intro` |

## Rules

1. **Credit CC BY files.** Run `credits` on the files used and put every line
   it prints in the video description. CC0 files need no credit.
2. **Listen before you ship.** Run the `audio-review` skill on the final mix;
   sound effects sit about 10 to 15 dB under the voice, and music ducks under
   speech.
3. **Content ID.** Free music can still be claimed by mistake if someone
   registered it with YouTube's Content ID. If a claim appears, dispute it with
   the source and licence from `library.json`.
4. **Nothing outside the library** goes into a founder's video unless its
   licence was checked the same way (the licence file, not a website's
   summary). Never use the folders a source's `exclude` lists.
