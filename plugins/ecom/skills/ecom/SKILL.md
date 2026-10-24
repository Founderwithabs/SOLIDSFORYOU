---
name: ecom
description: E-commerce operator for any marketplace or own store: listings, product image review and rendering, unit economics, fees, margins, pricing, discounts, ads reports (ACoS, TACoS), returns, stock and launches, on Amazon, Walmart, eBay, Etsy, TikTok Shop, Shopify, Flipkart, Meesho and more. Use for anything about selling online or business economics.
---

The files this skill uses sit next to this SKILL.md. In Claude Code that
folder is `${CLAUDE_SKILL_DIR}`; anywhere else, use the folder this file was
loaded from. Below, `SKILL_DIR` means that folder.

1. Read `SKILL_DIR/ecom.md` (the core: rules, which module to use, store
   memory and how the modules connect). Load the founder's store memory as
   it says.
2. Load only the module the task needs, when you reach it:
   - `SKILL_DIR/modules/listing.md`: listings
   - `SKILL_DIR/modules/images.md`: product images
   - `SKILL_DIR/modules/economics.md`: unit economics and pricing
   - `SKILL_DIR/modules/operations.md`: reports, ads, returns, stock,
     launches, sale events, expansion
   and only the marketplace's section of `SKILL_DIR/marketplaces.md`, for
   example Amazon with the tax and law reminders:
   `python3 "SKILL_DIR/scripts/read_sections.py" "SKILL_DIR/marketplaces.md" 1 2 17`
   Sections: 1 how to use, 2 Amazon, 3 Walmart, 4 eBay, 5 Etsy, 6 TikTok
   Shop, 7 own store, 8 Flipkart, 9 Meesho, 10 Myntra and Ajio, 11 Nykaa,
   12 Shopee and Lazada, 13 Mercado Libre, 14 Noon, 15 Zalando, 16 Allegro,
   Rakuten and others, 17 tax and law. Always include 1; add 17 for
   pricing, tax or legal questions.
3. Do every calculation with the bundled scripts (Python 3; the image tools
   also need ffmpeg, and rendering needs Node.js with Playwright):
   - `scripts/economics.py`: fee profiles, unit economics, break-even and
     target prices, price sweeps, channel comparison
   - `scripts/ops.py`: ads, returns and reorder reports
   - `scripts/listing_check.py`: listing lengths, keywords, risky words
   - `scripts/image_check.py`: image measurements and phone-size previews
   - `scripts/render_image.cjs` with `templates/`: render infographics and
     charts
   - `scripts/read_sections.py`: print only the sections of a guide you need
4. Save store memory in the project's `ecom/` folder, or in
   `${CLAUDE_PLUGIN_DATA}/ecom/` when there is no project. Never save inside
   the plugin folder.
5. Use the other SOLIDS FOR YOU tools where `ecom.md` says, if installed:
   competitor-research, harsh-buyer-review, careful-mode, social-media and the
   master skill's video workflow.
