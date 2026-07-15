from google import genai
import anthropic
import json
import os
import logging
import random

from app.services.gemini_budget import gemini_budget

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true" or os.getenv("TEST_MODE", "false").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
# Haiku is the cheapest Claude model (~$0.02/scan) and still supports the JSON
# schema enforcement the report pipeline depends on.
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")
# auto | anthropic | studio | vertex — override if prefix detection ever guesses wrong
GEMINI_API_BACKEND = os.getenv("GEMINI_API_BACKEND", "auto").lower()


def _build_client(key):
    """Route on the key prefix — each provider speaks to a different endpoint:
        sk-ant-  → Anthropic Messages API
        AQ.      → Gemini via Vertex AI express mode
        AIza     → Gemini via AI Studio
    Returns (provider, client) so the call site knows which SDK it's holding."""
    if not key:
        return None, None

    mode = GEMINI_API_BACKEND
    if mode == "auto":
        if key.startswith("sk-ant-"):
            mode = "anthropic"
        elif key.startswith("AQ."):
            mode = "vertex"
        else:
            mode = "studio"

    if mode == "anthropic":
        logger.info("LLM: Anthropic Messages API (model=%s)", ANTHROPIC_MODEL)
        return "anthropic", anthropic.AsyncAnthropic(api_key=key)

    if mode == "vertex":
        logger.info("LLM: Gemini via Vertex AI express mode (key prefix AQ.)")
        return "gemini", genai.Client(vertexai=True, api_key=key)

    logger.info("LLM: Gemini via AI Studio / Developer API")
    return "gemini", genai.Client(api_key=key)


PROVIDER, client = _build_client(api_key)
LLM_MODEL = ANTHROPIC_MODEL if PROVIDER == "anthropic" else GEMINI_MODEL

_CLEAN_SECTION_ANALYSIS = {
    "corporate_registry":   {"summary": "Entity shows active registration with no dissolution or filing irregularities detected.", "relevance": 85, "criticality": 10},
    "sanctions_watchlists": {"summary": "No matches found on major international watchlists or PEP databases.", "relevance": 90, "criticality": 5},
    "domain_ssl":           {"summary": "Domain is established with a valid SSL certificate; no anomalies detected.", "relevance": 60, "criticality": 8},
    "physical_address":     {"summary": "Business address is verifiable and shows operational status.", "relevance": 55, "criticality": 10},
    "wikipedia":            {"summary": "Entity has a public Wikipedia presence indicating established market recognition.", "relevance": 40, "criticality": 5},
    "news_media":           {"summary": "No significant adverse media coverage found across monitored news channels.", "relevance": 70, "criticality": 8},
    "reviews":              {"summary": "Customer and employee review data does not indicate systemic reputational issues.", "relevance": 65, "criticality": 12},
    "company_profile":      {"summary": "Company profile data is consistent across multiple sources with no contradictions.", "relevance": 60, "criticality": 8},
    "adverse_web":          {"summary": "Web search returns no fraud or scam allegations for this entity.", "relevance": 75, "criticality": 5},
}

_CLEAN_ARTICLE_ANALYSIS = [
    {"index": 0, "summary": "Routine industry coverage with no adverse signals detected.", "relevance": 45, "criticality": 8},
    {"index": 1, "summary": "General regulatory compliance article; no company-specific issues mentioned.", "relevance": 50, "criticality": 10},
]

# ── Response schema (Anthropic structured outputs) ────────────────────────────
# Gemini's response_mime_type only asks for *valid* JSON; Claude enforces an actual
# schema. That matters most for the three blocks the dashboard leans on — the news
# index, the adverse-web hits, and the reviews — because a malformed response used
# to land in the heuristic fallback with the tokens already spent.
_SCORE_BLOCK = {
    "type": "object",
    "properties": {
        "summary":     {"type": "string"},
        "relevance":   {"type": "integer"},
        "criticality": {"type": "integer"},
    },
    "required": ["summary", "relevance", "criticality"],
    "additionalProperties": False,
}

_SECTION_KEYS = list(_CLEAN_SECTION_ANALYSIS.keys())

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "finding_type": {"type": "string", "enum": [
                        "sanctions_match", "news_adverse", "regulatory_issue", "pep_match",
                        "domain_risk", "address_risk", "review_risk", "name_mismatch", "other",
                    ]},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "title":            {"type": "string"},
                    "description":      {"type": "string"},
                    "source_api":       {"type": "string"},
                    "source_url":       {"type": "string"},
                    "confidence_score": {"type": "number"},
                },
                "required": ["finding_type", "severity", "title", "description",
                             "source_api", "source_url", "confidence_score"],
                "additionalProperties": False,
            },
        },
        # Every section is required, so news_media / reviews / adverse_web always
        # come back scored — the model can't quietly omit the ones that matter.
        "section_analysis": {
            "type": "object",
            "properties": {k: _SCORE_BLOCK for k in _SECTION_KEYS},
            "required": _SECTION_KEYS,
            "additionalProperties": False,
        },
        "news_article_analysis": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index":       {"type": "integer"},
                    "summary":     {"type": "string"},
                    "relevance":   {"type": "integer"},
                    "criticality": {"type": "integer"},
                },
                "required": ["index", "summary", "relevance", "criticality"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["findings", "section_analysis", "news_article_analysis"],
    "additionalProperties": False,
}


async def _call_llm(prompt: str, max_out: int):
    """One prompt in, (raw JSON text, tokens spent) out — same contract either provider."""
    if PROVIDER == "anthropic":
        response = await client.messages.create(
            model=LLM_MODEL,
            max_tokens=max_out,
            # No temperature: Opus 4.7+/Sonnet 5 reject sampling params outright, so
            # omitting it keeps this call valid if ANTHROPIC_MODEL is ever changed.
            output_config={"format": {"type": "json_schema", "schema": _RESPONSE_SCHEMA}},
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "max_tokens":
            logger.warning("Claude hit the %d-token output ceiling — JSON is truncated", max_out)
        text = next((b.text for b in response.content if b.type == "text"), "")
        # Anthropic reports input and output separately; the budget wants the total.
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens

    response = await client.aio.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=max_out,
            response_mime_type="application/json",
        ),
    )
    tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
    return response.text, tokens


# ── Token optimisation ────────────────────────────────────────────────────────
# Gemini's free tier is billed on input tokens per request. The raw aggregated
# payload is huge: it carries verbose `raw_response` blobs, duplicate alias keys
# (sandbox_* mirror authbridge_*), and full news arrays that are ALSO sent in the
# flattened news index. We strip all of that before serialising so a single scan
# spends a fraction of the tokens.

# Heavy keys whose values are large verbatim API dumps not needed for analysis.
_DROP_KEYS = {"raw_response", "raw", "html", "content", "body", "_raw"}
# Alias keys that duplicate an authbridge_* key byte-for-byte.
_ALIAS_KEYS = {"sandbox_tsp", "sandbox_intel", "sandbox_enrichment"}
# News sources already represented (title + url + source) in the flat news index.
_NEWS_KEYS_IN_FLAT = {"gdelt", "newsapi", "newsapi_regulatory", "serper_news"}
# Per-alternate-name enrichment re-runs the whole search graph. Its news sub-results
# are already covered by the flat news index, so sending them again is the single
# largest redundant block in the prompt (~10 KB per alternate name).
_ENRICHMENT_NEWS_KEYS = {"news_results", "newsapi_results", "regulatory_results", "gdelt_results"}

# Articles sent to Gemini for scoring. Drives BOTH input and output size, since the
# prompt asks for one analysis object per indexed article. Lower = cheaper scan.
MAX_NEWS_ARTICLES = int(os.getenv("GEMINI_MAX_NEWS_ARTICLES", "25"))
# Per-scan ceiling. Above this the prompt is rebuilt without enrichment so that no
# single vendor can drain the daily budget.
MAX_PROMPT_TOKENS = int(os.getenv("GEMINI_MAX_PROMPT_TOKENS", "15000"))

_ADVERSE_TERMS = ("fraud", "scam", "penalt", "fine", "raid", "probe", "lawsuit", "sued",
                  "blacklist", "insolven", "recall", "adulterat", "pollut", "violation",
                  "arrest", "seiz", "notice", "default", "ban")

# Rough token accounting, used to size a call BEFORE spending it. A local estimate
# beats client.models.count_tokens() here — that would be an extra network round trip
# on every scan just to decide whether to make the real one.
_CHARS_PER_TOKEN = 4
# Static prompt scaffolding (source legend + task rules + JSON example) is ~10.2 KB
# and paid on every scan regardless of the data.
_SCAFFOLD_TOKENS = 2600


def _compact(obj, max_list: int = 4, max_str: int = 160):
    """Recursively cap list lengths, truncate long strings, and drop heavy keys.

    max_str dominates the payload size — search snippets are the bulk of it. 160 chars
    still carries the adverse signal (the headline and the first clause) while costing
    a third less than the full snippet.
    """
    if isinstance(obj, dict):
        return {
            k: _compact(v, max_list, max_str)
            for k, v in obj.items() if k not in _DROP_KEYS
        }
    if isinstance(obj, list):
        return [_compact(x, max_list, max_str) for x in obj[:max_list]]
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + "…"
    return obj


def _slim_enrichment(enrichment) -> dict:
    """Compact authbridge_enrichment, dropping the nested news already in the flat index."""
    if not isinstance(enrichment, dict):
        return _compact(enrichment)

    slim = {}
    for key, value in enrichment.items():
        if key != "by_alternate_name" or not isinstance(value, dict):
            slim[key] = _compact(value)
            continue
        slim[key] = {
            name: {
                k: _compact(v, max_list=3)
                for k, v in results.items() if k not in _ENRICHMENT_NEWS_KEYS
            } if isinstance(results, dict) else _compact(results, max_list=3)
            for name, results in value.items()
        }
    return slim


def _slim_data_for_llm(data: dict, include_enrichment: bool = True) -> dict:
    """Produce a compact copy of the aggregated data for the LLM prompt."""
    slim = {}
    for k, v in data.items():
        if k in _ALIAS_KEYS or k in _NEWS_KEYS_IN_FLAT:
            continue
        if k == "authbridge_enrichment":
            if not include_enrichment:
                continue
            slim[k] = _slim_enrichment(v)
        else:
            slim[k] = _compact(v)
    return slim


def _rank_news_for_llm(news_flat_list: list, limit: int) -> list:
    """Select the most analysis-worthy articles, adverse-signal headlines first.

    Each item keeps its ORIGINAL `index` — main.py assigns indices across the full
    list and maps Gemini's news_article_analysis back onto it by index, so
    re-indexing here would silently misattribute every score.
    """
    if limit <= 0 or len(news_flat_list) <= limit:
        return news_flat_list

    def adverse_score(item):
        title = (item.get("title") or "").lower()
        return sum(term in title for term in _ADVERSE_TERMS)

    ranked = sorted(news_flat_list, key=lambda i: (-adverse_score(i), i["index"]))
    return sorted(ranked[:limit], key=lambda i: i["index"])


# ── Heuristic (no-AI) section analysis ────────────────────────────────────────
# When Gemini is unavailable (quota exhausted / no key), we still want every scan
# to SHOW a summary sentence per section and to prove the category filtering ran —
# without spending a single token. These sentences are computed from the data by
# simple counting, not by an LLM, so criticality stays conservative (we can't judge
# sentiment) but relevance reflects how much data each source returned.

def _n(x) -> int:
    return len(x) if isinstance(x, list) else 0


def _organic(d) -> list:
    return (d or {}).get("organic", []) if isinstance(d, dict) else []


def _heuristic_section_analysis(data: dict) -> dict:
    """Build an AI-free section_analysis dict from raw aggregated data."""
    def sec(summary, relevance, criticality):
        return {"summary": summary, "relevance": int(relevance), "criticality": int(criticality)}

    # Corporate registry
    companies = (data.get("opencorporates") or {}).get("companies") or []
    corp = sec(
        f"{len(companies)} corporate registry record(s) found." if companies
        else "No corporate registry records returned.",
        70 if companies else 30, 10)

    # Sanctions
    sanc_hits = sum(
        1 for v in (data.get("opensanctions") or {}).values()
        if isinstance(v, dict) for r in v.get("results", []) if r.get("caption")
    )
    sanctions = sec(
        f"{sanc_hits} possible watchlist match(es) — review required." if sanc_hits
        else "No sanctions or watchlist matches found.",
        90 if sanc_hits else 60, 70 if sanc_hits else 5)

    # Domain / SSL
    whois = data.get("whois") or {}
    ssl = data.get("ssl") or {}
    has_domain = bool(whois and "error" not in whois) or bool(ssl and "error" not in ssl)
    domain_ssl = sec(
        "Domain WHOIS/SSL data retrieved." if has_domain else "No domain provided or domain data unavailable.",
        55 if has_domain else 20, 8)

    # Physical address
    places = (data.get("google_places") or {}).get("results") or []
    physical = sec(
        f"{len(places)} location record(s) found." if places else "No physical location data found.",
        50 if places else 20, 10)

    # Wikipedia
    wiki = data.get("wikipedia") or {}
    wikipedia = sec(
        "Public Wikipedia presence found." if wiki.get("found") else "No Wikipedia presence found.",
        40 if wiki.get("found") else 15, 5)

    # News / media
    gdelt_n = sum(_n(v.get("results")) for v in (data.get("gdelt") or {}).values() if isinstance(v, dict))
    news_n = gdelt_n + _n((data.get("newsapi") or {}).get("articles")) + _n(_organic(data.get("serper_news")))
    news = sec(
        f"{news_n} news/media item(s) collected across sources." if news_n
        else "No news or media coverage found.",
        min(85, 40 + news_n * 3) if news_n else 30, 15)

    # Reviews
    rev_n = _n(_organic(data.get("serper_reviews")))
    reviews = sec(
        f"{rev_n} review-site result(s) found." if rev_n else "No customer/employee review data found.",
        60 if rev_n else 30, 12)

    # Company profile
    prof_n = _n(_organic(data.get("serper_profile")))
    profile = sec(
        f"{prof_n} company-profile result(s) found." if prof_n else "No company profile data found.",
        55 if prof_n else 30, 8)

    # Adverse web — highlights the category filtering
    bucket = data.get("category_bucket") or "SERVICE_GENERAL"
    generic_n = _n(_organic(data.get("serper")))
    cat_n = _n(_organic(data.get("serper_category")))
    portal_hits = sum(_n(p.get("organic")) for p in (data.get("serper_portals") or []))
    adverse = sec(
        f"Category-tuned search ({bucket}): {generic_n} generic + {cat_n} category-specific "
        f"adverse result(s); {portal_hits} regulator-portal hit(s).",
        min(90, 50 + cat_n * 3 + portal_hits * 5),
        min(80, 15 + portal_hits * 15))

    return {
        "corporate_registry": corp,
        "sanctions_watchlists": sanctions,
        "domain_ssl": domain_ssl,
        "physical_address": physical,
        "wikipedia": wikipedia,
        "news_media": news,
        "reviews": reviews,
        "company_profile": profile,
        "adverse_web": adverse,
        "_heuristic": True,
    }


async def extract_findings_from_data(
    aggregated_data: dict, news_flat_list: list, category: str | None = None
) -> tuple[list, int, dict, list]:
    """
    Send aggregated API data to Gemini and extract adverse findings, section-level analysis,
    and per-article news analysis.
    Returns: (findings, tokens_used, section_analysis, news_article_analysis)
    """

    if MOCK_MODE or not client:
        logger.info("Using mock LLM response because MOCK_MODE/TEST_MODE is true or no API key is provided.")

        mock_article_analysis = [
            {"index": i, "summary": _CLEAN_ARTICLE_ANALYSIS[i % 2]["summary"],
             "relevance": _CLEAN_ARTICLE_ANALYSIS[i % 2]["relevance"],
             "criticality": _CLEAN_ARTICLE_ANALYSIS[i % 2]["criticality"]}
            for i in range(len(news_flat_list))
        ]

        scenarios = [
            # Scenario 1: Clean
            ([], _CLEAN_SECTION_ANALYSIS, mock_article_analysis),

            # Scenario 2: Critical Sanctions Match
            (
                [{
                    "finding_type": "sanctions_match",
                    "severity": "critical",
                    "title": "Mock: Possible Sanctions Match",
                    "description": "This is a mock finding. A potential match was found on an OFAC international watch list.",
                    "source_api": "opensanctions",
                    "confidence_score": 0.95
                }],
                {**_CLEAN_SECTION_ANALYSIS,
                 "sanctions_watchlists": {"summary": "A potential match was identified on an international sanctions watchlist — requires immediate escalation.", "relevance": 98, "criticality": 95},
                 "adverse_web": {"summary": "Adverse web search surfaced references consistent with the sanctions alert.", "relevance": 88, "criticality": 82}},
                mock_article_analysis,
            ),

            # Scenario 3: Medium Adverse Media
            (
                [{
                    "finding_type": "news_adverse",
                    "severity": "medium",
                    "title": "Mock: Adverse Media Coverage",
                    "description": "Mock finding: Recent news articles indicate possible involvement in a minor regulatory dispute.",
                    "source_api": "gdelt",
                    "confidence_score": 0.65
                }],
                {**_CLEAN_SECTION_ANALYSIS,
                 "news_media": {"summary": "News coverage contains references to a regulatory dispute; risk is limited but warrants monitoring.", "relevance": 82, "criticality": 58},
                 "adverse_web": {"summary": "Some web results corroborate adverse media coverage; no fraud allegations found.", "relevance": 78, "criticality": 45}},
                [
                    {"index": 0, "summary": "Article mentions a minor regulatory dispute involving the entity; details remain unverified.", "relevance": 78, "criticality": 60},
                    *[{"index": i, "summary": "General industry coverage; no adverse signals.", "relevance": 40, "criticality": 8}
                      for i in range(1, len(news_flat_list))],
                ],
            ),

            # Scenario 4: High Fraud + Domain Risk
            (
                [
                    {"finding_type": "news_adverse", "severity": "high", "title": "Mock: Fraud Allegations",
                     "description": "Mock finding: Multiple search results allege fraudulent business practices and scams.",
                     "source_api": "serper", "confidence_score": 0.88},
                    {"finding_type": "domain_risk", "severity": "medium", "title": "Mock: Suspicious Domain",
                     "description": "Mock finding: Website was registered very recently and lacks standard metadata.",
                     "source_api": "microlink", "confidence_score": 0.70},
                ],
                {**_CLEAN_SECTION_ANALYSIS,
                 "news_media": {"summary": "Multiple sources allege fraudulent practices; adverse coverage is extensive and consistent across outlets.", "relevance": 95, "criticality": 88},
                 "adverse_web": {"summary": "Fraud and scam allegations dominate web search results for this entity.", "relevance": 97, "criticality": 92},
                 "domain_ssl": {"summary": "Domain appears recently registered with minimal metadata, consistent with newly established or shell entities.", "relevance": 72, "criticality": 68},
                 "reviews": {"summary": "Review sites surface patterns of non-payment and product quality complaints.", "relevance": 80, "criticality": 74}},
                [
                    {"index": 0, "summary": "Article directly references fraud allegations involving the entity — high-risk signal.", "relevance": 95, "criticality": 90},
                    *[{"index": i, "summary": "Corroborating coverage; fraud narrative is consistent across sources.", "relevance": 85, "criticality": 78}
                      for i in range(1, len(news_flat_list))],
                ],
            ),
        ]

        findings, section_analysis, article_analysis = random.choice(scenarios)
        return findings, 1500, section_analysis, article_analysis

    def _news_block(items: list) -> str:
        if not items:
            return ""
        lines = [f"  [{item['index']}] [{item['source']}] {item['title']} — {item['url']}" for item in items]
        return "\n## Flattened News Article Index (for news_article_analysis):\n" + "\n".join(lines)

    # Only the top-ranked articles are scored by the LLM; the rest still reach the
    # report, just without an AI relevance score.
    news_for_llm = _rank_news_for_llm(news_flat_list, MAX_NEWS_ARTICLES)
    news_index_block = _news_block(news_for_llm)
    # Compact the payload before serialising — this is the primary token saver.
    data_block = json.dumps(_slim_data_for_llm(aggregated_data), separators=(",", ":"))

    # Per-scan ceiling: if this vendor is still oversized (many alternate names or
    # directors), drop the enrichment graph and halve the news rather than let one
    # scan eat the whole day's budget.
    est_input = (len(data_block) + len(news_index_block)) // _CHARS_PER_TOKEN + _SCAFFOLD_TOKENS
    if est_input > MAX_PROMPT_TOKENS:
        logger.warning("Prompt ~%d tokens exceeds GEMINI_MAX_PROMPT_TOKENS=%d — dropping enrichment "
                       "and halving news", est_input, MAX_PROMPT_TOKENS)
        news_for_llm = _rank_news_for_llm(news_flat_list, max(5, MAX_NEWS_ARTICLES // 2))
        news_index_block = _news_block(news_for_llm)
        data_block = json.dumps(_slim_data_for_llm(aggregated_data, include_enrichment=False),
                                separators=(",", ":"))

    logger.info("Gemini payload: %d news articles of %d, data %d chars, news %d chars",
                len(news_for_llm), len(news_flat_list), len(data_block), len(news_index_block))

    category_block = ""
    if category:
        category_block = f"""
## Vendor Business Category: {category}
This vendor operates in the "{category}" sector. Use this to keep the analysis focused:
- Prioritise sources, reviews, and articles that plausibly concern a company in this sector.
- AGGRESSIVELY discard name-collision noise: search results, news, or sanctions/registry
  hits that clearly belong to a DIFFERENT industry or an unrelated same-named entity are NOT
  about this vendor. Give such articles relevance < 20 in news_article_analysis and do NOT
  raise findings from them.
- Only surface findings supported by evidence that genuinely relates to a "{category}" business.
"""

    prompt = f"""You are a KYB (Know Your Business) due diligence analyst.
Analyze the provided data and return a structured JSON object with three keys: findings, section_analysis, and news_article_analysis.
{category_block}

## Data Sources in this payload:
- opencorporates: Company registry lookup
- opensanctions: Sanctions / PEP screening on legal name + all directors
- gdelt: Global news search (company + CEO/founder + directors)
- serper: Adverse web search — universal risk terms (fraud/penalty/blacklisted/raid/insolvency)
- serper_category: Adverse web search — CATEGORY-SPECIFIC risk terms for this vendor's compliance
    bucket (e.g. recall/adulteration for food, explosion/gas leak for chemicals, pollution/NGT for
    packaging). Adverse hits here are HIGH signal — they directly match the vendor's real risk profile.
- serper_portals: Site-restricted searches of official government regulator portals (FSSAI, CPCB,
    NGT, PESO, BIS). Each item = {{domain, keyword, organic:[...]}}. Any genuine hit naming this vendor
    is an OFFICIAL regulatory action → treat as HIGH or CRITICAL.
- category_bucket: The resolved compliance bucket (FOOD_INGREDIENT | FOOD_PACKAGING | GAS_CHEMICAL |
    CAPEX_COOLER | SERVICE_GENERAL). Focus the analysis on risks relevant to this bucket.
- serper_reviews: Review sites — Trustpilot, Glassdoor, G2, AmbitionBox
- serper_profile: Company overview — founding, HQ, employees
- serper_news: Latest general news
- newsapi: Adverse media (fraud/scandal/lawsuit)
- newsapi_regulatory: Regulatory angle (fines, SEBI/SEC, compliance)
- wikipedia: Company Wikipedia summary
- whois / ssl / microlink: Domain intelligence
- google_places: Physical address / business status
- authbridge_tsp / sandbox_tsp: AuthBridge live verification results — contains the sub-keys below:
    .gstin: GSTIN status (Active/Cancelled/Suspended), taxpayer name, registration date (India)
    .pan: PAN validity, name on record (India)
    .msmed: MSME/Udyam status, enterprise type, district (India)
    .email_verification: corporate email domain validity, deliverability, disposable-domain flag, MX records, risk level
    .court_check: dict keyed by entity/director name → court case records from Indian courts
    .defaulting_director: dict keyed by director name → MCA defaulter/disqualification status
    .global_sanctions: dict keyed by entity/director name → AuthBridge global sanctions matches
- authbridge_intel / sandbox_intel: Entities extracted from GSTIN/PAN/MSMED — alternate trade names, registered address, business type, industry
- authbridge_enrichment.by_alternate_name[NAME]: For each alternate/registered name recovered from GSTIN/PAN/MSMED, the search graph re-run — serper_results (adverse), reviews_results, profile_results, sanctions_results, wikipedia, opencorporates. Treat adverse hits here as HIGH signal. (News found under alternate names is folded into the Flattened News Article Index above, not repeated here.)
- authbridge_enrichment.gstin_address_places: Google Places result using the GSTIN-verified registered address
{news_index_block}

## Aggregated Data (compacted — long fields truncated, lists capped):
{data_block}

## Task:
Return a single JSON object with exactly these three keys:

### 1. "findings" — array of adverse findings
For EACH adverse finding include:
- finding_type: (sanctions_match | news_adverse | regulatory_issue | pep_match | domain_risk | address_risk | review_risk | name_mismatch | other)
- severity: (critical | high | medium | low)
- title: concise headline (max 80 chars) that names the specific risk
- description: detailed 3–5 sentence explanation. Quote specific field values from the data: exact entity names, article headlines, court case counts, sanction list names, dates, GSTIN status values, confidence scores. State WHAT was found, in WHICH data source, and WHY it constitutes a risk signal.
- source_api: the key from the data above that contains the primary evidence
- source_url: the single most direct URL from the raw data supporting this finding (from an article, OpenSanctions entity page, OpenCorporates record, etc.). Use empty string if none available.
- confidence_score: 0.0 to 1.0

### 2. "section_analysis" — dict with one entry per section below
For each section provide:
- summary: 1–2 sentences citing specific evidence values found in the data. Name actual field values: registration date, domain age, article count, rating score, specific sanction list, court case count, GSTIN status. Be factual and precise, not generic. Max 250 chars.
- relevance: integer 0–100 — how significant/informative this data source is for the risk assessment
- criticality: integer 0–100 — how concerning/risky the content is (0 = clean/positive, 100 = severe red flag)

Sections to analyse:
- corporate_registry (opencorporates data)
- sanctions_watchlists (opensanctions data)
- domain_ssl (whois + ssl + microlink data)
- physical_address (google_places data)
- wikipedia (wikipedia data)
- news_media (gdelt + newsapi + newsapi_regulatory + serper_news combined)
- reviews (serper_reviews data)
- company_profile (serper_profile data)
- adverse_web (serper adverse search data)

### 3. "news_article_analysis" — array with one entry per article in the Flattened News Article Index above
For each article (referenced by its [index]):
- index: integer matching the index in the list above
- summary: single sentence describing the article's relevance to this vendor's risk profile (max 100 chars)
- relevance: integer 0–100 — how relevant this specific article is to the risk assessment
- criticality: integer 0–100 — how alarming the content is for this vendor

## Analysis Rules:

**Regulatory / Compliance (regulatory_issue):**
- authbridge_tsp.gstin: status 'Cancelled' or 'Suspended' or valid=false → HIGH risk
- authbridge_tsp.pan: Inactive or name mismatch → MEDIUM–HIGH risk
- authbridge_tsp.msmed: invalid → MEDIUM risk
- authbridge_tsp.email_verification.disposable=true or risk='high' → MEDIUM risk (use of personal/disposable email domain suggests non-corporate entity)
- newsapi_regulatory: Penalty, SEBI/SEC action, compliance violation → MEDIUM–HIGH risk

**Adverse Media (news_adverse):**
- newsapi or gdelt: fraud, lawsuits, or scandals → HIGH or CRITICAL risk
- serper_news: Recent shutdown, investigation, or negative development → MEDIUM–HIGH risk
- serper_category: category-specific adverse hit (recall, adulteration, explosion, pollution, etc.) → HIGH risk
- sandbox_enrichment.by_alternate_name[X].gdelt: adverse news under an alternate name → HIGH risk

**Category / Regulator Portals (regulatory_issue):**
- serper_portals[X].organic: an official FSSAI/CPCB/NGT/PESO/BIS result naming this vendor
  (recall, closure notice, accident, direction, violation) → HIGH or CRITICAL risk.
  Ignore generic portal pages that do NOT name the vendor.

**Sanctions / PEP (sanctions_match / pep_match):**
- opensanctions: Any match on legal name or director → CRITICAL risk
- authbridge_tsp.global_sanctions[X].is_sanctioned=true: AuthBridge global sanctions hit → CRITICAL risk
- authbridge_enrichment.by_alternate_name[X].sanctions: Sanctions match on a trade name → CRITICAL risk

**Court Records (regulatory_issue or news_adverse):**
- authbridge_tsp.court_check[X].cases_found > 0: Active litigation found for entity or director → HIGH risk
- authbridge_tsp.court_check[X].cases_found > 2: Multiple court cases → CRITICAL risk

**Defaulting Director (regulatory_issue):**
- authbridge_tsp.defaulting_director[X].is_defaulter=true: Director listed as MCA defaulter → HIGH–CRITICAL risk

**Name Mismatch (name_mismatch):**
- sandbox_intel.additional_names contains names not matching submitted legal_name → MEDIUM risk if ≥2 different names

**Customer / Reputational Risk (review_risk):**
- serper_reviews: Consistently 1–2 star ratings or widespread fraud/non-payment complaints → MEDIUM–HIGH risk

**Address / Physical Presence (address_risk):**
- google_places or sandbox_enrichment.gstin_address_places: Business permanently closed → HIGH risk

**Domain / Web (domain_risk):**
- microlink: Unreachable or newly registered domain → MEDIUM risk
- wikipedia: Company defunct, dissolved, or linked to known fraud → HIGH risk

## Output format:
Return ONLY a valid JSON object. No preamble, no markdown fences. Example structure:
{{
  "findings": [
    {{"finding_type": "sanctions_match", "severity": "critical", "title": "...", "description": "...", "source_api": "opensanctions", "source_url": "https://www.opensanctions.org/entities/...", "confidence_score": 0.95}}
  ],
  "section_analysis": {{
    "corporate_registry": {{"summary": "Active registration with no anomalies.", "relevance": 80, "criticality": 10}},
    "sanctions_watchlists": {{"summary": "No watchlist matches detected.", "relevance": 90, "criticality": 5}},
    "domain_ssl": {{"summary": "Valid SSL; domain registered in 2019.", "relevance": 60, "criticality": 8}},
    "physical_address": {{"summary": "Operational business address verified.", "relevance": 55, "criticality": 10}},
    "wikipedia": {{"summary": "Entity has an established Wikipedia page.", "relevance": 40, "criticality": 5}},
    "news_media": {{"summary": "No adverse media found.", "relevance": 70, "criticality": 8}},
    "reviews": {{"summary": "Mixed reviews; no systemic fraud pattern.", "relevance": 65, "criticality": 20}},
    "company_profile": {{"summary": "Profile data is consistent across sources.", "relevance": 60, "criticality": 8}},
    "adverse_web": {{"summary": "No fraud allegations in web results.", "relevance": 75, "criticality": 5}}
  }},
  "news_article_analysis": [
    {{"index": 0, "summary": "Routine supply chain article; no adverse signals.", "relevance": 40, "criticality": 8}},
    {{"index": 1, "summary": "Regulatory update article; vendor not directly implicated.", "relevance": 50, "criticality": 12}}
  ]
}}

If NO adverse findings, set "findings" to [].
If no news articles were provided, set "news_article_analysis" to []."""

    # Size the output ceiling to what the prompt actually asks for. Per its own limits:
    #   9 sections x 250-char summary   ~=  700 tokens
    #   N articles x 100-char summary   ~=   45 tokens each
    #   findings (unbounded count)      ~= 1000 tokens of headroom
    # The old formula (1024 + 40/article) came in ~900 tokens short of that and
    # truncated the JSON mid-string, burning the whole call for nothing.
    # max_tokens is a CEILING, not a charge — unused headroom costs nothing.
    max_out = min(8192, 3072 + 100 * len(news_for_llm))
    est_tokens = len(prompt) // _CHARS_PER_TOKEN + max_out

    # Free-tier budget guard: reserve the estimated cost up front, so one oversized
    # scan can't overshoot the daily cap. Under budget → zero-token heuristic summaries.
    if not gemini_budget.can_afford(est_tokens):
        logger.warning("Gemini call (~%d tokens) would exceed the daily budget (%s) — using heuristic summaries",
                       est_tokens, gemini_budget.status())
        return [], 0, _heuristic_section_analysis(aggregated_data), []

    try:
        logger.info("Calling %s (%s): prompt %d chars, ~%d est tokens (max_out=%d), budget=%s",
                    PROVIDER, LLM_MODEL, len(prompt), est_tokens, max_out, gemini_budget.status())
        gemini_budget.reserve(est_tokens)

        response_text, tokens_used = await _call_llm(prompt, max_out)
        logger.info(f"LLM raw response (first 500 chars): {response_text[:500]}")

        # Strip markdown fences if present
        if response_text.strip().startswith("```"):
            response_text = response_text.strip()
            response_text = response_text[response_text.index("\n") + 1:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

        response_json = json.loads(response_text)

        findings = []
        for f in response_json.get("findings", []):
            findings.append({
                "finding_type":   f.get("finding_type"),
                "severity":       f.get("severity", "low").lower(),
                "title":          f.get("title"),
                "description":    f.get("description"),
                "source_api":     f.get("source_api"),
                "source_url":     f.get("source_url", ""),
                "confidence_score": float(f.get("confidence_score", 0.0))
            })

        section_analysis = response_json.get("section_analysis", {})
        news_article_analysis = response_json.get("news_article_analysis", [])

        gemini_budget.reconcile(est_tokens, tokens_used)
        logger.info(f"Extracted {len(findings)} findings, {len(news_article_analysis)} article scores using {tokens_used} tokens (est {est_tokens}, budget={gemini_budget.status()})")

        return findings, tokens_used, section_analysis, news_article_analysis

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e} — falling back to heuristic summaries")
        return [], 0, _heuristic_section_analysis(aggregated_data), []
    except Exception as e:
        logger.error(f"LLM API error ({PROVIDER}): {type(e).__name__}: {e} — falling back to heuristic summaries")
        return [], 0, _heuristic_section_analysis(aggregated_data), []
