"""
public_intel_map.py — turns a resolved category bucket into Serper queries.

Two uses of the category in a query:
  1. RISK_LEXICON  — WHAT bad thing to look for  (recall / pollution / explosion)
  2. PRODUCT_HINT  — WHICH "Sri Krishna Foods" this is  (disambiguation)

(2) is the one people forget, and it's the higher-value one.

Per vendor this yields at most 4 Serper queries (2 adverse + up to 2 portals).
Never OR a dozen terms into one query: long OR-chains plus a site: filter degrade
Google's ranking badly — two clean ~5-term queries beat one 10-term query.
"""

from dataclasses import dataclass, field

from app.core.category_resolver import (
    resolve_category, FOOD_INGREDIENT, FOOD_PACKAGING,
    GAS_CHEMICAL, CAPEX_COOLER, SERVICE_GENERAL,
)

# Applies to EVERY bucket — unioned in, never a fallback.
GENERIC_RISK = ["fraud", "penalty", "blacklisted", "raid", "insolvency"]

RISK_LEXICON = {
    FOOD_INGREDIENT: ["recall", "adulteration", "contamination",
                      "unsafe food", "sample failed"],
    FOOD_PACKAGING:  ["pollution", "closure notice", "environmental compensation",
                      "effluent", "NGT order"],
    GAS_CHEMICAL:    ["explosion", "gas leak", "factory accident",
                      "safety violation", "hazardous"],
    CAPEX_COOLER:    ["product recall", "defect", "consumer complaint", "fire"],
    SERVICE_GENERAL: ["lawsuit", "dispute", "non-payment"],
}

# Plain-English product words Google actually understands.
# NEVER put "IC CUPS" or "RM STAB." into a search query — no index has those.
PRODUCT_HINT = {
    FOOD_INGREDIENT: "food ingredients manufacturer",
    FOOD_PACKAGING:  "packaging manufacturer",
    GAS_CHEMICAL:    "industrial gas chemicals",
    CAPEX_COOLER:    "refrigeration equipment",
    SERVICE_GENERAL: "",
}

# Portal = (domain, keyword). Adding a portal = adding a tuple, not a function.
PORTAL_CHECKS = {
    FOOD_INGREDIENT: [("fssai.gov.in", "recall"),
                      ("foscos.fssai.gov.in", "recall")],
    FOOD_PACKAGING:  [("cpcb.nic.in", "direction"),
                      ("greentribunal.gov.in", "order")],
    GAS_CHEMICAL:    [("peso.gov.in", "accident"),
                      ("cpcb.nic.in", "direction")],
    CAPEX_COOLER:    [("bis.gov.in", "violation")],
    SERVICE_GENERAL: [],
}

# ── Display filtering ─────────────────────────────────────────────────────────
# Broad sector/product vocabulary used to keep only category-relevant items in the
# News & Media and Web & Reviews tabs. Much wider than RISK_LEXICON (which is only
# about *bad* events) because a legitimate, on-topic result may not mention any risk
# word — but it should still mention its sector. SERVICE_GENERAL has no vocabulary,
# so vendors in that bucket (and unrecognised categories) are never filtered.
RELEVANCE_TERMS = {
    FOOD_INGREDIENT: [
        "food", "ingredient", "edible", "dairy", "milk", "cream", "butter",
        "chocolate", "cocoa", "flavour", "flavor", "colour", "color", "fruit",
        "juice", "pulp", "sugar", "syrup", "spice", "biscuit", "cake", "candy",
        "confection", "beverage", "bakery", "nutrition", "fssai", "adulteration",
        "recall", "contamination", "fmcg",
    ],
    FOOD_PACKAGING: [
        "packaging", "packing", "pack", "carton", "laminate", "film", "label",
        "printing", "corrugat", "box", "foil", "pouch", "sachet", "cup", "lid",
        "tub", "closure", "bottle", "plastic", "paper", "flexible packaging",
        "cpcb", "ngt", "pollution", "effluent",
    ],
    GAS_CHEMICAL: [
        "gas", "chemical", "co2", "carbon dioxide", "nitrogen", "ammonia", "lpg",
        "oxygen", "solvent", "cylinder", "refrigerant", "industrial", "hazardous",
        "peso", "explosion", "leak", "caustic", "acid", "petrochemical",
    ],
    CAPEX_COOLER: [
        "cooler", "freezer", "refrigerat", "chiller", "visi", "cold storage",
        "hvac", "compressor", "equipment", "machine", "machinery", "appliance",
        "deep freezer", "bis",
    ],
    SERVICE_GENERAL: [],
}


def category_relevance(text: str, bucket: str) -> int:
    """
    Deterministic category-relevance score (no LLM). Counts case-insensitive
    substring hits of the bucket vocabulary. Buckets with no vocabulary
    (SERVICE_GENERAL / unknown) return a high score so nothing is filtered out.
    """
    terms = RELEVANCE_TERMS.get(bucket)
    if not terms:
        return 100
    t = (text or "").lower()
    hits = sum(1 for term in terms if term in t)
    return min(100, hits * 40)


def filter_relevant(items: list, bucket: str, fields: list[str]) -> tuple[list, bool]:
    """
    Keep only items whose combined `fields` text is relevant to the category.
    Returns (filtered_items, fell_back). If strict filtering would empty a
    non-empty list, the ORIGINAL list is returned with fell_back=True so callers
    can show a "no strong category match — showing all" note instead of a blank tab.
    """
    if not items:
        return items, False

    def _text(it) -> str:
        if not isinstance(it, dict):
            return str(it)
        return " ".join(str(it.get(f, "") or "") for f in fields)

    kept = [it for it in items if category_relevance(_text(it), bucket) > 0]
    if kept:
        return kept, False
    return items, True


@dataclass
class SerperPlan:
    bucket: str
    needs_review: bool
    note: str | None
    product_hint: str
    adverse_generic_q: str
    adverse_category_q: str
    portals: list = field(default_factory=list)   # list[(domain, keyword, query)]


def _clean(q: str) -> str:
    """Collapse the double-spaces left when location / hint are blank."""
    while "  " in q:
        q = q.replace("  ", " ")
    return q.strip()


def build_serper_plan(legal_name: str, category: str | None, location: str = "") -> SerperPlan:
    """
    Resolve the Excel category to a bucket, then build the (small, capped) set of
    Serper queries for that bucket. Location disambiguates same-named vendors.
    """
    res = resolve_category(category or "")
    bucket = res.bucket
    name = f'"{legal_name}"'
    loc = location or ""
    hint = PRODUCT_HINT[bucket]

    generic_q  = _clean(f'{name} {loc} ({" OR ".join(GENERIC_RISK)})')
    category_q = _clean(f'{name} {loc} {hint} ({" OR ".join(RISK_LEXICON[bucket])})')
    portals    = [(d, k, _clean(f'site:{d} {name} {k}')) for d, k in PORTAL_CHECKS[bucket]]

    return SerperPlan(
        bucket=bucket,
        needs_review=res.needs_review,
        note=res.note,
        product_hint=hint,
        adverse_generic_q=generic_q,
        adverse_category_q=category_q,
        portals=portals,
    )
