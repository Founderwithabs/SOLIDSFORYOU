# How to prompt and edit in each tool

These tools change fast: models, parameters and features are renamed,
added and retired every few months. Use this as the shape of each tool,
check its current documentation or interface for the exact names, and say
so in the hand-back if you couldn't check.

## 1. ChatGPT and the OpenAI image models

- **Prompt style:** plain, detailed sentences. Strong at following long
  instructions and at rendering text in quotes.
- **References:** upload images in the chat and say what each one is for
  ("keep this product exactly as it is; use this one only for the
  lighting").
- **Editing:** ask for a change in the same chat ("keep everything, only
  make the background warm grey"), or select an area in the image editor
  and describe the change there. Ask it to keep everything else unchanged.
- **Format:** state the aspect ratio; common sizes are square, portrait and
  landscape. Transparent backgrounds are available for some models (useful
  for product cut-outs and stickers).
- **API:** `generate_openai.py` in this skill (section 9 of `ai-visuals.md`).

## 2. Midjourney

- **Prompt style:** short descriptive phrases, most important first, then
  parameters at the end.
- **Parameters** (check the current version's list): `--ar` aspect ratio,
  `--stylize` or `--s` how much house style, `--chaos` variety, `--no` things
  to exclude, `--seed` repeatability, style references (`--sref`) and
  character or object references, and image weight for image prompts.
- **Editing:** Vary Region (or the editor) to repaint a selected area;
  Pan and Zoom to extend.
- **Watch:** text and exact product details are weaker; add text
  afterwards and use references for products.

## 3. Google Gemini and Imagen

- **Prompt style:** natural sentences. Gemini's image models are built for
  conversational editing and for keeping a product or character consistent
  across images from references; Imagen is for high-quality text-to-image.
- **Editing:** describe the change in the next message ("change only the
  background to..."), and ask it to keep the rest identical.
- **Watch:** check that small product details survive each edit round;
  compare against the real photo every time.

## 4. Flux (Black Forest Labs, in many apps)

- **Prompt style:** natural, specific sentences; it follows detailed
  descriptions well. Negative prompts usually aren't supported, so describe
  what you want instead of what you don't.
- **Editing and references:** the Kontext-style models edit from a
  reference image with an instruction; other apps offer inpainting.
- **Watch:** settings differ by the app hosting it (steps, guidance); note
  them so a result can be repeated.

## 5. Ideogram

- **Strength:** text in images (posters, labels, headlines).
- **Prompt style:** put the exact text in quotes and say where it goes.
  Turn off automatic prompt rewriting ("Magic Prompt") when the exact
  wording matters, or check what it changed.
- **Editing:** its canvas tools for region edits and extending the image.

## 6. Adobe Firefly and Photoshop

- **Strength:** editing real photos: Generative Fill for region edits,
  Generative Expand to change the format, and reference images for
  structure and style. Adobe states its models are trained for commercial
  use; check the current terms for the founder's case.
- **Best use for products:** keep the real product photo and change only
  the background or extend it.

## 7. Canva

- **Strength:** layouts with real, exact text, brand kits and many sizes
  from one design; AI generation and Magic Edit for images inside a layout.
- **Best use:** rung 3 in `ai-visuals.md` section 6: add headlines, prices
  and logos over a generated or real image.

## 8. Video: Sora, Veo, Kling, Runway and others

- **Prompt shape:** one shot per prompt: shot type and framing, the subject,
  **one** clear action over time, the camera's movement (static, slow push
  in, orbit, handheld), the setting and lighting, the style, the duration,
  and for tools that make sound (some Veo models do), the audio.
- **Image-to-video** from a real product photo or an approved still keeps
  the product and the first frame under control; prefer it for products.
- **Consistency:** use the tool's reference, character or style features to
  keep the same person or product across clips, and keep the same wording
  for them in every prompt.
- **Watch:** morphing between frames, flicker, hands, text (add it in the
  edit instead), physics, and the first second (it's the hook).
- **Finishing:** cut, add text, sound and captions in an editor or the
  SOLIDS FOR YOU `master` skill's video workflow, then review with
  `motion-design-taste`.

## 9. Writing the same prompt for a different tool

When moving a prompt to another tool, keep the content (the parts in section 5
in `ai-visuals.md`) and change the form: sentences or phrases, where the
aspect ratio and exclusions go (parameters or words), and how references are
attached. Say which tool each prompt is for.
