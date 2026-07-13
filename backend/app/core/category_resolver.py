"""
category_resolver.py — Excel free-text category -> compliance bucket.

Resolution order (first hit wins):
    1. EXACT_MAP        exact match on the normalized string  -> confidence "exact"
    2. RULES            ordered regex rules, most specific first -> confidence "rule"
    3. SERVICE_GENERAL  safe default                          -> confidence "fallback"

Anything in AMBIGUOUS resolves, but is flagged for analyst review in the UI.
No LLM call. Pure string work — runs in microseconds on a 5k-row Excel upload.
"""

import re
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Buckets
# --------------------------------------------------------------------------
FOOD_INGREDIENT = "FOOD_INGREDIENT"   # edible / goes into the product
FOOD_PACKAGING  = "FOOD_PACKAGING"    # food-contact + secondary packaging
GAS_CHEMICAL    = "GAS_CHEMICAL"      # industrial gas, process chemicals
CAPEX_COOLER    = "CAPEX_COOLER"      # equipment, freezers, visi-coolers
SERVICE_GENERAL = "SERVICE_GENERAL"   # services, admin, consumables

BUCKETS = (FOOD_INGREDIENT, FOOD_PACKAGING, GAS_CHEMICAL,
           CAPEX_COOLER, SERVICE_GENERAL)


# --------------------------------------------------------------------------
# Normalizer — collapses "Corru PAD", "CORRU  PAD", "corru-pad" to "CORRU PAD"
# --------------------------------------------------------------------------
def normalize(raw: str) -> str:
    if not raw:
        return ""
    s = raw.upper()
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)   # drops . , ( ) - /
    s = re.sub(r"\s+", " ", s).strip()
    return s


# --------------------------------------------------------------------------
# 1. EXACT MAP — the 62 procurement strings, normalized
# --------------------------------------------------------------------------
EXACT_MAP = {
    # ---- FOOD_INGREDIENT : edible, enters the product -----------------
    "RM":                     FOOD_INGREDIENT,
    "RM MAIN":                FOOD_INGREDIENT,
    "RM COMMON":              FOOD_INGREDIENT,
    "RM OTHER":               FOOD_INGREDIENT,
    "RM CHOCOLATE":           FOOD_INGREDIENT,
    "RM DRY FRUIT":           FOOD_INGREDIENT,
    "RM STAB":                FOOD_INGREDIENT,          # stabiliser
    "RM FLAVOUR":             FOOD_INGREDIENT,
    "RM COLOUR":              FOOD_INGREDIENT,
    "RM BISCIT":              FOOD_INGREDIENT,          # sic — Excel spelling
    "RM FRUIT":               FOOD_INGREDIENT,
    "RM CAKE":                FOOD_INGREDIENT,
    "RM JELLY":               FOOD_INGREDIENT,
    "RM CRUSH":               FOOD_INGREDIENT,
    "RM JUICE":               FOOD_INGREDIENT,
    "RM NDC":                 FOOD_INGREDIENT,          # non-dairy creamer
    "VAD RM":                 FOOD_INGREDIENT,          # value-added RM
    "PULP":                   FOOD_INGREDIENT,
    "DAIRY RAW MATERIAL":     FOOD_INGREDIENT,
    "MIX INGREDIENTS D":      FOOD_INGREDIENT,
    "CHOCO AND DRY FRUIT D":  FOOD_INGREDIENT,
    "FLAVOR AND COLOR D":     FOOD_INGREDIENT,
    "FRUIT JUICES AND PULP D":FOOD_INGREDIENT,
    "MISCE CONSUMABLES D":    FOOD_INGREDIENT,
    "NON DAIRY NON EXCISE":   FOOD_INGREDIENT,
    # Wafer cones are EDIBLE -> food, not packaging. See AMBIGUOUS note.
    "CONELARGE":              FOOD_INGREDIENT,
    "CONE LARGE":             FOOD_INGREDIENT,
    "CONESMALL":              FOOD_INGREDIENT,
    "CONE SMALL":             FOOD_INGREDIENT,
    "CONE LARGE PREMIUM":     FOOD_INGREDIENT,

    # ---- FOOD_PACKAGING : food-contact + secondary ---------------------
    "PM":                     FOOD_PACKAGING,
    "PMX":                    FOOD_PACKAGING,
    "PM NDC":                 FOOD_PACKAGING,
    "PM CHOC":                FOOD_PACKAGING,
    "IC CUPS":                FOOD_PACKAGING,
    "IC PREMIUM CUPS":        FOOD_PACKAGING,
    "IC MISC ITEMS PM":       FOOD_PACKAGING,
    "IC FILM ROLL":           FOOD_PACKAGING,
    "IC OUTERS":              FOOD_PACKAGING,
    "IC TUBS AND LIDS":       FOOD_PACKAGING,
    "IC LINERS":              FOOD_PACKAGING,
    "IC LIDS PAPER PACKAG":   FOOD_PACKAGING,
    "CORRU CARTON":           FOOD_PACKAGING,
    "CORRU PAD":              FOOD_PACKAGING,
    "LAMINATES":              FOOD_PACKAGING,
    "LABEL ROTO PRINTING":    FOOD_PACKAGING,
    "LABEL FLEXO PRINTING":   FOOD_PACKAGING,
    "CLOSURES":               FOOD_PACKAGING,
    "CAN":                    FOOD_PACKAGING,
    "STRAW":                  FOOD_PACKAGING,           # food-contact article
    "ICE BOX":                FOOD_PACKAGING,
    "JUMBOPACK":              FOOD_PACKAGING,
    "BP 4 LTR":               FOOD_PACKAGING,           # bulk pack
    "BP 5 LTR":               FOOD_PACKAGING,
    "PARTY PACK 1 LTR":       FOOD_PACKAGING,
    "PARTY PACK 700 ML":      FOOD_PACKAGING,
    "CASATTA AND CANDY MONO": FOOD_PACKAGING,           # mono carton

    # ---- GAS_CHEMICAL --------------------------------------------------
    "CO2":                    GAS_CHEMICAL,
    "SUGAR SYRUP CHEMICALS":  GAS_CHEMICAL,             # ambiguous, see below

    # ---- CAPEX_COOLER --------------------------------------------------
    "CAPEX":                  CAPEX_COOLER,
    "VISI":                   CAPEX_COOLER,             # visi-cooler

    # ---- SERVICE_GENERAL -----------------------------------------------
    "ADVERTISING AND MARKETING": SERVICE_GENERAL,
    "HOUSE KEEPING CONSUM":      SERVICE_GENERAL,
    "OYA":                       SERVICE_GENERAL,       # unknown, see below
}


# --------------------------------------------------------------------------
# Flagged for analyst review — resolves, but the UI should surface a warning
# --------------------------------------------------------------------------
AMBIGUOUS = {
    "CONELARGE": "Wafer cones are edible -> FOOD_INGREDIENT. If your cones are "
                 "sourced as packaging sleeves, re-map to FOOD_PACKAGING.",
    "CONESMALL": "Same as CONELARGE.",
    "CONE LARGE PREMIUM": "Same as CONELARGE.",
    "SUGAR SYRUP CHEMICALS": "If these are food-grade syrup inputs -> "
                             "FOOD_INGREDIENT. If CIP/process chemicals -> "
                             "GAS_CHEMICAL (current default).",
    "MISCE CONSUMABLES D": "'(D)' read as a dairy/production dept ingredient. "
                           "If these are non-edible plant consumables, re-map "
                           "to SERVICE_GENERAL.",
    "OYA": "Unrecognised code. Defaulted to SERVICE_GENERAL — please confirm.",
    "PMX": "Read as a packaging-material sub-ledger. Confirm.",
}


# --------------------------------------------------------------------------
# 2. RULES — ordered, most specific first. Catches free text + new codes.
#    e.g. "Food Ingredients", "Cooler CAPEX", "Gas / Chemicals", "RM SPICES"
# --------------------------------------------------------------------------
RULES = [
    # CAPEX first: "cooler capex" must not be caught by a packaging rule
    (r"\b(CAPEX|VISI|COOLER|DEEP FREEZER|FREEZER|CHILLER|MACHINE|"
     r"EQUIPMENT|PLANT)\b",                                      CAPEX_COOLER),

    # Gas / chemicals
    (r"\b(CO2|CARBON DIOXIDE|NITROGEN|AMMONIA|LPG|GAS|CHEMICAL|"
     r"SOLVENT|CIP|CAUSTIC|REFRIGERANT)\b",                      GAS_CHEMICAL),

    # Services / admin  (before packaging: "marketing collateral printing")
    (r"\b(ADVERTIS|MARKETING|MEDIA|AGENCY|SERVICE|MANPOWER|"
     r"HOUSE ?KEEPING|SECURITY|TRANSPORT|LOGISTIC|CONSULT|"
     r"STATIONERY|IT|SOFTWARE)\b",                               SERVICE_GENERAL),

    # Packaging  (PM prefix, IC prefix, and every packaging noun).
    # Stems use \w* so PACKAGING / LAMINATES / CLOSURES / PRINTING all match.
    # Short ambiguous tokens (CAN, CAP, PET) keep a hard \b.
    (r"^(PM|PMX|IC)\b",                                          FOOD_PACKAGING),
    (r"\b(PACKAG\w*|PACK\b|CUP\w*|LID\w*|TUB\w*|CARTON\w*|CORRU\w*|"
     r"BOX\w*|FILM\w*|FOIL\w*|LAMINAT\w*|LABEL\w*|PRINT\w*|CLOSURE\w*|"
     r"LINER\w*|OUTER\w*|SLEEVE\w*|POUCH\w*|SACHET\w*|WRAPPER\w*|"
     r"SHRINK\w*|CRATE\w*|PALLET\w*|STRAW\w*|SPOON\w*|"
     r"CAN\b|CAP\b|PET\b|BOPP\b|MONO\b|BP \d)",                  FOOD_PACKAGING),

    # Food ingredients  (RM prefix, and every edible noun)
    (r"^(RM|VAD RM)\b",                                          FOOD_INGREDIENT),
    (r"\b(FOOD\w*|INGREDIENT\w*|EDIBLE|DAIRY|MILK|CREAM\w*|BUTTER|"
     r"CHOCO\w*|COCOA|FRUIT\w*|JUICE\w*|PULP|SUGAR|FLAVOUR\w*|FLAVOR\w*|"
     r"COLOUR\w*|COLOR\w*|STAB\w*|EMULSIF\w*|BISC\w*|CAKE\w*|JELLY|"
     r"CRUSH|CONE\w*|WAFER\w*|CANDY|SYRUP|SPICE\w*|NUT\b|SMP\b|"
     r"NDC\b|NON DAIRY)",                                        FOOD_INGREDIENT),
]

COMPILED = [(re.compile(p), b) for p, b in RULES]


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
@dataclass
class CategoryResolution:
    raw: str
    normalized: str
    bucket: str
    confidence: str            # "exact" | "rule" | "fallback"
    needs_review: bool
    note: str | None = None


def resolve_category(raw: str) -> CategoryResolution:
    n = normalize(raw)

    if n in EXACT_MAP:
        return CategoryResolution(
            raw=raw, normalized=n, bucket=EXACT_MAP[n], confidence="exact",
            needs_review=n in AMBIGUOUS, note=AMBIGUOUS.get(n),
        )

    for pattern, bucket in COMPILED:
        if pattern.search(n):
            return CategoryResolution(
                raw=raw, normalized=n, bucket=bucket, confidence="rule",
                needs_review=False,
                note="Matched by rule, not in the known category list.",
            )

    return CategoryResolution(
        raw=raw, normalized=n, bucket=SERVICE_GENERAL, confidence="fallback",
        needs_review=True,
        note="Unrecognised category — defaulted to SERVICE_GENERAL. "
             "Only universal (news/litigation) checks will run.",
    )


def _match_category(raw: str) -> str:
    """Convenience shim: raw category string -> bucket."""
    return resolve_category(raw).bucket


# --------------------------------------------------------------------------
# Self-test: every one of the 62 Excel strings must hit EXACT_MAP.
# --------------------------------------------------------------------------
if __name__ == "__main__":
    EXCEL = [
        "IC CUPS", "IC PREMIUM CUPS", "IC MISC ITEMS PM", "PM", "RM", "PULP",
        "IC FILM ROLL", "Capex", "Visi", "RM COMMON", "CORRU CARTON",
        "BP 4 LTR", "RM MAIN", "CONELARGE", "Corru PAD", "VAD RM",
        "RM CHOCOLATE", "OYA", "IC OUTERS", "Advertising & marketing",
        "IC TUBS & LIDS", "RM DRY FRUIT", "RM NDC", "Mix Ingredients(D)",
        "Choco & Dry Fruit(D)", "RM STAB.", "RM FLAVOUR",
        "CASATTA & CANDY MONO", "PM NDC", "CONE LARGE PREMIUM",
        "PARTY PACK 1 LTR", "IC LINERS", "Non Dairy-Non Excise", "RM BISCIT",
        "PMX", "RM OTHER", "RM FRUIT", "RM CAKE", "ICE BOX",
        "PARTY PACK 700 ML", "Flavor and color (D)", "RM JELLY",
        "HOUSE KEEPING CONSUM", "RM COLOUR", "IC LIDS PAPER PACKAG", "PM CHOC",
        "CONESMALL", "RM CRUSH", "Can", "BP 5 LTR", "Fruit,Juices&Pulp(D)",
        "DAIRY RAW MATERIAL", "Misce Consumables(D)", "Laminates",
        "Label -Roto Printing", "Closures", "Label -Flexo Printing", "Straw ",
        "Sugar Syrup Chemicals", "CO2", "RM JUICE", "JUMBOPACK",
    ]
    tally, misses = {}, []
    for c in EXCEL:
        r = resolve_category(c)
        tally[r.bucket] = tally.get(r.bucket, 0) + 1
        if r.confidence != "exact":
            misses.append((c, r.confidence, r.bucket))
        flag = "  <-- REVIEW" if r.needs_review else ""
        print(f"{c:<26} -> {r.bucket:<17} [{r.confidence}]{flag}")

    print("\n--- free-text (what procurement actually types) ---")
    for c in ["Food Ingredients", "Gas / Chemicals", "Cooler CAPEX",
              "Primary Packaging", "RM SPICES", "Legal retainer", "zzz"]:
        r = resolve_category(c)
        print(f"{c:<26} -> {r.bucket:<17} [{r.confidence}]")

    print(f"\nTotal: {len(EXCEL)}   Tally: {tally}")
    print(f"Non-exact among the 62: {misses if misses else 'NONE — all mapped'}")
