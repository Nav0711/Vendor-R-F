from app.api.endpoints import (
    opencorp, opensanctions, gdelt, whois_api, ssl_api,
    authbridge_api, sandbox_api,  # sandbox_api is an alias for authbridge_api
    serper_api, ecourts_api, news_api, google_places_api, microlink_api, wikipedia_api
)
from app.core.public_intel_map import build_serper_plan
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def _safe_call(api_name, coro):
    try:
        return api_name, await coro
    except Exception as e:
        logger.error(f"{api_name} Aggregation failed: {e}")
        return api_name, {"error": str(e)}

async def _gather_sanctions(all_names):
    sanctions_results = {}
    for name in all_names:
        if name:
            sanctions_results[name] = await opensanctions.search_entity(name)
    return sanctions_results

async def _gather_gdelt(legal_name, founder_ceo_name, director_names=None):
    """Search GDELT for company, CEO/founder, and up to 2 directors."""
    news_results = {}
    news_results[legal_name] = await gdelt.search_news(legal_name)
    if founder_ceo_name:
        news_results[founder_ceo_name] = await gdelt.search_news(founder_ceo_name)
    for director in (director_names or [])[:2]:
        if director and director not in (founder_ceo_name, legal_name):
            news_results[director] = await gdelt.search_news(director)
    return news_results

async def _gather_authbridge(
    jurisdiction_country, tax_identifier, pan_number, msmed_certificate_number,
    legal_name=None, director_names=None, director_din=None,
    founder_ceo_name=None, corporate_email_domain=None,
):
    """
    Run all AuthBridge checks in parallel:
    - Universal (any vendor, if key set): email verification, court check,
      defaulting director, global sanctions
    - India-specific: GSTIN, PAN, MSME verification
    """
    # A placeholder key ("your_authbridge_api_key_here") is truthy, so a bare
    # truthiness check let the scan attempt live calls against an unconfigured host.
    if not authbridge_api.is_configured:
        logger.info("AuthBridge not configured (need AUTHBRIDGE_API_KEY + AUTHBRIDGE_BASE_URL) — skipping")
        return {}

    tasks = []
    keys  = []

    # ── Universal checks ──────────────────────────────────────────────────
    if corporate_email_domain:
        tasks.append(authbridge_api.verify_email(corporate_email_domain))
        keys.append("email_verification")

    # Court check: entity + each director + founder
    if legal_name:
        tasks.append(ecourts_api.search_party(legal_name))
        keys.append("court_entity")
    for i, d in enumerate((director_names or [])[:5]):
        if d:
            tasks.append(ecourts_api.search_party(d))
            keys.append(f"court_dir_{i}")
    if founder_ceo_name:
        tasks.append(ecourts_api.search_party(founder_ceo_name))
        keys.append("court_founder")

    # Defaulting director: each director + founder
    for i, d in enumerate((director_names or [])[:5]):
        if d:
            din = (director_din or [])[i] if director_din and i < len(director_din) else None
            tasks.append(authbridge_api.check_defaulting_director(d, din=din))
            keys.append(f"default_dir_{i}")
    if founder_ceo_name:
        tasks.append(authbridge_api.check_defaulting_director(founder_ceo_name))
        keys.append("default_founder")

    # Global sanctions: entity + each director + founder
    if legal_name:
        tasks.append(authbridge_api.check_global_sanctions(legal_name, entity_type="company"))
        keys.append("sanctions_entity")
    for i, d in enumerate((director_names or [])[:5]):
        if d:
            tasks.append(authbridge_api.check_global_sanctions(d, entity_type="individual"))
            keys.append(f"sanctions_dir_{i}")
    if founder_ceo_name:
        tasks.append(authbridge_api.check_global_sanctions(founder_ceo_name, entity_type="individual"))
        keys.append("sanctions_founder")

    # ── India-specific checks ─────────────────────────────────────────────
    is_india     = jurisdiction_country and jurisdiction_country.upper() in ("IN", "IND", "INDIA")
    has_india_id = any([tax_identifier, pan_number, msmed_certificate_number])
    if is_india or has_india_id:
        if tax_identifier:
            tasks.append(authbridge_api.verify_gstin(tax_identifier))
            keys.append("gstin")
        if pan_number:
            tasks.append(authbridge_api.verify_pan(pan_number))
            keys.append("pan")
        if msmed_certificate_number:
            tasks.append(authbridge_api.verify_msmed(msmed_certificate_number))
            keys.append("msmed")

    if not tasks:
        return {}

    settled = await asyncio.gather(*tasks, return_exceptions=True)
    raw = {k: (v if not isinstance(v, Exception) else {"error": str(v)})
           for k, v in zip(keys, settled)}

    result = {}

    # Email
    if "email_verification" in raw:
        result["email_verification"] = raw["email_verification"]

    # Court check — group into {entity_name: result}
    court = {}
    if "court_entity" in raw and legal_name:
        court[legal_name] = raw["court_entity"]
    for i, d in enumerate((director_names or [])[:5]):
        if d and f"court_dir_{i}" in raw:
            court[d] = raw[f"court_dir_{i}"]
    if founder_ceo_name and "court_founder" in raw:
        court[founder_ceo_name] = raw["court_founder"]
    if court:
        result["court_check"] = court

    # Defaulting director — group into {director_name: result}
    defaulting = {}
    for i, d in enumerate((director_names or [])[:5]):
        if d and f"default_dir_{i}" in raw:
            defaulting[d] = raw[f"default_dir_{i}"]
    if founder_ceo_name and "default_founder" in raw:
        defaulting[founder_ceo_name] = raw["default_founder"]
    if defaulting:
        result["defaulting_director"] = defaulting

    # Global sanctions — group into {name: result}
    sanctions_ab = {}
    if "sanctions_entity" in raw and legal_name:
        sanctions_ab[legal_name] = raw["sanctions_entity"]
    for i, d in enumerate((director_names or [])[:5]):
        if d and f"sanctions_dir_{i}" in raw:
            sanctions_ab[d] = raw[f"sanctions_dir_{i}"]
    if founder_ceo_name and "sanctions_founder" in raw:
        sanctions_ab[founder_ceo_name] = raw["sanctions_founder"]
    if sanctions_ab:
        result["global_sanctions"] = sanctions_ab

    # India IDs
    for k in ("gstin", "pan", "msmed"):
        if k in raw:
            result[k] = raw[k]

    return result


# Keep old name as alias so Phase 2 references still compile
_gather_sandbox = _gather_authbridge

async def _async_return(val):
    return val


def _extract_sandbox_intel(sandbox_results: dict, legal_name: str) -> dict:
    """
    Extract additional searchable entities from Sandbox verification responses.

    GSTIN gives trade name, registered address, business type, industry.
    PAN gives the name registered with the tax authority.
    MSMED gives enterprise name, district/state, and activity type.
    Any name that differs from legal_name is a candidate for cross-checking.
    """
    intel = {
        "additional_names": [],     # Alternate/trade names to re-search in other APIs
        "registered_address": None, # Full address from GSTIN pradr block
        "business_type": None,      # e.g. "Private Limited Company"
        "industry": None,           # Nature of business / activity
        "location": None,           # City/district from GSTIN or MSMED
    }
    legal_lower = (legal_name or "").lower().strip()

    # ── GSTIN ──────────────────────────────────────────────────────────────
    gstin_data = sandbox_results.get("gstin", {})
    if gstin_data and not gstin_data.get("error"):
        raw = gstin_data.get("raw_response", {})

        # Trade name is the operating name; lgnm is the full legal registered name
        for field in ("tradeNam", "lgnm"):
            name = (raw.get(field) or "").strip()
            if name and name.lower() != legal_lower and name not in intel["additional_names"]:
                intel["additional_names"].append(name)

        # Principal registered address (building/street → locality → district → state → pin)
        pradr = raw.get("pradr", {})
        if pradr:
            parts = filter(None, [
                pradr.get("adr") or pradr.get("bno"),
                pradr.get("loc"),
                pradr.get("dst"),
                pradr.get("stcd"),
                pradr.get("pncd"),
            ])
            addr = ", ".join(parts)
            if addr:
                intel["registered_address"] = addr
                intel["location"] = pradr.get("dst") or pradr.get("loc")

        intel["business_type"] = raw.get("ctb")
        nba = raw.get("nba", [])
        if nba:
            intel["industry"] = ", ".join(nba[:3]) if isinstance(nba, list) else str(nba)

    # ── PAN ────────────────────────────────────────────────────────────────
    pan_data = sandbox_results.get("pan", {})
    if pan_data and not pan_data.get("error"):
        pan_name = (pan_data.get("name") or "").strip()
        if pan_name and pan_name.lower() != legal_lower and pan_name not in intel["additional_names"]:
            intel["additional_names"].append(pan_name)

    # ── MSMED ──────────────────────────────────────────────────────────────
    msmed_data = sandbox_results.get("msmed", {})
    if msmed_data and not msmed_data.get("error"):
        msmed_name = (msmed_data.get("name") or "").strip()
        if msmed_name and msmed_name.lower() != legal_lower and msmed_name not in intel["additional_names"]:
            intel["additional_names"].append(msmed_name)

        if not intel["industry"] and msmed_data.get("activity"):
            intel["industry"] = msmed_data["activity"]

        if not intel["location"] and msmed_data.get("district"):
            intel["location"] = msmed_data["district"]

    return intel


async def _enrich_from_sandbox_intel(intel: dict, legal_name: str) -> dict:
    """
    Phase 2 enrichment: for every alternate name found in GSTIN/PAN/MSMED,
    re-run the full text-search graph (Serper adverse/reviews/profile/news,
    NewsAPI adverse + regulatory, GDELT, OpenSanctions, Wikipedia, OpenCorporates)
    so the whole intelligence picture is searched under the company's real
    registered names — not just the name typed into the form.
    Also run a precise Google Places lookup using the GSTIN registered address.
    """
    tasks = []
    names = intel.get("additional_names", [])

    # The full per-name search set (mirrors the Phase-1 queries).
    # (task_key, coroutine factory) — index-keyed below to avoid name collisions.
    def _name_tasks(name: str) -> dict:
        return {
            "serper_adverse":     serper_api.search(f'"{name}" fraud scam complaints reviews'),
            "serper_reviews":     serper_api.search(
                f'"{name}" reviews rating site:trustpilot.com OR site:glassdoor.com OR site:g2.com OR site:ambitionbox.com'
            ),
            "serper_profile":     serper_api.search(f'"{name}" company founded headquarters employees overview'),
            "serper_news":        serper_api.search(f'"{name}" latest news announcement update'),
            "newsapi_adverse":    news_api.search_news(f"{name} AND (fraud OR scandal OR lawsuit)"),
            "newsapi_regulatory": news_api.search_news(
                f"{name} AND (penalty OR fine OR SEBI OR SEC OR regulatory OR compliance)"
            ),
            "gdelt":              gdelt.search_news(name),
            "sanctions":          opensanctions.search_entity(name),
            "wikipedia":          wikipedia_api.get_summary(name),
            "opencorporates":     opencorp.search_company(name, jurisdiction="in"),
        }

    for i, name in enumerate(names):
        for task_key, coro in _name_tasks(name).items():
            tasks.append(_safe_call(f"enrich_{i}_{task_key}", coro))

    # Use the verified GSTIN address for a precise physical presence check
    addr = intel.get("registered_address")
    if addr:
        tasks.append(_safe_call(
            "enrich_places_gstin",
            google_places_api.search_address(f"{legal_name} {addr}")
        ))

    if not tasks:
        return {}

    results = await asyncio.gather(*tasks)
    raw = {k: v for k, v in results}

    # Structure by alternate name for easy LLM consumption
    enrichment = {
        "by_alternate_name": {},
        "gstin_address_places": raw.get("enrich_places_gstin")
    }
    for i, name in enumerate(names):
        enrichment["by_alternate_name"][name] = {
            "serper_adverse":     raw.get(f"enrich_{i}_serper_adverse"),
            "serper_reviews":     raw.get(f"enrich_{i}_serper_reviews"),
            "serper_profile":     raw.get(f"enrich_{i}_serper_profile"),
            "serper_news":        raw.get(f"enrich_{i}_serper_news"),
            "newsapi_adverse":    raw.get(f"enrich_{i}_newsapi_adverse"),
            "newsapi_regulatory": raw.get(f"enrich_{i}_newsapi_regulatory"),
            "gdelt":              raw.get(f"enrich_{i}_gdelt"),
            "sanctions":          raw.get(f"enrich_{i}_sanctions"),
            "wikipedia":          raw.get(f"enrich_{i}_wikipedia"),
            "opencorporates":     raw.get(f"enrich_{i}_opencorporates"),
        }

    return enrichment


async def aggregate_vendor_data(
    legal_name: str,
    website_domain: Optional[str],
    registration_number: Optional[str],
    jurisdiction_country: Optional[str],
    director_names: list[str],
    director_din: list[str],
    founder_ceo_name: Optional[str],
    tax_identifier: Optional[str] = None,
    pan_number: Optional[str] = None,
    msmed_certificate_number: Optional[str] = None,
    city: Optional[str] = None,
    registered_address: Optional[str] = None,
    social_handles: Optional[dict] = None,
    corporate_email_domain: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """
    Two-phase vendor intelligence aggregation.

    Phase 1 — parallel core lookups (all APIs fired simultaneously).
    Phase 2 — sandbox-driven enrichment: trade names / addresses from GSTIN/PAN/MSMED
               are fed into Serper, GDELT, OpenSanctions, and Google Places for deeper intel.
    """
    all_names = [legal_name] + (director_names or [])
    if founder_ceo_name and founder_ceo_name not in all_names:
        all_names.append(founder_ceo_name)

    # ── Category-oriented Serper plan ──────────────────────────────────────
    # Resolve the Excel category to a compliance bucket, then tailor the adverse
    # web search + government-portal checks to that bucket. The raw Excel code
    # (e.g. "RM CHOCOLATE") is never searched directly — a plain-English product
    # hint ("food ingredients manufacturer") is used to disambiguate the entity.
    location = city or jurisdiction_country or ""
    serper_plan = build_serper_plan(legal_name, category, location)
    logger.info("Category '%s' → bucket %s (%d portal checks)",
                category, serper_plan.bucket, len(serper_plan.portals))

    # ── Phase 1: core tasks ────────────────────────────────────────────────
    tasks = [
        _safe_call("opencorporates", opencorp.search_company(
            legal_name, jurisdiction=jurisdiction_country.lower() if jurisdiction_country else "us"
        )),
        _safe_call("opensanctions", _gather_sanctions(all_names)),
        _safe_call("gdelt", _gather_gdelt(legal_name, founder_ceo_name, director_names)),
        # Adverse web search — universal risk terms (Serper)
        _safe_call("serper", serper_api.search(serper_plan.adverse_generic_q)),
        # Adverse web search — category-specific risk terms + product hint (Serper)
        _safe_call("serper_category", serper_api.search(serper_plan.adverse_category_q)),
        _safe_call("newsapi", news_api.search_news(f"{legal_name} AND (fraud OR scandal OR lawsuit)")),
        # Customer/employee reviews — Trustpilot, Glassdoor, G2, AmbitionBox
        _safe_call("serper_reviews", serper_api.search(
            f'"{legal_name}" reviews rating site:trustpilot.com OR site:glassdoor.com OR site:g2.com OR site:ambitionbox.com'
        )),
        # General company profile — founding, HQ, size, leadership.
        # Product hint (from the resolved bucket) disambiguates same-named firms.
        _safe_call("serper_profile", serper_api.search(
            f'"{legal_name}" {serper_plan.product_hint} company founded headquarters employees overview'.replace("  ", " ").strip()
        )),
        # Latest general news
        _safe_call("serper_news", serper_api.search(
            f'"{legal_name}" latest news announcement update'
        )),
        # Wikipedia company overview (free, no auth)
        _safe_call("wikipedia", wikipedia_api.get_summary(legal_name)),
        # NewsAPI — financial / regulatory angle
        _safe_call("newsapi_regulatory", news_api.search_news(
            f"{legal_name} AND (penalty OR fine OR SEBI OR SEC OR regulatory OR compliance)"
        )),
    ]

    # Category government-portal checks — site-restricted Serper (FSSAI/CPCB/PESO/NGT/BIS)
    for i, (_domain, _keyword, portal_q) in enumerate(serper_plan.portals):
        tasks.append(_safe_call(f"serper_portal_{i}", serper_api.search(portal_q)))

    if website_domain:
        tasks.extend([
            _safe_call("whois", whois_api.search_domain(website_domain)),
            _safe_call("ssl", ssl_api.check_ssl(website_domain)),
            _safe_call("microlink", microlink_api.get_metadata(website_domain)),
        ])
    else:
        tasks.extend([
            _safe_call("whois", _async_return({"error": "No domain provided"})),
            _safe_call("ssl", _async_return({"error": "No domain provided"})),
            _safe_call("microlink", _async_return({"error": "No domain provided"})),
        ])

    # Google Places — prefer city or registered_address over bare country
    if city:
        address_query = f"{legal_name} {city} {jurisdiction_country or ''}".strip()
    elif registered_address:
        address_query = f"{legal_name} {registered_address}".strip()
    else:
        address_query = f"{legal_name} {jurisdiction_country or ''}".strip()
    tasks.append(_safe_call("google_places", google_places_api.search_address(address_query)))

    tasks.append(_safe_call("authbridge_tsp", _gather_authbridge(
        jurisdiction_country, tax_identifier, pan_number, msmed_certificate_number,
        legal_name=legal_name,
        director_names=director_names,
        director_din=director_din,
        founder_ceo_name=founder_ceo_name,
        corporate_email_domain=corporate_email_domain,
    )))

    results_phase1 = await asyncio.gather(*tasks)
    aggregated = {k: v for k, v in results_phase1}

    # ── Category metadata + collapse portal checks into one list ───────────
    aggregated["category_bucket"] = serper_plan.bucket
    aggregated["category_needs_review"] = serper_plan.needs_review
    portals = []
    for i, (domain, keyword, portal_q) in enumerate(serper_plan.portals):
        r = aggregated.pop(f"serper_portal_{i}", None) or {}
        portals.append({
            "domain": domain,
            "keyword": keyword,
            "organic": r.get("organic", []),
        })
    aggregated["serper_portals"] = portals

    # ── Phase 2: AuthBridge-driven alternate-name enrichment (India only) ─
    ab_results = aggregated.get("authbridge_tsp", {})
    # Also keep sandbox_tsp key for backwards compat with main.py / LLM prompt
    aggregated["sandbox_tsp"] = ab_results
    if ab_results and isinstance(ab_results, dict) and not ab_results.get("error"):
        intel = _extract_sandbox_intel(ab_results, legal_name)
        aggregated["sandbox_intel"] = intel
        aggregated["authbridge_intel"] = intel

        if intel["additional_names"] or intel["registered_address"]:
            logger.info(
                f"Phase 2 enrichment: {len(intel['additional_names'])} alternate name(s) — "
                f"{intel['additional_names']}"
            )
            enrichment = await _enrich_from_sandbox_intel(intel, legal_name)
            aggregated["sandbox_enrichment"] = enrichment
            aggregated["authbridge_enrichment"] = enrichment

    return aggregated