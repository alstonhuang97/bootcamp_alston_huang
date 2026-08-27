# Dataset: Hobby Box EV

Two linked tables in `data/raw/`, built by `src/build_raw_dataset.py` from public
checklist/odds articles ([checklistinsider.com](https://www.checklistinsider.com/) for
configs and odds; [blowoutcards.com](https://www.blowoutcards.com/) for current retail
prices, cross-checked against Cardboard Connection and Topps Ripped box guides).
`build_raw_dataset.py` holds the hand-transcribed source data; re-run it to regenerate
the CSVs.

`card_tiers.product_id` → `box_products.product_id` (many-to-one).

**Scope:** the **2025-26 Topps NBA** line — Topps' first NBA licence year. Six product
lines (Chrome, Chrome Update, NBA Hoops, Cosmic Chrome, Bowman, Signature Class), one
`box_products` row per **(line × box format)** = 29 rows (Hobby, Jumbo, Breakers Delight,
Mega, Value Blaster, Hanger, First Day Issue, Lunar).

`card_tiers.csv` details the full parallel/insert/autograph ladder for the **Hobby**
format only (every row has `box_format = Hobby`). Other formats carry box-level headline
odds (`auto_odds_pack`, `ssp_odds_pack`) in `box_products.csv`; their full tier ladders
are a later collection step.

**Money:** every price column is USD (`currency` column is a constant `"USD"` marker).

**Odds convention:** every `*_odds_pack` is the aggregate "1 in N packs for **any** card
in that tier" as published by checklistinsider — not per-individual-card odds.

## `box_products.csv` — one row per (product line × box format)

| column | type | notes |
|---|---|---|
| `product_id` | str | primary key, e.g. `2025-26-topps-chrome-bkb-hobby`, `…-value-blaster` |
| `product_line` | str | the release, shared across its formats |
| `product_name` | str | `product_line` + format |
| `brand` / `sport` / `season_label` | str | Topps / Basketball / 2025-26 |
| `release_year` | int | calendar year the format hit the market |
| `release_date` | date | line-level release date |
| `box_format` | str | Hobby, Jumbo, Jumbo First Day Issue, Breakers Delight, Mega, Value Blaster, Fanatics Value Blaster, Hanger, First Day Issue, Lunar |
| `format_channel` | str | `hobby` / `retail` / `breaker` / `premium` — coarse grouping for EDA |
| `currency` | str | always `USD` |
| `cards_per_pack` / `packs_per_box` / `boxes_per_case` | int | blank = not published |
| `cards_per_box` | int | derived = `cards_per_pack × packs_per_box` |
| `stated_autos_per_box` | float | manufacturer's advertised autos per box; blank if guaranteed per case instead |
| `stated_autos_per_case` | int | used when the guarantee is per case (Cosmic, some retail) |
| `auto_odds_pack` | float | "1 in N packs for any autograph". `auto_odds_basis` says where it came from |
| `auto_odds_basis` | str | `published` (from odds sheet) / `derived_from_guarantee` (= `packs_per_box / stated_autos_per_box`) / blank |
| `ssp_odds_pack` | float | "1 in N packs for any SSP insert"; blank = not published for that format |
| `srp_usd` | float | Topps release retail price (SRP) |
| `retail_price_usd` | float | current sealed-box price |
| `retail_price_asof` | date | when `retail_price_usd` was captured |
| `retail_price_source` | str | `blowoutcards.com`, or `srp_placeholder …` where a live price wasn't captured (value copied from `srp_usd`) |
| `base_set_size` | int | base cards in the line |
| `odds_source_url` | str | article the odds were transcribed from |
| `source_note` | str | per-format caveats |

## `card_tiers.csv` — one row per (Hobby product × parallel / insert / autograph set)

| column | type | notes |
|---|---|---|
| `product_id` | str | foreign key — always a `…-hobby` id |
| `box_format` | str | always `Hobby` in this version |
| `tier_name` | str | e.g. `Gold Refractor`, `Clutch Gene`, `Chrome Autographs` |
| `tier_group` | str | `base` / `parallel` / `insert` / `auto` / `variation` |
| `print_run` | int | serial number (`/50` → 50); blank = unnumbered |
| `is_numbered` | bool | `print_run` is not blank |
| `is_autograph` | bool | |
| `is_ssp` | bool | super short print / unannounced |
| `odds_pack` | float | "1 in N packs" (aggregate); blank = only card-level odds published |
| `odds_box` | float | derived: `odds_pack / packs_per_box` ("1 in N boxes") |
| `est_value_usd` | float | **crude placeholder** from `est_value()` — a per-tier-group ladder, not a real comp |
| `value_basis` | str | `rough_estimate_v0` on every row until replaced with eBay sold medians |
| `source_note` | str | e.g. `card-level odds only`, `1/1 per subject` |

## Known gaps / assumptions

- **`est_value_usd` is a placeholder**, not a comp. `est_value()` is a generic ladder
  (every `/50` parallel = $70, every rookie auto = $150, NBA Debut Patch Auto = $5,000
  flat). It ignores *which player* is on the card — a Cooper Flagg 1/1 and a bench-vet
  1/1 are worlds apart. This is why the crude hobby EV (~$150-260) sits so far under the
  hot retail prices: buyers are pricing a Flagg-shaped lottery ticket the placeholder
  can't see. First thing to replace; every row flagged `value_basis = rough_estimate_v0`.
- **`retail_price_usd`**: live prices captured from Blowout for the six Hobby boxes
  (Chrome Basketball Hobby was out of stock, so it falls back to SRP). Every non-Hobby
  format is `srp_placeholder` — value copied from `srp_usd`, `retail_price_source` says
  so. Fill these from a retailer (dacardworld etc.) when needed.
- **`ssp_odds_pack`** is published per format only for Chrome Basketball and Chrome Update
  (and, loosely, Signature Class where the "SSP" figure is really the base FoilFractor
  1/1 rate — left blank, noted). NBA Hoops, Cosmic Chrome, and Bowman don't publish an
  aggregate SSP number.
- **`auto_odds_pack`**: `published` where checklistinsider gave an aggregate; otherwise
  `derived_from_guarantee` = `packs_per_box / stated_autos_per_box`; blank for retail
  formats with no guarantee and no published figure.
- Odds are **aggregate, not per-card**. Fine for box-level EV; per-player EV needs the
  per-card odds from the Topps PDF.
- Odds sheets state averages over the full print run; real box-to-box variance is higher,
  especially for 1/1s.
- `card_tiers.csv` is **Hobby only**. Retail/Jumbo/Breaker parallel ladders are not in it
  yet — don't compute a non-Hobby tier-level EV from this file.

## Card values / comps (`tier_comps.csv`, `chase_cards.csv`)

`est_value_usd` in `card_tiers.csv` is a placeholder. Real values come from **eBay
sold / completed listings** (or CardLadder), collected into:

**`tier_comps.csv`** — one row per observed sale. `src/ev.py` takes the **median** per
`(product_id, tier_name)` and uses it in place of `est_value_usd` (flips `basis` to
`ebay_sold_median_nN`).

| column | notes |
|---|---|
| `product_id` / `tier_name` | must match a `card_tiers.csv` row |
| `subject` | player on the card (e.g. `Cooper Flagg`) |
| `sale_price_usd` / `sale_date` | one sold listing |
| `source_url` | the eBay/130point/CardLadder link |

**`chase_cards.csv`** — the top-value cards (1/1s, /5-and-under, SSPs, rare autos), one
row each, generated as candidates from `card_tiers.csv`; fill `subject` + `last_sale_usd`.
`src/ev.py chase_upside()` uses these for `P(>=1 chase card in a box)` and the jackpot EV.

### Method (how to turn eBay sold into a tier value)

1. **Base / commons** → do **not** eBay-average. Listings self-select to cards worth
   ~$5+, so a naive average 3-5x's the EV. Use `BASE_CARD_VALUE_USD` in `src/ev.py`
   (currently $0.20, a bulk-lot rate).
2. **Common unnumbered refractors** (1:3-1:15) → spot-check a few sales, one value.
3. **Numbered parallels /399 → /25** and **autograph sets** → pick 2-3 representative
   subjects (a star rookie, a mid veteran), median of the last ~10-15 sold each, average
   across subjects → the tier value. Put the individual sales in `tier_comps.csv`.
4. **/10, /5, 1/1** → representative median where sales exist; where a 1/1 has no sales,
   model it as a multiple of the /5 (SuperFractors historically ~3-8x the /5) and note it.
5. **Chase 1/1 autos** (NBA Debut Patch, SuperFractor autos) → value each in
   `chase_cards.csv` from the handful of public sales. **Weight by its own `odds_pack`** —
   a $500k card at 1:500,000 packs is ~$1/pack of EV. Do **not** average the top-10 chase
   prices into the EV unweighted; keep them at their individual pull odds.

### Access note

eBay's sold filter, 130point, and CardLadder all block automated fetching. Collect these
manually (eBay "Sold items" filter) or via eBay's Marketplace Insights API, then paste
rows into `tier_comps.csv`.

## To extend

1. Add a line to `LINES` and its formats to `FORMATS` in `src/build_raw_dataset.py`;
   add a tier list to `HOBBY_TIERS` keyed by the `…-hobby` product_id.
2. Re-run `python src/build_raw_dataset.py`.
3. Replace `est_value_usd` for the tiers that matter (numbered parallels, autos) with the
   median of ~10 recent eBay **sold** comps; set `value_basis` to e.g.
   `ebay_sold_median_n10_2026-08`.
4. For per-format EV: transcribe each retail format's parallel/insert odds into a
   `box_format`-aware tier table (checklistinsider lists Hobby/Jumbo/Blaster/Mega columns).
