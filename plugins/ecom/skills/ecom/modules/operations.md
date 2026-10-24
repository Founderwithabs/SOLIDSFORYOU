# Module: Store operations

Runs the store after the listing is live: reports, ads, returns, reviews,
stock, account health, launches, sale events and new marketplaces. Every
number comes from `ops.py`, `economics.py` (next to this skill's SKILL.md)
or your code tool.

## 1. Sales and traffic reports

Ask for the marketplace's business or sales report (sessions or page views,
units, orders, revenue, conversion) for a recent period and a comparison
period. Compute in code: conversion rate (orders or units ÷ sessions),
average order value, revenue per session, and the change against the
comparison period. Diagnose in this order:
1. **Traffic down?** Search rank for the primary phrase, ad spend changes,
   suppressed or stranded listings, stock-outs, seasonality, a competitor's
   new launch or price cut.
2. **Conversion down?** Price against competitors, lost featured offer or
   buy box, rating or new negative reviews, delivery promise, images or
   listing changes, out-of-stock variants.
3. **Order value down?** Pack mix, bundles, discounts.
Name the most likely cause with evidence, and what to check next.

## 2. Advertising

```
python3 "SKILL_DIR/scripts/ops.py" ads report.csv --breakeven-acos <from economics> --total-sales <all sales>
```

It works out spend, ad sales, ACoS, ROAS, CPC, CTR and conversion per
campaign (or ad group, keyword or search term, depending on the report) and
in total, flags rows above break-even and rows with spend but no sales, and
gives TACoS. Then recommend, with numbers:
- **Cut or lower bids** on rows above break-even with enough clicks to judge.
- **Add negatives** for irrelevant search terms with spend and no sales.
- **Scale** rows well below break-even with room to grow.
- **Harvest** converting search terms from automatic or broad campaigns into
  exact-match campaigns.
"Enough clicks to judge" depends on conversion rate: with a 10% conversion
rate, 20 clicks with no order is a warning; 40 is a signal. Say how
confident you are.

## 3. Returns and reviews

```
python3 "SKILL_DIR/scripts/ops.py" returns returns.csv --orders <orders in the period>
```

Group the reasons, then fix the cause, not the symptom: size and fit returns
call for a better size chart, fit images and size advice in the listing;
"not as described" calls for truer images and copy; damage calls for
packaging; quality calls for the product or supplier.

Reviews: read the recent and the critical reviews (or use the
`competitor-research` review codebook on your own product) to find themes.
Reply where the marketplace allows, helpfully and without arguing. Ask for
reviews only through the marketplace's own tools and rules; never offer
rewards, ask only happy buyers, or post or buy reviews.

## 4. Stock

```
python3 "SKILL_DIR/scripts/ops.py" reorder --daily-sales <units a day> --lead-days <days> \
  --on-hand <units> [--inbound <units>] [--safety-days 14] [--cover-days 60]
```

Use recent daily sales (adjusted for seasonality and planned promotions),
the real supplier and shipping lead time, and stock already on its way. Flag
stock-out risk before sale events. For marketplace fulfilment, check the
current storage limits, long-term storage fees and inbound rules.

## 5. Account health

Each marketplace has its own seller performance metrics (for example order
defect, late dispatch, cancellation and return rates) and policy warnings.
Ask the founder for their dashboard, compare each metric with the
marketplace's current target (check it), and treat anything near a
threshold as urgent. Never suggest ways around a policy; suggest how to fix
the underlying problem and, for appeals, a factual plan of action.

## 6. Launch plan

For a new product or channel, a checklist with owners and dates:
1. Research and economics done (`competitor-research`, `modules/economics.md`).
2. Listing and images approved (`modules/listing.md`, `modules/images.md`,
   `harsh-buyer-review`).
3. Stock in place and shipping set; returns policy decided.
4. Launch price and launch discount (with the discount maths).
5. Ads: campaign structure, daily budget, target and break-even ACoS, and
   when to review (daily for the first two weeks).
6. Getting the first reviews through the marketplace's official programmes
   only.
7. Launch content (SOLIDS FOR YOU `social-media`, and a product video with
   the `master` skill's video workflow).
8. What to measure in weeks 1, 2 and 4, and the decision each one triggers.

## 7. Sale events and seasons

Plan around the big events in the founder's markets (for example Prime Day,
Great Indian Festival, Big Billion Days, Diwali, Black Friday and Cyber
Monday, 11.11, Ramadan and White Friday, Christmas, end-of-season sales).
For each: stock needed (`ops.py reorder` with the expected lift), deal price
and its profit (`economics.py`), deal and coupon rules and deadlines (check
them; they're often weeks before the event), and the ad budget.

## 8. New marketplace or country

Before expanding: the marketplace's section in `marketplaces.md`; demand and
competitors (`competitor-research`); a fee profile and economics at a
realistic price; legal and tax requirements (registration, product safety
and labelling, the importer or responsible person; say a qualified advisor
should confirm); logistics and returns; and a go/no-go with the numbers.

## 9. Deliver

Lead with what to do this week, ranked by impact, with the numbers behind
each action. Then the analysis. Save measured lessons, with dates, to
`ecom/learnings.md`.
