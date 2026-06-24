from app.api.endpoints import (
    opencorp, opensanctions, gdelt, whois_api, ssl_api, sandbox_api,
    serper_api, news_api, google_places_api, microlink_api, wikipedia_api
)
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

async def _gather_sandbox(jurisdiction_country, tax_identifier, pan_number, msmed_certificate_number):
    if jurisdiction_country and jurisdiction_country.upper() == "IN":
        tsp_results = {}
        if tax_identifier:
            tsp_results["gstin"] = await sandbox_api.verify_gstin(tax_identifier)
        if pan_number:
            tsp_results["pan"] = await sandbox_api.verify_pan(pan_number)
        if msmed_certificate_number:
            tsp_results["msmed"] = await sandbox_api.verify_msmed(msmed_certificate_number)
        return tsp_results
    return {}

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
    run Serper, GDELT, and OpenSanctions searches.
    Also run a more precise Google Places lookup using the GSTIN registered address.
    """
    tasks = []

    for name in intel.get("additional_names", []):
        tasks.append(_safe_call(
            f"enrich_serper_{name}",
            serper_api.search(f'"{name}" fraud scam complaints news reviews')
        ))
        tasks.append(_safe_call(
            f"enrich_gdelt_{name}",
            gdelt.search_news(name)
        ))
        tasks.append(_safe_call(
            f"enrich_sanctions_{name}",
            opensanctions.search_entity(name)
        ))

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
    for name in intel.get("additional_names", []):
        enrichment["by_alternate_name"][name] = {
            "serper": raw.get(f"enrich_serper_{name}"),
            "gdelt": raw.get(f"enrich_gdelt_{name}"),
            "sanctions": raw.get(f"enrich_sanctions_{name}")
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
    social_handles: Optional[dict] = None
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

    # ── Phase 1: core tasks ────────────────────────────────────────────────
    tasks = [
        _safe_call("opencorporates", opencorp.search_company(
            legal_name, jurisdiction=jurisdiction_country.lower() if jurisdiction_country else "us"
        )),
        _safe_call("opensanctions", _gather_sanctions(all_names)),
        _safe_call("gdelt", _gather_gdelt(legal_name, founder_ceo_name, director_names)),
        # Adverse search — fraud / scam / complaints
        _safe_call("serper", serper_api.search(f"{legal_name} fraud scam complaints reviews")),
        _safe_call("newsapi", news_api.search_news(f"{legal_name} AND (fraud OR scandal OR lawsuit)")),
        # Customer/employee reviews — Trustpilot, Glassdoor, G2, AmbitionBox
        _safe_call("serper_reviews", serper_api.search(
            f'"{legal_name}" reviews rating site:trustpilot.com OR site:glassdoor.com OR site:g2.com OR site:ambitionbox.com'
        )),
        # General company profile — founding, HQ, size, leadership
        _safe_call("serper_profile", serper_api.search(
            f'"{legal_name}" company founded headquarters employees overview'
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

    tasks.append(_safe_call("sandbox_tsp", _gather_sandbox(
        jurisdiction_country, tax_identifier, pan_number, msmed_certificate_number
    )))

    results_phase1 = await asyncio.gather(*tasks)
    aggregated = {k: v for k, v in results_phase1}

    # ── Phase 2: sandbox-driven enrichment (India only) ───────────────────
    sandbox_results = aggregated.get("sandbox_tsp", {})
    if sandbox_results and isinstance(sandbox_results, dict) and not sandbox_results.get("error"):
        intel = _extract_sandbox_intel(sandbox_results, legal_name)
        aggregated["sandbox_intel"] = intel

        if intel["additional_names"] or intel["registered_address"]:
            logger.info(
                f"Phase 2 enrichment: {len(intel['additional_names'])} alternate name(s) found — "
                f"{intel['additional_names']}"
            )
            enrichment = await _enrich_from_sandbox_intel(intel, legal_name)
            aggregated["sandbox_enrichment"] = enrichment

    return aggregated