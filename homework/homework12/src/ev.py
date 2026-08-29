"""Expected value of a sealed box, from the raw dataset.

EV_box = the expected $ value of the cards in ONE box, from pull odds x card values.

  HOBBY boxes -- summed over the full tier ladder in card_tiers.csv:
      EV = sum_tiers (packs_per_box / odds_pack) x tier_value  +  base_slots x base_value

  EVERY OTHER format (Jumbo, Blaster, Mega, Hanger, ...) -- card_tiers has no ladder for
  them, so EV is approximated from box-level fields only:
      EV ~= exp_autos x line_auto_value  +  exp_ssp x line_ssp_value  +  base_slots x base_value
      The parallel rainbow is NOT modelled here, so these are a LOWER BOUND
      (basis = 'autos+ssp+base').

  tier_value = median eBay sold comp (data/raw/tier_comps.csv) if present, else the
               rough_estimate_v0 placeholder in card_tiers.csv.

EV is PER SKU (one product line x one box format). Formats are compared by ratio, never
pooled -- a $50 Blaster and a $380 Hobby are different bets:
      EV / price  -> buy/pass signal ( >1 = +EV before selling fees, <1 = -EV )
      EV / pack   -> value per pack, strips out box size

EV is the MEAN. Box outcomes are heavily right-skewed -- most boxes come back well under
EV, a rare few hit a chase -- so EV > price does NOT mean a given box will profit.
See chase_upside() for P(>=1 chase card).

Usage:
  python src/ev.py                 # ranked table, every box config
  python src/ev.py <product_id>    # breakdown for one SKU
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
BASE_CARD_VALUE_USD = 0.20   # documented bulk assumption for a common base card
                             # (do NOT use an eBay "average sold" here -- eBay listings
                             #  self-select to cards worth ~$5+, which 3-5x's the EV)


def _rows(name):
    p = RAW / name
    if not p.exists():
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def _f(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def load():
    products = {r["product_id"]: r for r in _rows("box_products.csv")}
    tiers = defaultdict(list)
    for r in _rows("card_tiers.csv"):
        tiers[r["product_id"]].append(r)

    comps_raw = defaultdict(list)
    for r in _rows("tier_comps.csv"):
        try:
            comps_raw[(r["product_id"], r["tier_name"])].append(float(r["sale_price_usd"]))
        except (KeyError, ValueError):
            continue
    comps = {k: (statistics.median(v), len(v)) for k, v in comps_raw.items() if v}
    return products, tiers, comps


def tier_value(product_id, tier, comps):
    """(value_usd, basis) for one tier row."""
    hit = comps.get((product_id, tier["tier_name"]))
    if hit:
        return hit[0], f"ebay_sold_median_n{hit[1]}"
    return _f(tier["est_value_usd"], 0.0), "rough_estimate_v0"


def line_hit_values(products, tiers, comps):
    """Median autograph value and median SSP value per product_line, from HOBBY tiers.
    Used to approximate EV for non-Hobby formats of the same line."""
    auto, ssp = defaultdict(list), defaultdict(list)
    for pid, rows in tiers.items():
        line = products.get(pid, {}).get("product_line", pid)
        for t in rows:
            val, _ = tier_value(pid, t, comps)
            if t["tier_group"] == "auto":
                auto[line].append(val)
            if t["is_ssp"] == "True":
                ssp[line].append(val)
    return ({k: statistics.median(v) for k, v in auto.items() if v},
            {k: statistics.median(v) for k, v in ssp.items() if v})


def box_ev(product_id, products, tiers, comps, line_auto_v, line_ssp_v,
           base_value=BASE_CARD_VALUE_USD):
    p = products[product_id]
    ppb = _f(p["packs_per_box"])
    cpb = _f(p["cards_per_box"])
    if not ppb or not cpb:
        return None
    line = p["product_line"]
    price = _f(p["retail_price_usd"]) or _f(p["srp_usd"])
    common = dict(product_id=product_id, name=p["product_name"], fmt=p["box_format"],
                  channel=p["format_channel"], ppb=ppb, price=price,
                  srp=_f(p["srp_usd"]), retail=_f(p["retail_price_usd"]))

    # ---- Hobby: full tier ladder ----
    if p["box_format"] == "Hobby" and product_id in tiers:
        lines, ev_hits, exp_nonbase = [], 0.0, 0.0
        for t in tiers[product_id]:
            odds = _f(t["odds_pack"])
            if not odds:
                continue
            exp = ppb / odds
            val, vb = tier_value(product_id, t, comps)
            contrib = exp * val
            if t["tier_group"] != "base":
                exp_nonbase += exp
                ev_hits += contrib
            lines.append(dict(tier=t["tier_name"], group=t["tier_group"],
                              exp_per_box=exp, value=val, basis=vb, ev=contrib))
        base_slots = max(0.0, cpb - exp_nonbase)
        ev_base = base_slots * base_value
        lines.sort(key=lambda d: -d["ev"])
        return dict(common, ev_total=ev_hits + ev_base, ev_hits=ev_hits, ev_base=ev_base,
                    base_slots=base_slots, basis="tier_ladder", lines=lines)

    # ---- other formats: autos + SSP + base only (parallels omitted -> lower bound) ----
    a_box, a_case, bpc = (_f(p["stated_autos_per_box"]), _f(p["stated_autos_per_case"]),
                          _f(p["boxes_per_case"]))
    auto_odds, ssp_odds = _f(p["auto_odds_pack"]), _f(p["ssp_odds_pack"])
    if a_box:
        exp_autos = a_box
    elif a_case and bpc:
        exp_autos = a_case / bpc
    elif auto_odds:
        exp_autos = ppb / auto_odds
    else:
        exp_autos = 0.0
    exp_ssp = ppb / ssp_odds if ssp_odds else 0.0
    auto_val = line_auto_v.get(line, 100.0)
    ssp_val = line_ssp_v.get(line, 0.0)
    ev_autos, ev_ssp = exp_autos * auto_val, exp_ssp * ssp_val
    base_slots = max(0.0, cpb - exp_autos - exp_ssp)
    ev_base = base_slots * base_value
    return dict(common, ev_total=ev_autos + ev_ssp + ev_base, basis="autos+ssp+base",
                comps=dict(exp_autos=exp_autos, auto_val=auto_val, ev_autos=ev_autos,
                           exp_ssp=exp_ssp, ssp_val=ssp_val, ev_ssp=ev_ssp,
                           base_slots=base_slots, ev_base=ev_base))


def chase_upside(product_id, products, tiers, comps):
    """P(>=1 'chase' card in a box) and its blended value, from chase_cards.csv if present,
    else from tier rows with print_run <= 5 / SSP."""
    p = products[product_id]
    ppb = _f(p["packs_per_box"]) or 0
    chase = [r for r in _rows("chase_cards.csv") if r.get("product_id") == product_id]
    if not chase:
        chase = [dict(tier_name=t["tier_name"], odds_pack=t["odds_pack"],
                      last_sale_usd=t["est_value_usd"])
                 for t in tiers.get(product_id, [])
                 if (_f(t["print_run"]) or 99) <= 5 or t["is_ssp"] == "True"]
    p_none, ev, n_valued = 1.0, 0.0, 0
    for c in chase:
        odds = _f(c.get("odds_pack"))
        if not odds:
            continue
        exp = ppb / odds
        p_none *= (1 - min(exp, 1.0))
        val = _f(c.get("last_sale_usd"))
        if val:
            ev += exp * val
            n_valued += 1
    return dict(p_any_chase=1 - p_none, chase_ev=ev, n=len(chase), n_valued=n_valued)


def ev_table(base_card_value=BASE_CARD_VALUE_USD):
    """Every box config as a DataFrame, ranked by EV/price. Columns: product, line,
    box_format, channel, packs, ev, srp, retail, price, ev_per_price, ev_per_pack, basis.
    (Lazy pandas import so the CLI stays dependency-free.)"""
    import pandas as pd

    products, tiers, comps = load()
    auto_v, ssp_v = line_hit_values(products, tiers, comps)
    rows = []
    for pid, p in products.items():
        r = box_ev(pid, products, tiers, comps, auto_v, ssp_v, base_card_value)
        if not r:
            continue
        price = r["price"]
        rows.append(dict(
            product=r["name"], line=p["product_line"], box_format=r["fmt"],
            channel=r["channel"], packs=r["ppb"],
            ev=round(r["ev_total"], 2), srp=r["srp"], retail=r["retail"], price=price,
            ev_per_price=round(r["ev_total"] / price, 3) if price else None,
            ev_per_pack=round(r["ev_total"] / r["ppb"], 2) if r["ppb"] else None,
            basis=r["basis"],
        ))
    return (pd.DataFrame(rows)
            .sort_values("ev_per_price", ascending=False, na_position="last")
            .reset_index(drop=True))


def main():
    products, tiers, comps = load()
    auto_v, ssp_v = line_hit_values(products, tiers, comps)

    if len(sys.argv) > 1:
        pid = sys.argv[1]
        r = box_ev(pid, products, tiers, comps, auto_v, ssp_v)
        if not r:
            print(f"no EV for {pid} (missing packs_per_box / cards_per_box?)")
            return
        print(f"\n{r['name']}   [{r['fmt']} / {r['channel']}]")
        print(f"  SRP ${r['srp']}   retail ${r['retail']}   packs/box {r['ppb']:.0f}")
        print(f"  EV ${r['ev_total']:.2f}   basis: {r['basis']}")
        if r["price"]:
            print(f"  EV / price = {r['ev_total']/r['price']:.2f}"
                  f"      EV / pack = ${r['ev_total']/r['ppb']:.2f}")
        if r["basis"] == "tier_ladder":
            c = chase_upside(pid, products, tiers, comps)
            print(f"  P(>=1 chase card) = {c['p_any_chase']:.3f}   chase EV ${c['chase_ev']:.2f}"
                  f"  ({c['n_valued']}/{c['n']} priced)")
            print(f"\n  {'tier':<38}{'exp/box':>9}{'value':>10}{'EV':>9}  basis")
            for L in r["lines"][:20]:
                print(f"  {L['tier'][:37]:<38}{L['exp_per_box']:>9.3f}{L['value']:>10.2f}"
                      f"{L['ev']:>9.2f}  {L['basis']}")
        else:
            c = r["comps"]
            print(f"\n  {'component':<18}{'exp/box':>9}{'value':>10}{'EV':>9}")
            print(f"  {'autographs':<18}{c['exp_autos']:>9.4f}{c['auto_val']:>10.0f}{c['ev_autos']:>9.2f}")
            print(f"  {'SSP inserts':<18}{c['exp_ssp']:>9.4f}{c['ssp_val']:>10.0f}{c['ev_ssp']:>9.2f}")
            print(f"  {'base slots':<18}{c['base_slots']:>9.0f}{BASE_CARD_VALUE_USD:>10.2f}{c['ev_base']:>9.2f}")
            print("  (parallel rainbow not modelled for non-Hobby formats -> EV is a lower bound)")
        return

    rows = [r for pid in products
            if (r := box_ev(pid, products, tiers, comps, auto_v, ssp_v))]
    rows.sort(key=lambda r: (r["ev_total"] / r["price"]) if r["price"] else -1, reverse=True)

    print(f"{len(comps)} tier(s) with real eBay comps; everything else is rough_estimate_v0\n")
    hdr = f"{'box config':<46}{'EV':>7}{'price':>7}{'EV/$':>7}{'EV/pk':>7}  basis"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        rr = f"{r['ev_total']/r['price']:.2f}" if r["price"] else "-"
        pk = f"{r['ev_total']/r['ppb']:.1f}" if r["ppb"] else "-"
        pr = f"{r['price']:.0f}" if r["price"] else "-"
        print(f"{r['name'][:45]:<46}{r['ev_total']:>7.0f}{pr:>7}{rr:>7}{pk:>7}  {r['basis']}")
    print("\nHobby EV = full tier ladder.  Other formats = autos+SSP+base only "
          "(parallels omitted -> lower bound).")
    print("EV is a mean; box outcomes are right-skewed, so EV/$ > 1 is 'good bet long-run', "
          "not 'this box profits'.  Subtract ~13% selling fees before acting.")


if __name__ == "__main__":
    main()
