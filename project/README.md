# Hobby Box Expected Value Calculator
*Pilot: 2026 Topps Chrome Update Basketball*

**Stage:** Problem Framing & Scoping (Stage 01)

## Problem Statement

Hobby box collectors across sports and card sets face the same recurring decision: is a box's price justified by the expected value of what's inside? Box prices are set by scarcity and marketing hype around chase cards, but the actual odds and secondary-market comps needed to evaluate that price are scattered across manufacturer odds sheets, checklists, and marketplaces — making it hard for buyers to tell whether they're making a good bet or just paying for hype.

**Pilot scope (Stage 01):** this project starts with the 2026 Topps Chrome Update Series Basketball release, chosen for its high-profile chase cards — NBA Debut Patch Autographs, Alter Egos Inserts, and Minions Variations — some of which have sold for five to seven figures (e.g., recent Alter Egos/Minions sales over $10,000; Cooper Flagg's Debut Patch Auto reportedly worth multiple millions). The goal is to build an expected-value (EV) calculator for this set first, then generalize the approach to other sets and sports.

## Stakeholder & User

**Primary stakeholder & user:** an individual hobby box collector deciding whether to purchase a specific box before opening it. In this case, the decision-maker and the end user are the same person — they provide a box's price and its odds/checklist data through the tool's interface (a CLI for this Stage 01 pilot, with a web UI planned once this is embedded into [AAA Card Shop](https://aaacardshop.com/)) and use the resulting EV + buy/pass recommendation to decide whether the purchase is worth it.

**Timing & workflow context:** this decision happens pre-purchase, often while comparing prices across retailers or the secondary market in real time — so the tool needs to give a fast answer (seconds, not a research session) to be useful in that moment.

## Useful Answer & Decision

This is a **predictive** question.  

Inputs: box purchase price, the checklist/odds sheet (pull rates for parallels, inserts, autographs), and current secondary-market comps for the chase cards.  
Output: expected value (EV) in USD — the probability-weighted sum of likely card values across the checklist, compared against the purchase price.  
Artifact: a command-line tool that takes a box price and odds/checklist data as input (via arguments or prompts) and returns an EV figure plus a buy/pass recommendation.

## Assumptions & Constraints

- **Data source (checklist/odds):** For this pilot, [Beckett's 2025-26 Topps Chrome Update Basketball checklist](https://www.beckett.com/news/2025-26-topps-chrome-update-basketball-cards/) provides parallels, inserts, and print runs used to identify chase cards and odds context. Beckett publishes similar checklists for most releases, so this same source pattern is expected to generalize to other sets in later stages.
- **Data source (comps):** eBay, CardHobby, and CardLadder for sold-price comps. This pilot assumes the user already has CardLadder access — common among professional/serious collectors — so it's treated as an available data source rather than a blocker. If the tool later generalizes to casual buyers (per the generalization goal in Lifecycle Mapping), a lower-cost or free comp source may need to be considered.
- **Data format:** Beckett's checklist and Topps' official odds sheet are published as articles/PDFs, not a structured API — so pulling this data means manual entry or scraping rather than a clean automated feed, at least for this pilot stage.
- **Odds accuracy:** the model assumes Topps' published odds reflect true pull rates. In reality, published odds are averages across a full print run — actual box-to-box variance can differ, especially for very low-probability chase cards (e.g., 1-of-1s).
- **Scope constraint:** EV is calculated for a single box purchase only; group-split or box-break spot pricing is out of scope for this pilot (see Useful Answer & Decision).
- **Compliance:** any scraping/pulling from eBay, CardHobby, or Beckett must respect each site's terms of service and rate limits.

## Known Unknowns / Risks

### Known
- **Odds:** Topps publishes pull-rate odds for autographs and SSPs (Super Short Prints) per box/case configuration; box size (packs per box) affects hit probability.
- **Price:** Limited box supply pushes secondary-market price to ~2x+ retail; grails are rarely pulled from a single box, so cost-splitting (box breaks, splitting with friends) is common.
- **Availability:** Print-run size drives scarcity — low-numbered parallels (/1, /5, /10) and 1-of-1 NBA Debut Patch Autos (one per rookie) are the scarcest and most closely tracked by collector communities; card condition/centering is a separate factor that also affects resale price.

### Unknowns / Risks
1. **Card value volatility** — grail prices swing with player/team performance, and even a scarce card has no realizable value without a buyer.
2. **Box defects** — boxes are marketed with a guaranteed autograph, but some ship without one; Topps' compensation process can take weeks to years.
3. **Shipping loss/theft** — high-value autos are a known theft target in transit; uninsured shipments have no recovery path (or a little compensation) if lost.

## Monitoring Plan
1. **Card value volatility:** check sold comps weekly across eBay, CardHobby, and CardLadder; feed updated comps into the EV calculation on a recurring (weekly) refresh so EV stays current rather than static.
2. **Box defects:** track defect/compensation-time reports from collector forums; apply a defect-rate discount factor to the EV calculation rather than assuming 100% fulfillment.
3. **Shipping loss/theft:** track insured vs. uninsured shipment rate; if a shipment isn't insured, lower the calculated EV by the estimated chance of loss, since an uninsured loss means you get $0 for that card instead of its full value.


## Lifecycle Mapping

Goal → Stage → Deliverable

- Frame the problem and define the EV decision framework → Problem Framing & Scoping (Stage 01) → Problem Statement, Useful Answer & Decision sections (this README)
- Scope the data sources needed for EV inputs (checklist, odds, comps) → Problem Framing & Scoping (Stage 01) → Assumptions & Constraints section (this README)
- Define the stakeholder, decision workflow, and risk factors → Problem Framing & Scoping (Stage 01) → Stakeholder & User, Known Unknowns/Risks, and Monitoring Plan sections (this README)
- Build the EV calculation CLI tool → later stage (post-Stage 01) → working CLI in `src/`
- Generalize EV model → later stage (post-Stage 01) → support additional card sets/sports beyond Topps Chrome Update
- Embed EV tool as web UI → later stage (post-Stage 01) → live feature on [AAA Card Shop](https://aaacardshop.com/)

## Repo Plan

- `data/` — raw and processed data: checklist/odds sheets from [Beckett](https://www.beckett.com/news/2025-26-topps-chrome-update-basketball-cards/), plus sold-comp pulls from eBay, CardHobby, and CardLadder
- `src/` — CLI tool source code (EV calculation logic, odds/checklist parsing)
- `notebooks/` — exploratory analysis and prototyping (testing EV formulas, parsing checklist data before it's finalized into `src/`)
- `docs/` — stakeholder artifact, data source log, and project notes

**Update cadence:** `data/` refreshed weekly per the Monitoring Plan; `src/`, `notebooks/`, and `docs/` updated as the tool and scoping evolve.