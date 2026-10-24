# What each placement needs

Sizes and rules change; treat these as starting points and check the
platform's current help pages before final export. "Safe zone" means the
area the platform's interface (buttons, captions, profile name) won't cover.

## 1. E-commerce

- **Main image (Amazon, Flipkart, Walmart and most marketplaces):** a real
  photo of the real product, usually on a pure white background with no
  text or props. **Don't use AI generation for the main image.** At most,
  use AI tools to clean up a real photo (background removal, dust), and
  keep the product untouched. Square, large enough for zoom (2,000 px is a
  safe target). See the SOLIDS FOR YOU `ecom` skill's images module.
- **Lifestyle and in-use images:** AI can build the scene around a real
  product photo (reference or edit mode), if the product stays exactly as it
  is and the scene doesn't imply anything untrue (size, included items,
  results). Check the marketplace's current rules on edited images.
- **Infographics, comparison charts, size charts, A+ modules:** generate or
  photograph the visuals, but add the text afterwards with a layout tool
  (the `ecom` skill's templates and `render_image.cjs`), because exact text,
  prices and measurements must be right. A+ module sizes vary by module;
  check the current ones.
- **Store banners and brand pages:** wide formats; check the marketplace's
  sizes; keep text in the centre.

## 2. Instagram

- **Feed post:** 4:5 portrait at 1080 × 1350 shows largest in the feed; the
  profile grid crops to a taller-than-square preview (check the current
  grid ratio), so keep the subject centred.
- **Carousel:** every slide the same size and template; slide 1 must work
  alone as the hook.
- **Stories and reels:** 9:16 at 1080 × 1920. Keep text and faces away from
  the top and bottom (roughly the top 14% and bottom 20%, check current
  guidance) where the profile name, caption and buttons sit.
- **Reel cover:** readable at grid and profile size.
- See the SOLIDS FOR YOU `social-media` skill for the post itself.

## 3. LinkedIn

- **Feed image:** 1200 × 627 (1.91:1) landscape, or square 1080 × 1080, or
  1080 × 1350 portrait for more feed space.
- **Document carousel:** a PDF, usually 1080 × 1350 or square pages.
- **Profile banner** 1584 × 396 and **company page cover**: check current
  sizes; the profile photo covers part of the banner's lower left.
- Tone: credible and specific. Stock-looking AI people hurt trust here more
  than anywhere; prefer real photos of the founder and team, or clean
  diagrams.

## 4. YouTube

- **Thumbnail:** 1280 × 720 (16:9). Readable at about 160 px wide: one
  subject, three words at most, high contrast. The duration stamp covers the
  bottom right. Pair it with the title (the `social-media` skill's
  `package_check.py`).
- **Channel banner:** check the current size and the safe area that shows on
  every device.

## 5. Other social

- **X:** single images about 16:9 (1600 × 900) show uncropped.
- **Pinterest:** 2:3 at 1000 × 1500.
- **TikTok:** 9:16 at 1080 × 1920; keep the right edge and bottom clear of
  buttons and caption.
- **Facebook:** feed 4:5 or 1:1; stories and reels 9:16.

## 6. Ads

- **Meta (Facebook and Instagram):** plan 1:1, 4:5 and 9:16 versions of the
  same creative; little text; the product and message readable in under a
  second. Check the current ad specs and AI-disclosure rules.
- **Google (Display and Performance Max):** several ratios, commonly
  1.91:1 (1200 × 628), 1:1 (1200 × 1200) and 4:5 (960 × 1200); some
  placements reject text-heavy images. Check current specs.
- **Marketplace ads:** product images follow the main-image rules; custom
  creative (brand banners) follows the ad console's specs.
- Never show results, testimonials or claims the founder can't prove.

## 7. Website, decks and print

- **Website hero:** wide (16:9 at 1920 × 1080 or wider); leave clear space
  for the headline and button; check how it crops on phones; compress for
  speed.
- **Pitch deck:** 16:9; visuals explain one point per slide; never AI
  "product screenshots" that look like a product that doesn't exist yet,
  unless clearly labelled as a concept.
- **Packaging and mockups:** label mockups as mockups; check print size,
  bleed and resolution (300 dpi at print size) with the printer.
