# Module: Unit economics and pricing

Answers money questions for an e-commerce business: what each sale really
earns on each channel, the lowest safe price, the right price, how much can
go on ads, which pack sizes and bundles make sense, and what a discount
costs. Every number comes from `economics.py` (next to this skill's
SKILL.md) or your code tool, never mental arithmetic.

## 1. Build the fee profile first

One JSON file per channel in `ecom/fees/<channel>.json`. Start from the
template:

```
python3 "SKILL_DIR/scripts/economics.py" template > ecom/fees/<channel>.json
```

Fill it from the best source available, in this order:
1. **The founder's settlement or payout report** for a recent period: the
   real fees charged per order, including shipping, closing or fixed fees,
   payment fees and tax on fees. Best, because it reflects their category,
   weight and programmes.
2. **The marketplace's current rate card** for the founder's country and
   category, from the marketplace's own seller site. Record the URL.
3. **The founder's own numbers** (for own stores: payment gateway, shipping
   partner, app costs).

Every profile needs `source` and `checked_at`; `economics.py` warns when a
profile is older than 30 days or still has template values. Model
everything the channel charges:
- `fees`: `percent` (of price, or `price_ex_tax`), `percent_tiers` and
  `fixed_tiers` (by price band), `weight_tiers` (by weight in grams) and
  `fixed`. Tiers list `up_to` limits in order, with `null` for "and above".
- `tax`: `inclusive` where listed prices include GST or VAT (India, EU, UK
  and most of the world); `exclusive` where tax is added at checkout (US
  sales tax). Tax charged on marketplace fees, and whether the founder can
  claim it back.
- `returns`: return rate, cost per return (reverse shipping plus fees not
  refunded) and the share of returned units that can't be resold.
- `ads`: ad spend as a share of sales (TACoS) or a cost per order.

Product costs come from `products.csv`: unit cost, packaging, inbound
freight and duties per unit, weight and pack quantity.

## 2. Unit economics

```
python3 "SKILL_DIR/scripts/economics.py" unit --fees ecom/fees/<channel>.json [more channels...] \
  --products ecom/products.csv --sku <SKU> [--price 999] [--target-margin 25] \
  [--sweep 799,899,999,1099]
```

It gives, per order placed: revenue after tax, fees, returns, product
cost, packaging, ads and profit; margin and return on product cost;
break-even ad spend (TACoS); break-even price; the lowest price for a target
margin; a price sweep; and a channel comparison when several profiles are
given. It warns when a fee tier makes profit drop as the price rises (a
price just under the boundary often earns more).

Always show the founder the waterfall table, not just the final number,
and name the two or three costs that matter most.

## 3. Pricing

Work through these, using the script for every number:
1. **Floor:** the break-even price including ads and returns. Never
   recommend a price below it without saying it loses money per order.
2. **Target:** the lowest price that reaches the founder's margin goal (ask
   for one; if they have none, show 20%, 30% and 40%).
3. **Market band:** competitor prices and unit prices from the
   `competitor-research` tables (or a short, sourced check). Place the
   product deliberately: below the band (needs a cost advantage), in it (needs
   a better listing and reviews), or above it (needs a visible reason).
4. **Value ceiling:** what the buyer gets that others don't (from the
   harsh buyer review and competitor complaints). A clear difference
   supports a higher price.
5. **Price points:** use the endings and round numbers buyers expect in that
   market (for example 499 and 999 in India, .99 in the US and much of
   Europe), and check fee tier boundaries near them.
6. **Strike-through and MRP:** reference prices ("M.R.P.", "list price",
   "was") must be real and follow the marketplace's rules and consumer law.
   Never invent a higher "was" price.

**Discount maths.** For any planned discount, compute in code the profit per
order at the discounted price and the sales increase needed to earn the same
total profit: `required increase = old profit per order ÷ new profit per
order − 1`. If the new profit per order is zero or negative, the discount
loses money on every order, whatever the volume.

**Pack sizes and bundles.** Run the economics for each pack size and bundle
as its own SKU (cost and weight scale; some fees are per order, so bigger
packs often earn more per unit). Show the unit price the buyer sees for each
pack, from smallest to largest; it should fall as the pack grows.

**Channel choice.** Compare profit per order and margin across channels at
the same price, then add what the numbers don't show: volume potential,
payout timing, return behaviour and the work each channel takes.

## 4. Ads budget

The break-even TACoS from the script is the most a channel can spend on ads
as a share of sales before each order loses money. Set a target well below
it (the founder decides how much profit to give up for growth during a
launch), and pass the break-even ACoS to `ops.py ads` when reviewing ad
reports.

## 5. Cash and scenarios

- **Payout timing:** marketplaces pay out on cycles and hold reserves; ask
  for the founder's cycle and include it when they plan stock purchases.
- **Scenarios:** for a decision (raising the price, changing a supplier,
  moving to marketplace fulfilment), run the script for each option and
  show them side by side with the assumptions that differ.
- **Sensitivity:** show what happens to profit if return rate, ad spend or
  cost moves by a realistic amount, so the founder sees which assumption
  matters most.

## 6. Deliver

1. The recommendation in one or two sentences (for example: "Price at 949:
   it earns 231 per order after ads and returns, stays under the fee tier at
   1,000, and sits in the middle of the competitor band").
2. The waterfall table and key figures from the script.
3. The assumptions, each with its source and date, and which one matters
   most.
4. What to watch after the change, and when to re-run the numbers.
Run `careful-mode` on any price or fee profile before the founder uses it.
