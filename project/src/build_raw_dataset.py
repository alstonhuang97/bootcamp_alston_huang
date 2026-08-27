"""Build the hobby-box EV raw dataset: data/raw/box_products.csv + data/raw/card_tiers.csv.

Everything below is hand-transcribed from public checklist/odds articles
(checklistinsider.com for configs/odds; blowoutcards.com + dacardworld search snippets
for current retail prices). This script is the "manual entry" step the README's data
plan anticipates -- kept in version control so the transcription is auditable and the
CSVs are regenerable.

Scope: 2025-26 Topps NBA hobby line, Topps' first NBA licence year -- six product lines
(Chrome, Chrome Update, NBA Hoops, Cosmic Chrome, Bowman, Signature Class), one
box_products row per (line x box format).

Money: every price column is USD.

Blank == not published / not captured (NOT zero).
`est_value_usd` in card_tiers is a crude per-tier placeholder (see `est_value`);
`value_basis = rough_estimate_v0` marks every one for replacement with eBay sold medians.

Odds convention: `*_odds_pack` = aggregate "1 in N packs for ANY card in that tier",
as published by checklistinsider (not per-individual-card odds).

Run:  python src/build_raw_dataset.py
"""
from __future__ import annotations

import csv
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
SRC = "https://www.checklistinsider.com"
PRICE_ASOF = "2026-08-27"

# --------------------------------------------------------------------------------------
# product lines (shared attributes)
# --------------------------------------------------------------------------------------
LINES = {
    "chrome": dict(
        id_base="2025-26-topps-chrome-bkb",
        line="2025-26 Topps Chrome Basketball",
        release_year=2025, release_date="2025-12-18", base_set_size=299,
        odds_url=f"{SRC}/2025-26-topps-chrome-basketball",
    ),
    "chrome_update": dict(
        id_base="2025-26-topps-chrome-update-bkb",
        line="2025-26 Topps Chrome Update Series Basketball",
        release_year=2026, release_date="2026-08-06", base_set_size=200,
        odds_url=f"{SRC}/2025-26-topps-chrome-update-series-basketball",
    ),
    "hoops": dict(
        id_base="2025-26-topps-nba-hoops",
        line="2025-26 Topps NBA Hoops",
        release_year=2026, release_date="2026-05-14", base_set_size=300,
        odds_url=f"{SRC}/2025-26-topps-nba-hoops-basketball",
    ),
    "cosmic": dict(
        id_base="2025-26-topps-cosmic-chrome-bkb",
        line="2025-26 Topps Cosmic Chrome Basketball",
        release_year=2026, release_date="2026-04-29", base_set_size=200,
        odds_url=f"{SRC}/2025-26-topps-cosmic-chrome-basketball",
    ),
    "bowman": dict(
        id_base="2025-26-bowman-bkb",
        line="2025-26 Bowman Basketball",
        release_year=2026, release_date="2026-04-22", base_set_size=200,
        odds_url=f"{SRC}/2025-26-bowman-basketball",
    ),
    "sigclass": dict(
        id_base="2025-26-topps-signature-class-bkb",
        line="2025-26 Topps Signature Class Basketball",
        release_year=2026, release_date="2026-05-28", base_set_size=150,
        odds_url=f"{SRC}/2025-26-topps-signature-class-basketball",
    ),
}

FMT_SLUG = {
    "Hobby": "hobby", "Jumbo": "jumbo", "Jumbo First Day Issue": "jumbo-fdi",
    "Breakers Delight": "breakers-delight", "Mega": "mega",
    "Value Blaster": "value-blaster", "Fanatics Value Blaster": "fanatics-value-blaster",
    "Hanger": "hanger", "First Day Issue": "fdi", "Lunar": "lunar",
}

# --------------------------------------------------------------------------------------
# box formats: one tuple per (line x format)
# (line_key, box_format, channel, cpp, ppb, bpc,
#  autos_per_box, autos_per_case,
#  ssp_odds_pack, auto_odds_pack_pub,
#  srp_usd, retail_usd, retail_src, note)
# --------------------------------------------------------------------------------------
FORMATS = [
    # ---- Topps Chrome Basketball ----
    ("chrome", "Hobby", "hobby", 4, 20, 12, 1, None, 26121, 2361,
     379.99, 379.99, "srp_placeholder (box out of stock at Blowout on price date)", ""),
    ("chrome", "Jumbo", "hobby", 11, 12, 8, 3, None, 7698, 693,
     699.99, 699.99, "srp_placeholder", ""),
    ("chrome", "Jumbo First Day Issue", "premium", 11, 12, 8, 3, None, 7698, 693,
     3500.00, 3500.00, "srp_placeholder (reverse Dutch auction opens $3,500)", ""),
    ("chrome", "Breakers Delight", "breaker", 10, 1, 6, 2, None, 1256, 67,
     None, None, "", ""),
    ("chrome", "Mega", "retail", 8, 7, 20, 0, None, 126227, 53647,
     84.99, 84.99, "srp_placeholder", ""),
    ("chrome", "Value Blaster", "retail", 4, 7, 40, 0, None, 254668, 101867,
     49.99, 49.99, "srp_placeholder", ""),
    ("chrome", "Hanger", "retail", 15, 1, None, 0, None, 29760, 12648,
     19.99, 19.99, "srp_placeholder", "ssp/auto odds are per box (hanger = 1 pack)"),

    # ---- Topps Chrome Update Series ----
    ("chrome_update", "Hobby", "hobby", 4, 20, 12, 1, None, 6054, 141,
     549.99, 1099.95, "blowoutcards.com", "Cooper Flagg RDPA demand -> ~2x SRP"),
    ("chrome_update", "Jumbo", "hobby", 11, 12, 8, 3, None, 2415, 34,
     1099.99, 1099.99, "srp_placeholder", ""),
    ("chrome_update", "Breakers Delight", "breaker", 6, 1, 6, 2, None, 201, 5,
     None, None, "", ""),
    ("chrome_update", "Mega", "retail", 6, 7, 20, 0, None, 112000, None,
     84.99, 84.99, "srp_placeholder", ""),
    ("chrome_update", "Value Blaster", "retail", 4, 7, 40, 0, None, 17365, 30619,
     44.99, 44.99, "srp_placeholder", ""),

    # ---- Topps NBA Hoops ----
    ("hoops", "Hobby", "hobby", 8, 20, 12, 1, None, None, None,
     279.99, 259.95, "blowoutcards.com", "SSP odds not published by format"),
    ("hoops", "Jumbo", "hobby", 20, 10, 8, 2, None, None, None,
     519.99, 519.99, "srp_placeholder", ""),
    ("hoops", "Value Blaster", "retail", 8, 7, 40, 0, None, None, None,
     34.99, 34.99, "srp_placeholder", ""),
    ("hoops", "Fanatics Value Blaster", "retail", 8, 8, None, 0, None, None, None,
     39.99, 39.99, "srp_placeholder", ""),
    ("hoops", "Hanger", "retail", 25, 1, 64, 0, None, None, None,
     None, None, "", ""),

    # ---- Topps Cosmic Chrome ----
    ("cosmic", "Hobby", "hobby", 4, 20, 8, None, 2, None, None,
     579.99, 1100.00, "blowoutcards.com 8-box case $8,799.95 / 8", "autos guaranteed per case, not per box"),
    ("cosmic", "First Day Issue", "premium", 4, 20, 8, None, 2, None, None,
     1575.00, 1575.00, "srp_placeholder (Dutch auction ~$1,550-1,600)", ""),
    ("cosmic", "Lunar", "hobby", 4, 20, 8, None, 2, None, None,
     None, None, "", "1 Lunar Refractor SP guaranteed per pack"),

    # ---- Bowman Basketball ----
    ("bowman", "Hobby", "hobby", 8, 20, 12, 2, None, None, 68,
     359.99, 499.95, "blowoutcards.com", "2 autos/box = 1 NBA + 1 NIL"),
    ("bowman", "Jumbo", "hobby", 24, 12, 8, 4, None, None, None,
     599.99, 599.99, "srp_placeholder", "4 autos/box = 2 NBA + 2 NIL"),
    ("bowman", "Breakers Delight", "breaker", 10, 1, 6, 3, None, None, None,
     None, None, "", "3 autos/box = 2 NBA + 1 NIL"),
    ("bowman", "Mega", "retail", 7, 6, 20, None, 4, None, None,
     59.99, 59.99, "srp_placeholder", "~4 autos per case"),
    ("bowman", "Value Blaster", "retail", 10, 6, None, None, 4, None, None,
     29.99, 29.99, "srp_placeholder", "~4 autos per case"),

    # ---- Topps Signature Class ----
    ("sigclass", "Hobby", "hobby", 4, 8, 12, 2, None, None, None,
     549.99, 549.99, "srp_placeholder (retailer bot-blocked on price date)",
     "autograph-driven product; no SSP inserts (base FoilFractor 1/1 is 1:14,661 hobby)"),
    ("sigclass", "Jumbo", "hobby", 10, 4, 6, 4, None, None, None,
     899.99, 899.99, "srp_placeholder", ""),
    ("sigclass", "Mega", "retail", 8, 10, 20, 0, None, None, None,
     64.99, 64.99, "srp_placeholder", ""),
    ("sigclass", "Value Blaster", "retail", 7, 6, 40, 0, None, None, None,
     34.99, 34.99, "srp_placeholder", ""),
]


def _slug(fmt):
    return FMT_SLUG[fmt]


def build_products():
    rows = []
    for (lk, fmt, channel, cpp, ppb, bpc, a_box, a_case,
         ssp, auto_pub, srp, retail, retail_src, note) in FORMATS:
        L = LINES[lk]
        pid = f"{L['id_base']}-{_slug(fmt)}"
        # aggregate "any autograph" pack odds: published value, else derived from a
        # per-box guarantee, else blank
        if auto_pub is not None:
            auto_odds, auto_basis = auto_pub, "published"
        elif a_box:
            auto_odds, auto_basis = round(ppb / a_box, 1), "derived_from_guarantee"
        else:
            auto_odds, auto_basis = "", ""
        rows.append(dict(
            product_id=pid,
            product_line=L["line"],
            product_name=f"{L['line']} {fmt}",
            brand="Topps", sport="Basketball", season_label="2025-26",
            release_year=L["release_year"], release_date=L["release_date"],
            box_format=fmt, format_channel=channel, currency="USD",
            cards_per_pack=cpp, packs_per_box=ppb,
            boxes_per_case="" if bpc is None else bpc,
            cards_per_box=cpp * ppb,
            stated_autos_per_box="" if a_box is None else a_box,
            stated_autos_per_case="" if a_case is None else a_case,
            auto_odds_pack=auto_odds, auto_odds_basis=auto_basis,
            ssp_odds_pack="" if ssp is None else ssp,
            srp_usd="" if srp is None else srp,
            retail_price_usd="" if retail is None else retail,
            retail_price_asof=PRICE_ASOF if retail is not None else "",
            retail_price_source=retail_src,
            base_set_size=L["base_set_size"],
            odds_source_url=L["odds_url"],
            source_note=note,
        ))
    return rows


# --------------------------------------------------------------------------------------
# card_tiers: HOBBY box only. one row per (product x parallel / insert / autograph set)
# tuple = (tier_name, tier_group, print_run, is_auto, is_ssp, odds_pack, note)
# --------------------------------------------------------------------------------------
HOBBY_TIERS: dict[str, list[tuple]] = {
    "2025-26-topps-chrome-bkb-hobby": [
        ("Base", "base", None, False, False, None, ""),
        ("Base Refractor", "parallel", None, False, False, 3, ""),
        ("Prism Refractor", "parallel", None, False, False, 5, ""),
        ("Wave Refractor", "parallel", None, False, False, 14, ""),
        ("Negative Refractor", "parallel", None, False, False, 31, ""),
        ("Magenta Refractor", "parallel", 399, False, False, 47, ""),
        ("Teal Refractor", "parallel", 299, False, False, 72, ""),
        ("Yellow Refractor", "parallel", 275, False, False, 79, ""),
        ("Aqua Refractor", "parallel", 199, False, False, 109, ""),
        ("Blue Refractor", "parallel", 150, False, False, 145, ""),
        ("Blue Wave Refractor", "parallel", 150, False, False, 113, ""),
        ("Green Refractor", "parallel", 99, False, False, 219, ""),
        ("Green Wave Refractor", "parallel", 99, False, False, 172, ""),
        ("Purple Refractor", "parallel", 75, False, False, 290, ""),
        ("Purple Wave Refractor", "parallel", 75, False, False, 227, ""),
        ("Gold Refractor", "parallel", 50, False, False, 435, ""),
        ("Gold Wave Refractor", "parallel", 50, False, False, 341, ""),
        ("Orange Refractor", "parallel", 25, False, False, 870, ""),
        ("Orange Wave Refractor", "parallel", 25, False, False, 684, ""),
        ("Black Refractor", "parallel", 10, False, False, 2176, ""),
        ("Black Wave Refractor", "parallel", 10, False, False, 1710, ""),
        ("Red Refractor", "parallel", 5, False, False, 4353, ""),
        ("Red Wave Refractor", "parallel", 5, False, False, 3420, ""),
        ("FrozenFractor", "parallel", 5, False, False, 4353, "numbered /-5"),
        ("SuperFractor", "parallel", 1, False, False, 21767, ""),
        ("Clutch Gene", "insert", None, False, False, 11, ""),
        ("Destiny", "insert", None, False, False, 17, ""),
        ("Tall Tales", "insert", None, False, True, None, "hobby-exclusive SSP; card-level odds only"),
        ("Inspirational", "insert", None, False, True, None, "hobby-exclusive SSP; card-level odds only"),
        ("X's and Whoa's", "insert", None, False, True, None, "SSP; card-level odds only"),
        ("Ultra Violet", "insert", None, False, True, None, "hobby-exclusive SSP; card-level odds only"),
        ("Topps Chrome Autographs Rookies", "auto", None, True, False, 65, ""),
        ("SkyWrite Signatures", "auto", None, True, False, 417, ""),
        ("Topps Certified Autograph Issue Rookies", "auto", None, True, False, 417, ""),
        ("Next Stop Signatures", "auto", None, True, False, 522, ""),
        ("Signature Style", "auto", None, True, False, 522, ""),
        ("Topps Chrome Autographs", "auto", None, True, False, 2361, ""),
    ],
    "2025-26-topps-chrome-update-bkb-hobby": [
        ("Base", "base", None, False, False, None, ""),
        ("Refractor", "parallel", None, False, False, 4, ""),
        ("Prism Refractor", "parallel", None, False, False, 5, ""),
        ("Wave Refractor", "parallel", None, False, False, 13, ""),
        ("Negative Refractor", "parallel", None, False, False, 45, ""),
        ("Magenta Refractor", "parallel", 399, False, False, 76, ""),
        ("Teal Refractor", "parallel", 299, False, False, 101, ""),
        ("Yellow Refractor", "parallel", 275, False, False, 110, ""),
        ("Yellow Wave Refractor", "parallel", 275, False, False, 129, ""),
        ("Aqua Refractor", "parallel", 199, False, False, 152, ""),
        ("Aqua Wave Refractor", "parallel", 199, False, False, 79, ""),
        ("Blue Refractor", "parallel", 150, False, False, 202, ""),
        ("Blue Wave Refractor", "parallel", 150, False, False, 104, ""),
        ("Green Refractor", "parallel", 99, False, False, 306, ""),
        ("Green Wave Refractor", "parallel", 99, False, False, 158, ""),
        ("Purple Refractor", "parallel", 75, False, False, 403, ""),
        ("Purple Wave Refractor", "parallel", 75, False, False, 208, ""),
        ("Gold Refractor", "parallel", 50, False, False, 604, ""),
        ("Gold Wave Refractor", "parallel", 50, False, False, 312, ""),
        ("Orange Refractor", "parallel", 25, False, False, 1209, ""),
        ("Orange Wave Refractor", "parallel", 25, False, False, 623, ""),
        ("Black Refractor", "parallel", 10, False, False, 3022, ""),
        ("Black Wave Refractor", "parallel", 10, False, False, 1559, ""),
        ("Red Refractor", "parallel", 5, False, False, 6054, ""),
        ("Red Wave Refractor", "parallel", 5, False, False, 3119, ""),
        ("FrozenFractor", "parallel", 5, False, False, 6054, ""),
        ("SuperFractor", "parallel", 1, False, False, 30361, ""),
        ("Activators", "insert", None, False, False, 20, ""),
        ("Image Variations Speckle", "variation", None, False, False, 150, ""),
        ("Denim Tears", "insert", None, False, True, 6054, "SSP parallel; hobby aggregate"),
        ("Alter Egos", "insert", None, False, True, 4000,
         "base NOT on official odds sheet; ~113 copies/card, 10-card set; odds_pack "
         "estimated from 2025 Topps Chrome baseball Alter Egos (~1:4,000 hobby)"),
        ("Minions NBA", "variation", None, False, True, 12456,
         "Minions Variation; 5 subjects only; 1:12,456 packs / 1:623 boxes; also has Red /5 + SuperFractor 1/1"),
        ("Minions NBA MinionFractor", "variation", None, False, True, 13000,
         "refractor parallel of Minions; ~92 copies/card x 5 subjects; odds_pack "
         "estimated (~equal to base Minions rate) -- not published"),
        ("Chrome Autographs", "auto", None, True, False, 141, ""),
        ("Topps Chrome Autographs Druski", "auto", None, True, False, 141, ""),
        ("Havoc Marks", "auto", None, True, False, 280, ""),
        ("Future Stars Autographs", "auto", None, True, False, 622, ""),
        ("1980-81 Topps Autographs", "auto", None, True, False, 1455, ""),
        ("Rookie Autographs Lava Lamp", "auto", None, True, False, None, "1:295-2,133 range (parallels)"),
        ("NBA Debut Patch Autographs", "auto", 1, True, False, 74733, "1/1 per subject"),
        ("Topps Chrome Autographs Spike Lee", "auto", None, True, False, 138789, "1:138,789+"),
    ],
    "2025-26-topps-nba-hoops-hobby": [
        ("Base", "base", None, False, False, None, ""),
        ("Rainbow", "parallel", None, False, False, 3, ""),
        ("Pixel Burst", "parallel", None, False, False, 9, ""),
        ("Rainbow Green & Blue", "parallel", 249, False, False, 35, ""),
        ("Rainbow Gold & Green", "parallel", 199, False, False, 44, ""),
        ("Rainbow Yellow", "parallel", 275, False, False, 86, ""),
        ("Pixel Burst Blue", "parallel", 149, False, False, 59, ""),
        ("Pixel Burst Purple", "parallel", 99, False, False, 88, ""),
        ("Pixel Burst Green", "parallel", 75, False, False, 117, ""),
        ("Pixel Burst Gold", "parallel", 50, False, False, 175, ""),
        ("Pixel Burst Orange", "parallel", 25, False, False, 348, ""),
        ("Pixel Burst Black", "parallel", 10, False, False, 870, ""),
        ("Pixel Burst Red", "parallel", 5, False, False, 1735, ""),
        ("Pixel Burst Platinum", "parallel", 1, False, False, 8614, ""),
        ("Bounce House", "insert", None, False, False, 15, ""),
        ("Hoopers", "insert", None, False, False, 19, ""),
        ("Dunk-umentory", "insert", None, False, False, 25, ""),
        ("Finals Pursuit", "insert", None, False, False, 27, ""),
        ("Hoopnotic", "insert", None, False, False, 346, ""),
        ("Checkmate", "insert", None, False, False, 403, ""),
        ("Joy", "insert", None, False, False, 1154, ""),
        ("Hoops Signs", "auto", None, True, False, 55, ""),
        ("Hoops Rookie Signatures", "auto", None, True, False, 74, ""),
        ("1989 Hoops Signatures", "auto", None, True, False, 130, ""),
        ("Hoops Rookie Duals", "auto", None, True, False, 1994, ""),
        ("Hoops Rookie Triples", "auto", None, True, False, 9903, ""),
        ("Rookie Veteran Duals", "auto", None, True, False, 19650, ""),
    ],
    "2025-26-topps-cosmic-chrome-bkb-hobby": [
        ("Base", "base", None, False, False, None, ""),
        ("Refractor", "parallel", None, False, False, 10, ""),
        ("Nucleus Refractor", "parallel", None, False, False, 20, ""),
        ("White Hole Refractor", "parallel", None, False, False, 126, ""),
        ("Aqua Equinox Refractor", "parallel", 199, False, False, 42, ""),
        ("Purple Nebula Refractor", "parallel", 150, False, False, 56, ""),
        ("Blue Moon Refractor", "parallel", 99, False, False, 85, ""),
        ("Green Space Dust Refractor", "parallel", 75, False, False, 111, ""),
        ("Gold Interstellar Refractor", "parallel", 50, False, False, 167, ""),
        ("Orange Galactic Refractor", "parallel", 25, False, False, 333, ""),
        ("Black Eclipse Refractor", "parallel", 10, False, False, 832, ""),
        ("Red Flare Refractor", "parallel", 5, False, False, 1664, ""),
        ("SuperFractor", "parallel", 1, False, False, 8319, ""),
        ("Galaxy Greats", "insert", None, False, False, 6, ""),
        ("Extraterrestrial Talent", "insert", None, False, False, 8, ""),
        ("Propulsion", "insert", None, False, False, 8, ""),
        ("Space Walk", "insert", None, False, False, 13, ""),
        ("StarFractor", "insert", None, False, False, 609, ""),
        ("Cosmic Dust", "insert", None, False, False, 793, ""),
        ("Re-Entry", "insert", None, False, False, 871, ""),
        ("Hypernova", "insert", None, False, False, 201, ""),
        ("First Light", "insert", None, False, False, 1109, ""),
        ("Geocentric", "insert", None, False, False, 1109, ""),
        ("Singularity Signatures", "auto", None, True, False, 331, ""),
        ("Cosmic Chrome Autographs", "auto", None, True, False, 383, ""),
        ("First Flight Signatures", "auto", None, True, False, 678, ""),
        ("Electro Static Signatures", "auto", None, True, False, 805, ""),
        ("Alien Autographs", "auto", None, True, False, 1235, ""),
        ("Cosmic Chrome Autographs II", "auto", None, True, False, 31776, ""),
    ],
    "2025-26-bowman-bkb-hobby": [
        ("Base", "base", None, False, False, None, ""),
        ("Prospects Paper", "base", None, False, False, 1, "prospect base, 1:1"),
        ("Prospects Chrome", "base", None, False, False, 1, "prospect base, 1:1"),
        ("Chrome Mini-Diamond Refractor", "parallel", None, False, False, 30, ""),
        ("Chrome Refractor", "parallel", 499, False, False, 75, ""),
        ("Chrome Fuchsia Refractor", "parallel", 199, False, False, 188, ""),
        ("Base Purple Pattern Border", "parallel", 199, False, False, 188, ""),
        ("Base Pink Border", "parallel", 175, False, False, 214, ""),
        ("Base Blue Border", "parallel", 150, False, False, 250, ""),
        ("Chrome Blue Refractor", "parallel", 150, False, False, 250, ""),
        ("Base Orange Border", "parallel", 25, False, False, 449, ""),
        ("Base Yellow Border", "parallel", 75, False, False, 499, ""),
        ("Chrome Yellow Refractor", "parallel", 75, False, False, 499, ""),
        ("Base Gold Border", "parallel", 50, False, False, 748, ""),
        ("Chrome Gold Refractor", "parallel", 50, False, False, 748, ""),
        ("Base Black Border", "parallel", 10, False, False, 1123, ""),
        ("Base Black Pattern Border", "parallel", 10, False, False, 1123, ""),
        ("Chrome Black Refractor", "parallel", 10, False, False, 3742, ""),
        ("Base Red Border", "parallel", 5, False, False, 7496, ""),
        ("Chrome Red Refractor", "parallel", 5, False, False, 7496, ""),
        ("Chrome FireFractor", "parallel", 3, False, False, 12522, ""),
        ("Chrome SuperFractor", "parallel", 1, False, False, 23046, ""),
        ("Base Platinum Border", "parallel", 1, False, False, 38005, ""),
        ("Rookie Red RC Logos", "insert", None, False, False, 20, ""),
        ("Etched In Glass", "insert", None, False, False, 1733, ""),
        ("Base Chrome Autographs", "auto", None, True, False, 68, ""),
        ("Chrome Prospect Autographs", "auto", None, True, False, 76, ""),
        ("Buzz Factor", "auto", None, True, False, 1417, ""),
        ("Opening Statement Signatures", "auto", None, True, False, 1731, ""),
        ("Future Script", "auto", None, True, False, 1889, ""),
        ("Bowman Dual Autographs", "auto", 10, True, False, 49233, ""),
    ],
    "2025-26-topps-signature-class-bkb-hobby": [
        ("Base", "base", None, False, False, None, ""),
        ("Chrome Refractor", "parallel", None, False, False, 6, ""),
        ("Magenta Refractor", "parallel", 250, False, False, 58, ""),
        ("Teal Refractor", "parallel", 225, False, False, 64, ""),
        ("Indigo Refractor", "parallel", 175, False, False, 82, ""),
        ("Green Refractor", "parallel", 150, False, False, 96, ""),
        ("Purple Refractor", "parallel", 199, False, False, 143, "listed /199 out of ladder order"),
        ("Pink Refractor", "parallel", 75, False, False, 191, ""),
        ("Orange Refractor", "parallel", 50, False, False, 286, ""),
        ("Red Refractor", "parallel", 25, False, False, 571, ""),
        ("Red Lava Refractor", "parallel", 25, False, False, 571, ""),
        ("Gold Refractor", "parallel", 10, False, False, 1426, ""),
        ("Blue Refractor", "parallel", 5, False, False, 2851, ""),
        ("SuperFractor", "parallel", 1, False, False, 14661, ""),
        ("After Image", "auto", None, True, False, 12, "autographed insert"),
        ("Manuscripts", "auto", None, True, False, 24, ""),
        ("Penstroke Signatures", "auto", None, True, False, 60, ""),
        ("Shadow Scripts", "auto", None, True, False, 90, ""),
        ("Algorithm", "auto", None, True, False, 110, "autographed insert"),
        ("Signature Blend", "auto", None, True, False, 135, ""),
        ("Crystal Clear Rookie Autographs", "auto", None, True, False, 179, ""),
        ("Fluidity", "auto", None, True, False, 329, "autographed insert"),
        ("Eternal Marks", "auto", None, True, False, 471, ""),
        ("Crystal Clear Veteran Autographs", "auto", None, True, False, 529, ""),
        ("Legends of Their Class Crystal Clear", "auto", None, True, False, 1086, ""),
        ("Dual Autographs", "auto", None, True, False, 2756, ""),
        ("Triple Autographs", "auto", None, True, False, 4830, ""),
        ("Chrome Rookie Autographs", "auto", None, True, False, None, "only parallel odds published"),
        ("Chrome Veteran Autographs", "auto", None, True, False, None, "only parallel odds published"),
    ],
}


def est_value(name, group, print_run, is_auto, is_ssp, odds_pack):
    """Crude per-tier USD placeholder. Replace with eBay sold-comp medians."""
    n = name.lower()
    if is_auto:
        if "triple" in n:
            return 600
        if "dual" in n:
            return 350
        if "debut patch" in n or "logoman" in n:
            return 5000
        if print_run is not None:
            if print_run <= 5:
                return 900
            if print_run <= 25:
                return 400
            if print_run <= 99:
                return 200
        if odds_pack and odds_pack >= 1500:
            return 250
        if "rookie" in n:
            return 150
        return 100
    if group == "base":
        return 0.5
    if group == "variation":
        return 40
    if group == "parallel":
        if print_run is None:
            if odds_pack and odds_pack >= 100:
                return 20
            if odds_pack and odds_pack >= 25:
                return 8
            return 3
        if print_run == 1:
            return 4000
        if print_run <= 3:
            return 900
        if print_run <= 5:
            return 550
        if print_run <= 10:
            return 300
        if print_run <= 25:
            return 120
        if print_run <= 50:
            return 70
        if print_run <= 99:
            return 45
        if print_run <= 175:
            return 28
        if print_run <= 299:
            return 16
        return 12
    if group == "insert":
        if is_ssp:
            return 150
        if odds_pack is None:
            return 15
        if odds_pack >= 500:
            return 120
        if odds_pack >= 50:
            return 30
        if odds_pack >= 15:
            return 12
        return 5
    return ""


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    products = build_products()
    prod_cols = [
        "product_id", "product_line", "product_name", "brand", "sport", "season_label",
        "release_year", "release_date", "box_format", "format_channel", "currency",
        "cards_per_pack", "packs_per_box", "boxes_per_case", "cards_per_box",
        "stated_autos_per_box", "stated_autos_per_case",
        "auto_odds_pack", "auto_odds_basis", "ssp_odds_pack",
        "srp_usd", "retail_price_usd", "retail_price_asof", "retail_price_source",
        "base_set_size", "odds_source_url", "source_note",
    ]
    with open(RAW / "box_products.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=prod_cols)
        w.writeheader()
        w.writerows(products)

    ppb_by_id = {p["product_id"]: p["packs_per_box"] for p in products}

    tier_cols = [
        "product_id", "box_format", "tier_name", "tier_group", "print_run",
        "is_numbered", "is_autograph", "is_ssp", "odds_pack", "odds_box",
        "est_value_usd", "value_basis", "source_note",
    ]
    n_tiers = 0
    with open(RAW / "card_tiers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=tier_cols)
        w.writeheader()
        for pid, rows in HOBBY_TIERS.items():
            ppb = ppb_by_id.get(pid)
            for (name, group, print_run, is_auto, is_ssp, odds_pack, note) in rows:
                odds_box = round(odds_pack / ppb, 2) if (odds_pack and ppb) else ""
                w.writerow({
                    "product_id": pid,
                    "box_format": "Hobby",
                    "tier_name": name,
                    "tier_group": group,
                    "print_run": "" if print_run is None else print_run,
                    "is_numbered": print_run is not None,
                    "is_autograph": is_auto,
                    "is_ssp": is_ssp,
                    "odds_pack": "" if odds_pack is None else odds_pack,
                    "odds_box": odds_box,
                    "est_value_usd": est_value(name, group, print_run, is_auto, is_ssp, odds_pack),
                    "value_basis": "rough_estimate_v0",
                    "source_note": note,
                })
                n_tiers += 1

    print(f"wrote {len(products)} box-format rows -> {RAW / 'box_products.csv'}")
    print(f"wrote {n_tiers} hobby tier rows -> {RAW / 'card_tiers.csv'}")


if __name__ == "__main__":
    main()
