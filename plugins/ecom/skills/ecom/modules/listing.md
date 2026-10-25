# Module: Marketplace listing builder

Builds or fixes a complete listing for one product on one marketplace, ready
to paste field by field. Read the marketplace's section in `marketplaces.md`
first, and the core rules in `ecom.md`.

## 1. Inputs (gather before writing)

1. **Product facts** from `products.csv`, `store.md` and the founder:
   materials, sizes, dimensions, weight, what's in the box, care, origin,
   certifications, warranty. Mark every fact you don't have as a gap.
2. **Competitor research**: a `research/` folder from SOLIDS FOR YOU
   `competitor-research` (or a short version: the top 5 to 10 listings for
   the main search phrase, with their titles, prices, claims and top
   complaints, each with a link and date).
3. **The marketplace's current rules** for this category: title length and
   format, bullet count and length, banned words, required attributes,
   search-term limits. Check the seller help pages or category style guide
   and note the date.
4. **Search words buyers use**, from: the marketplace's search box
   suggestions for the main phrase; competitor titles and bullets; the words
   in competitor reviews (how buyers describe the product and its problems);
   the founder's search term or ads reports if they have them.

## 2. Keyword map

Write a table: keyword, type (`primary`, `secondary`, `attribute`,
`long-tail`, `use-case`), where it goes (title, bullets, description,
backend, attributes), and the evidence (suggestion, competitor, review,
report). Rules:
- One primary phrase, the one most buyers type for exactly this product.
- Never use competitor brand names, trademarks you don't own, or
  irrelevant popular words. Marketplaces suppress or remove listings for it.
- Don't repeat the same word many times; most marketplaces index a word once.

## 3. Write the fields

**Title.** Follow the marketplace's current formula (usually brand, product
type, key attribute, then variant details such as size, colour or count).
Put the primary phrase early. Readable as a sentence, not a list of
keywords. Within the current length limit for the category; mobile shows
far less, so the first 60 to 80 characters must work on their own.

**Bullets or key features.** One benefit per bullet, in order of what
buyers care about most (use the competitor complaints and review language).
Start with a short label in capitals or bold if the marketplace's style
allows it, then the benefit, then the proof (material, measurement, test).
Answer the top objections directly: fit and sizing, quality, what's in the
box, care, returns or warranty. No claims you can't prove.

**Description.** Expands on the product, use cases, care and what's in the
box. On marketplaces with enhanced content (A+), plan that instead (section
5) and keep the plain description short and factual.

**Backend search terms** (where the marketplace has them): words that
aren't already in the title and bullets: synonyms, other spellings, other
languages buyers use, use cases. No punctuation padding, no repeats, no
brand names you don't own, within the byte or character limit.

**Attributes and item specifics.** Fill every one that applies. Shoppers
filter by them (size, colour, material, fit, pattern, occasion, age group),
and an empty attribute can hide the listing from filtered search.

**Variations.** Group sizes, colours and pack counts under one parent where
the marketplace allows, so reviews and ranking are shared. Use the
marketplace's variation themes exactly.

## 4. Check the text in code

Run the bundled checker (next to this skill's SKILL.md):

```
python3 "SKILL_DIR/scripts/listing_check.py" listing.json --keywords keywords.txt \
  --avoid brands.txt --limits title=200,bullet=500,description=2000,search_terms=250
```

`listing.json` holds `{"title": "...", "bullets": [...], "description":
"...", "search_terms": "..."}`. `brands.txt` lists the competitor brands and
trademarks from the research, one per line; any found is a problem to fix.
Use the limits you confirmed for this marketplace and category. It reports
length in characters and bytes, words repeated, keywords covered and
missing, and risky words (superlatives, guarantees, health and environmental
claims, urgency words, competitor-style terms) to check against the rules.

## 5. Images and A+ content plan

Plan the image set with `modules/images.md`. For A+ or enhanced brand
content: list the modules in order (brand story, feature highlights,
comparison chart of your own range, how to use, size or fit guide, care),
each with its headline, text and the image it needs. Keep text in images
large and short; put searchable text in the text fields too, because text
inside images usually isn't indexed.

## 6. Listing scorecard (out of 100)

| Criterion | Weight | A 10 looks like |
|---|---|---|
| Search relevance | 20 | Primary phrase early in the title, keyword map covered, attributes complete |
| Click appeal | 15 | Title readable on mobile; main image (images module) wins in search results |
| Conversion | 20 | Bullets answer the real objections from reviews; proof for every claim; images show what buyers need |
| Accuracy and proof | 15 | Every fact sourced from the founder or tested; no gaps hidden |
| Differentiation | 10 | Clear reason to choose this over the top three competitors |
| Compliance | 10 | Within current limits; no banned words, misleading claims or competitor terms |
| Readability | 10 | Plain words, scannable on a phone, consistent with the brand voice |

Total it in code (weights × scores ÷ 10). **Ready at 85 or above, with no
criterion below 7 and compliance at 10.** Then run the SOLIDS FOR YOU
`harsh-buyer-review` on the full listing and images (it can use the same
research folder), fix what it finds, and re-score. Up to three rounds.

## 7. Deliver

1. The listing, field by field, ready to paste, with the character count of
   each field from the checker.
2. The keyword map.
3. Gaps the founder must fill (facts, photos, certifications).
4. The scorecard and the harsh buyer's verdict.
5. What to measure after it goes live (sessions, conversion rate, search
   rank for the primary phrase, return reasons) and when to review.
Save the approved version to `ecom/listings/<sku>-<channel>.md`.
