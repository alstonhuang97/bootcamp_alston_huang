# Project Summary — Hobby-Box Expected Value Calculator

*For a non-technical reader. The full technical trail is in `README.md`, `docs/`, and
`notebooks/project_pipeline.ipynb`.*

## The problem

Sports-card collectors buy sealed "hobby boxes" hoping the cards inside are worth more than
the box costs. Box prices are set by hype around a few rare "chase" cards, while the
information you would need to judge the price — pull odds and what the cards actually sell
for — is scattered across manufacturer odds sheets, checklists, and marketplaces. The
question this project answers: **for a specific sealed box at a specific price, is the price
justified by the expected value (EV) of what's inside?**

Scope: the 2025-26 Topps NBA basketball line — six releases, 29 box configurations, ~194
card tiers. The decision is a single pre-purchase "buy or pass," not group breaks or
long-term investing.

## What we did

1. **Collected the inputs by hand.** Pull odds and print runs were transcribed from Topps
   and checklistinsider into version-controlled spreadsheets (`data/raw/`), because the
   sources block automated collection. Card values are a rough placeholder ladder — only
   about six tiers have real eBay sold prices so far.
2. **Computed box EV.** For each box: `EV = Σ (how many of each card you expect) ×
   (what that card is worth) + base cards`. Compared to the price as a ratio, `EV / $`
   (above 1 = a good bet over many boxes; below 1 = paying for the lottery ticket).
3. **Built a value model.** A regression that predicts a card tier's value from its rarity
   and type. It fits the current data well, but the "current data" is the placeholder
   ladder, so the fit is partly circular until real prices replace it.
4. **Stress-tested the conclusion.** Re-ran everything with card values halved and doubled,
   and with three different ways of handling missing odds.
5. **Packaged it.** A command-line tool and a small web API (`app.py`) return an EV and a
   buy/pass call for any box. Plans for keeping it running and for automating the weekly
   refresh are in `docs/`.

## What we found

- **At today's prices, only one of the six sealed hobby boxes is a positive-EV buy:**
  2025-26 Topps NBA Hoops Hobby (about $260, expected card value about $290).
- The two most-hyped premium boxes (Chrome Update Series, Cosmic Chrome, both about $1,100)
  return roughly **20 cents of expected card value per dollar spent.** You are buying the
  chance at a chase card, not the expected contents.
- **The ranking is robust.** Halving or doubling every card-value estimate does not flip a
  single buy/pass verdict, and the way we fill in missing pull-odds does not move the
  model. So even though the absolute EV numbers are rough, the ordering of boxes is
  trustworthy.
- The value model systematically **under-values autograph cards** and over-values commons —
  it works best for the mid-rarity "refractor rainbow."

## What we would not rely on

- **The absolute EV dollar figures.** Card values are a placeholder ladder, not real
  market data. Treat them as "roughly this order of magnitude," not a price.
- **The model for the rarest cards.** Uncertainty is widest exactly for the 1-of-1s and
  short prints that drive a box's upside — where we have the least data.
- **A one-time answer.** Sealed-box prices move weekly and card values swing with player
  performance. The numbers are a snapshot dated 2026-08-28.
- **EV as a promise.** EV is an average; most boxes come back well under it, a rare few hit
  a chase. `EV / $` above 1 means "good bet across many boxes," not "this box profits."

## What we would do next

1. Replace the placeholder value ladder with real eBay sold-comp medians — start with
   autographs and low-numbered parallels, where the model is weakest.
2. Transcribe per-format pull odds so non-Hobby boxes (Jumbo, Blaster, Mega) get a real
   estimate instead of a lower bound.
3. Refresh prices and comps weekly and re-run the pipeline (`src/run_step.py`), so `EV / $`
   tracks the live market.
4. Report the *median* box outcome and the probability of beating the price alongside EV,
   so the right-skew is visible.
5. Embed the buy/pass call into the AAA Card Shop storefront once the value data is real.

## Where the work lives

`README.md` — install and run. `docs/lifecycle_framework_guide.md` — every stage mapped to
a file. `reports/stakeholder_report.md` — the detailed memo with charts.
`notebooks/project_pipeline.ipynb` — the whole analysis, top to bottom.
