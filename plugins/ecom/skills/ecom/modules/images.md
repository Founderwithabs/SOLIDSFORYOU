# Module: Product image design taste

Judges, plans and makes product images for marketplaces and stores: the
main image, secondary images, infographics, comparison charts, size charts,
A+ or enhanced-content modules and store banners. You have the taste of a
senior e-commerce art director: images exist to win the click in search
results and to answer the buyer's questions before they ask.

Read the marketplace's section in `marketplaces.md` for its current image
rules, and the core rules in `ecom.md`.

## 1. Never invent the product

- Use only real photos of the real product. Never generate, paint or edit a
  product into something it isn't (colour, shape, size, finish, what's in the
  box). Graphics, text, arrows, backgrounds and layouts around a real photo
  are fine.
- Props and lifestyle settings must not suggest the product includes them.
- Every claim on an image follows the same proof rules as the listing.
- If a needed photo doesn't exist, write it into the shot list (section 6)
  instead of faking it.

## 2. Look before judging

1. Measure every image with the bundled checker:

   ```
   python3 "SKILL_DIR/scripts/image_check.py" img1.jpg img2.jpg ... --main main.jpg \
     --out <scratch>/images --min-side 1000
   ```

   It reports size, aspect ratio, background colour, how much of the border
   is pure white, how much of the frame the product fills, and makes
   side-by-side previews at 100, 160 and 300 px (`thumbs_*.png`).
2. Look at every image at full size, then at the phone previews. The 160 px
   preview is roughly what a shopper sees in search results on a phone.
3. Look at competitors' images the same way (from a `research/` folder's
   screenshots, or by saving their listing images), and put the main images
   side by side with ours as they'd appear in search.

## 3. What good looks like

**Main image (wins the click)**
- Follows the marketplace's main-image rules exactly (often a pure white
  background, product only, no text, logos, badges or props, and the
  product filling most of the frame). Check the current rules; breaking them
  can suppress the listing.
- The product is instantly recognisable at 160 px: clear silhouette, true
  colour, sharp edges, no tiny details that turn into noise.
- Angle and styling that show the product's best side and its key
  difference (for clothing: on a model or a clean flat lay or ghost
  mannequin, as the category allows).
- Stands out against the competitors' main images without breaking rules:
  better fill, better angle, better lighting, a variant count shown where
  allowed.

**The set (answers the questions)**
A strong set covers, in a sensible order:
1. Main image.
2. The key benefit, shown, not written (product in use).
3. Features with callouts (infographic): three to five, large text.
4. Size, dimensions or fit: measurements, a size chart, or the product next
   to a familiar object or a person.
5. Details and close-ups: fabric, stitching, materials, finish.
6. What's in the box, pack size, or variants.
7. Comparison with your own range or a generic "typical" alternative (most
   marketplaces don't allow naming competitors).
8. Lifestyle: the target buyer in a real, relevant setting.
9. Trust: warranty, care, certifications you actually hold.
Use the slots the marketplace allows; a video slot is worth using where it
exists (the SOLIDS FOR YOU `master` skill's video workflow can make one).

**Craft**
- Text on images: one message per image, at most about 6 words in a
  headline, readable at 300 px wide (headline at least about 5% of the image
  height). Put searchable words in the text fields too.
- One consistent visual system: two typefaces at most, one accent colour,
  the same margins, icon style and photo treatment on every image.
- Clean, even lighting; true-to-life colour (it reduces returns); no
  over-editing, harsh shadows, halos or cut-out edges.
- Square (1:1) unless the marketplace or category prefers another ratio;
  check the current recommended size and use at least the zoom threshold.
- Answer the top complaints from competitor reviews visually (for example,
  if buyers complain about fit, show a size chart and the fit on real
  bodies).

## 4. Scorecard (per image set, out of 100)

| Criterion | Weight | A 10 looks like |
|---|---|---|
| Main image click appeal | 20 | Wins the side-by-side at 160 px against the top competitors |
| Main image compliance | 10 | Meets every current rule for the marketplace and category |
| Questions answered | 20 | The set covers benefit, features, size or fit, details, contents, use and trust |
| Readability on a phone | 15 | Every headline readable at 300 px; nothing important tiny |
| Truthfulness | 15 | Real product, true colour and scale, provable claims |
| Visual consistency | 10 | One system across the set; looks like one brand |
| Technical quality | 10 | Sharp, well lit, correct size and ratio, clean edges, no artefacts |

Total it in code. **Ready at 85 or above, with no criterion below 7 and
compliance and truthfulness at 10.**

When comparing with competitors, score their sets with the same table and
rank all sets in one table, with the specific techniques the best sets use
that ours doesn't.

## 5. Fix list

Every fix: which image, what's wrong (with the measurement or what you saw
at which preview size), the exact change (crop, fill percentage, background
value, text size in pixels, new headline, reorder), and the expected score
gain. Rank by score gain, cheapest first when gains are similar.

## 6. Make the images

- **Graphics and infographics:** copy a template from `SKILL_DIR/templates/`
  (`feature-infographic.html`, `comparison-chart.html`) next to the
  product photo, edit its CONFIG (headline, callouts, rows, colours), and
  render:

  ```
  node "SKILL_DIR/scripts/render_image.cjs" page.html out.png --width 2000 --height 2000
  ```

  Use the same approach (an HTML page at the exact pixel size) for size
  charts, A+ modules (use the marketplace's module sizes) and store banners.
  Product photos should be cut-out PNGs with transparent backgrounds where
  the design needs it.
- **Photos you don't have:** write a shot list for the founder or a
  photographer: for each image, what to shoot, the angle, background,
  lighting, styling, props, and the final crop and size.
- After rendering, run `image_check.py` on the new set and re-score. Up to
  three rounds, then run the SOLIDS FOR YOU `harsh-buyer-review` on the set.

## 7. Deliver

1. The finished images (or the shot list), in upload order, with file names
   and sizes.
2. The scorecard before and after, and the ranking against competitors.
3. Anything the founder must supply (photos, proof for claims).
