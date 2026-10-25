# Example: the Agensi demo videos for Ecom and Careful mode

Two 32-second demo videos for the Agensi listings, made with the Master
Skill's video workflow in the launch video v2 style (see
[`../launch-video`](../launch-video)):

- [`ecom-demo.mp4`](../../assets/agensi/ecom-demo.mp4): a listing checked
  for risky claims and a competitor brand, the profit on one order as a
  waterfall, an ads report, and the marketplaces it covers.
- [`careful-mode-demo.mp4`](../../assets/agensi/careful-mode-demo.mp4):
  the three reviews (a wrong price found, a missing requirement added, an
  action that can't be undone held for a yes), the restart rule and the
  review record.

1920 × 1080, 30 fps, -14 LUFS. They work on mute.

## No invented claims

- Every number in the Ecom video is real script output:
  - `listing_check.py` on an illustrative listing;
  - `economics.py` on its example fee profile (₹999 sale, ₹245.29 profit per order);
  - `ops.py ads` on an example report.
  Each is labelled on screen.
- The work being checked in the Careful mode video is labelled illustrative.
  The review record uses the format from the skill.

## Scores (motion design rubric)

| Video | Draft | Final |
|---|---|---|
| Ecom | 81 | 86 |
| Careful mode | 82 | 86 |

Fixes between rounds:
- A grid that bled into the end card.
- Longer ads and record scenes.
- 22 px labels raised to 24 to 26 px.
- "Listings that pass the rules" changed to "Every listing, checked first",
  since the checker flags problems rather than guaranteeing a pass.
- Music EQ'd for phone speakers.

## Sound

All CC0, from the SOLIDS FOR YOU sound library, so no credit is required:
- Music: "Dear Mr Super Computer" by HoliznaCC0 (alvana-audio), from 7.363 s.
- Effects: wyzowl/sfx-kit.

## Rebuild

`source/` holds the two scenes, the beat grid and the sound cues.
1. Replace `__BEATS__` in a scene with the `beats` list from `beats.json`.
2. Fetch the sounds with `get_sounds.py fetch sfx-kit` and
   `get_sounds.py fetch alvana --category music-tech`.
3. Mix with `sfx_mix.py`, using the music as `--vo`.
4. Render with `render_html_video.cjs`.
