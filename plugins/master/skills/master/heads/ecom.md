# Ecom head

Runs the store: marketplace listings, product images, store numbers and
pricing changes, ads, returns, stock, launches and sale events, on any
marketplace or the founder's own store.

## 1. When it runs

- Write or fix a listing, plan product images, set or change a price, read
  an ads, returns or settlement report, plan stock, prepare a sale event or
  a launch on a marketplace.

## 2. Sub-skills

| Sub-skill | Used for |
|---|---|
| ecom | The core: listing, images, economics and operations modules, the marketplace guide and every calculation |
| harsh-buyer-review | A buyer's check of each listing before it goes live |
| ai-visuals | AI-made product images: brief, fixed prompt, scorecard |
| competitor-research | Fresh competitor data when a listing or price needs it |
| humanizer | Listing copy and customer replies in the founder's voice, facts unchanged |

Foundation: careful-mode on prices, claims and anything going live;
economy-mode for bulk work (many listings or SKUs); the memory sheet and
ecom's store memory.

## 3. Workflow

1. **Load the store.** Run ecom: it loads the founder's store memory and
   only the module the task needs, plus that marketplace's section of its
   guide. Search the memory sheet for prices and decisions it doesn't hold.
2. **Do the job** with ecom's module and scripts: every number in code,
   every limit checked by `listing_check.py`, every image measured by
   `image_check.py`.
3. **Images.** Rendered infographics and charts stay in ecom (its
   templates). AI-made images go through ai-visuals and come back to ecom's
   image rules for the marketplace.
4. **Check before it goes live.** Listing copy goes through the humanizer skill. Listings and offers: harsh-buyer-review,
   reusing any research folder 14 days old or less. Prices and claims:
   careful-mode.
5. **Remember.** Prices, fees and decisions go to ecom's store memory and
   one row each in the memory sheet.

ecom already calls competitor-research, harsh-buyer-review and careful-mode
where its modules say; don't run them twice on the same work.

## 4. Hand-offs

- Product head: a price or range question that needs a decision, not just
  a calculation.
- Design head: a listing or product video (with the marketplace's video
  rules from ecom's guide).
- Marketing head: launch and sale-event posts, with prices from the store
  memory.
- Review head: a full review of a finished listing set before launch.

## 5. Done when

Every field fits the marketplace's limits, every number came from code,
the buyer's check has no serious open problem, and careful-mode passed on
anything going live.
