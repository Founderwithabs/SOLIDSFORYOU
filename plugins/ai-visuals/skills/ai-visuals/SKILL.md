---
name: ai-visuals
description: Art director for AI-generated images and video (ChatGPT, Midjourney, Gemini, Flux, Ideogram, Firefly, Canva, Sora, Veo, Kling, Runway): reviews a result for its use (e-commerce, Instagram, LinkedIn, YouTube, ads, web), scores it, and gives the exact fixed prompt or edit with every change explained. Can generate with an OpenAI key.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. If the files came as text with no folder (for example from a
skill marketplace), save the ones a task needs to a temporary folder, never
the founder's project, and use that. Below, `SKILL_DIR` means that folder.

1. Follow `SKILL_DIR/ai-visuals.md`: the rules, the brief, how to read an
   image or video, prompt anatomy, diagnosis and fix ladder, scorecard,
   hand-back format and optional generation.
2. Read only what the task needs from `SKILL_DIR/purposes.md` (the
   placement's section) and `SKILL_DIR/generators.md` (the tool's section).
3. Use the scripts instead of doing it by eye or by hand:
   - `scripts/prompt_diff.py old.txt new.txt`: every change between two prompts
   - `scripts/score.py` followed by eight scores: the scorecard total and ready rule
   - `scripts/generate_openai.py`: optional generation or editing with the
     founder's `OPENAI_API_KEY` (costs money; ask first)
4. For product images use the `ecom` skill's image rules and
   `image_check.py`; for finished videos, `motion-design-taste`; for the
   post around the image, `social-media` (all SOLIDS FOR YOU, if installed).
