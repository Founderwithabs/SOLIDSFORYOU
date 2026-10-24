# Design head

Makes the visuals and sound: videos and animations, AI-generated images
and clips, product graphics, and soundtracks.

## 1. When it runs

- Make or edit a video, reel, ad, explainer, animation, product video or
  GIF; make or fix an AI image or clip; design a product graphic; make or
  fix a soundtrack.

## 2. Sub-skills

| Sub-skill | Used for |
|---|---|
| Video workflow | Every video: `workflows/video.md` (plan, build, review, fix, re-render to the quality bar) |
| ai-visuals | AI-generated images and clips: brief, prompt, scorecard, optional generation |
| motion-design-taste | Taste before and after building any video; the founder's taste notes |
| audio-review | The sound of every video; voice-overs and music |
| ecom | Product graphics (infographics, comparison charts) and marketplace image rules |
| transcriber | Footage with speech: the transcript and captions the rough cut and subtitles start from |
| humanizer | Scripts and voice-overs that sound spoken, not generated |

Foundation: careful-mode on the brief and every delivery; economy-mode for
bulk steps; the memory sheet for brand rules.

## 3. Workflow

1. **What is the asset?** Video, AI image or clip, product graphic, or
   sound. A job can have several.
2. **Video:** footage with speech is transcribed first with transcriber
   (its `.srt` feeds the rough cut and the captions). Then follow
   `workflows/video.md` from start to finish. It runs
   economy-mode, careful-mode, motion-design-taste, audio-review and
   harsh-buyer-review itself, and takes marketplace rules from ecom and
   scripts from social-media.
3. **AI image or clip:** run ai-visuals: brief for the placement, fixed
   prompt, scorecard, and generation only if the founder agrees to the cost.
   Clips used in a video then go back into the video workflow.
4. **Product graphic:** use ecom's image module and templates, rendered in
   code at the marketplace's size.
5. **Sound:** audio-review, the video workflow's `sfx_mix.py` for effects
   under a voice-over, and its licence-checked sound library
   (`scripts/get_sounds.py`) for richer effects and background music, with
   the credit lines it gives.
6. **Scripts and voice-overs** go through the humanizer skill
   before recording: spoken words show machine phrasing even faster.
7. **Before delivery:** the Review head's check for the asset type (the
   video workflow already includes it).

## 4. Hand-offs

- Marketing head: the script, hook and posting plan for social videos.
- Ecom head: product facts, prices and the marketplace's rules.
- Review head: anything delivered without the video workflow.

## 5. Done when

The asset meets its quality bar (video: motion design taste 85 or more, no
criterion below 7; AI visual: ai-visuals' ready rule), and careful-mode
passed on the final file.
