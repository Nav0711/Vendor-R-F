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
