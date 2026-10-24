# Example: profit per order with the Ecom tool

A real run of the Ecom tool's `economics.py`, unedited. The question: "I sell
at ₹999 on Amazon India, my product costs ₹280. What do I make per order, and
should I raise the price to ₹1,099?"

```
python3 economics.py unit --fees fees-example.json --price 999 --cost 280 \
  --packaging 20 --weight 350 --tax-rate 12 --sweep 799,899,999,1099 --target-margin 25
```

The full output is in [`report.md`](report.md). What it found:

- **₹259 profit per order** at ₹999, after marketplace fees, returns, GST and
  ad spend, worked out per order placed, so returns are counted properly.
- **Raising the price to ₹1,099 makes less money (₹248 per order),** because
  that price crosses into a higher referral-fee tier. The tool flags it on
  its own: "profit falls as price rises somewhere in this range". Guessing
  from a percentage would have said the opposite.
- The lowest price that keeps a 25% margin (₹868), the break-even price
  (₹580) and the most you can spend on ads before you lose money (38% of
  sales).

**These are example fees** (`fees-example.json` is the tool's template, and
the report warns about that). With the Ecom tool installed, Claude builds the
fee profile from your own settlement report or the marketplace's current rate
card, with the source and date of every number.
