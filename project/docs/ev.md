# Box Expected Value

Implementation: `src/ev.py`. Inputs: `data/raw/box_products.csv`, `data/raw/card_tiers.csv`,
`data/raw/tier_comps.csv`. Run `python src/ev.py` for the ranked table, or
`python src/ev.py <product_id>` for one SKU's breakdown.

## Definition

**EV of a box = the probability-weighted dollar value of the cards inside one box.**

    EV_box = Σ over tiers  (expected cards of that tier per box) × (value of that tier)
           + (leftover base slots) × (base card value)

    expected cards per box = packs_per_box / odds_pack      ("1 in N packs", aggregate)
    tier value             = median eBay sold comp if we have one, else est_value_usd

It is **gross** card value. Net return also subtracts selling fees (~13% eBay/PayPal),
shipping, and any grading cost.

## EV is a mean, not a promise

Box outcomes are heavily right-skewed: most boxes come back **well under** EV, a rare few
hit a chase and pull the average up. Consequences:

- You "lose money" on a box when the cards you actually pull are worth less than **what
  you paid** (plus fees) — *not* less than EV.
- Because the median box < the mean box, even a box with `EV > price` will **usually**
  return a loss on a single open. `EV > price` means "+EV if you buy many," not "this box
  profits."
- `chase_upside()` reports `P(≥1 chase card)` and the jackpot EV separately — that is the
  tail the mean hides.

## Per SKU, compared by ratio

EV is computed for **one product line × one box format** and never pooled — a $50 Blaster
and a $380 Hobby box are different bets. Two ratios make formats comparable:

| metric | meaning |
|---|---|
| `EV / price` | buy/pass signal. `> 1` = +EV before fees, `< 1` = −EV. Price is `retail_price_usd`, or `srp_usd` if no retail price is recorded. |
| `EV / pack` | value per pack — strips out box size |

## `basis` column — how the EV was built

| basis | which SKUs | how |
|---|---|---|
| `tier_ladder` | the 6 **Hobby** boxes | full per-tier sum over `card_tiers.csv` (every parallel / insert / autograph set) + base slots |
| `autos+ssp+base` | the other 23 formats (Jumbo, Blaster, Mega, Hanger, Breakers Delight, FDI, Lunar) | `card_tiers.csv` has no ladder for them, so EV ≈ `expected_autos × line_auto_value + expected_ssp × line_ssp_value + base_slots × base_value`. **The parallel rainbow is omitted → these are a lower bound**, not an estimate. `expected_autos` comes from `stated_autos_per_box`, else `stated_autos_per_case / boxes_per_case`, else `packs_per_box / auto_odds_pack`. `line_auto_value` / `line_ssp_value` are the median Hobby-tier auto / SSP values for that product line. |

## Known softness in the numbers

- `est_value_usd` is a `rough_estimate_v0` placeholder for all but 6 tiers (the Alter Egos
  / Minions eBay comps). Every EV here is provisional.
- Those 6 comps are marquee subjects (Curry, LeBron, Wembanyama), so they overstate their
  tiers' averages — which also inflates `line_ssp_value` for the non-Hobby Chrome Update
  formats.
- Some SSP / autograph odds are missing from the odds sheet; e.g. Alter Egos `1:4,000` is
  estimated from the baseball analogue. Alter Egos EV alone moves ~$10–$50/box on that.
- `BASE_CARD_VALUE_USD = 0.20` in `src/ev.py` is a documented bulk-lot assumption, not an
  eBay average (eBay listings self-select to cards worth ~$5+, which would 3–5× the EV).
