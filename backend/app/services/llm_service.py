from google import genai
import json
import os
import logging
import random

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true" or os.getenv("TEST_MODE", "false").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None

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


def _compact(obj, max_list: int = 5, max_str: int = 240):
    """Recursively cap list lengths, truncate long strings, and drop heavy keys."""
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


def _slim_data_for_llm(data: dict) -> dict:
    """Produce a compact copy of the aggregated data for the LLM prompt."""
    return {
        k: _compact(v)
        for k, v in data.items()
        if k not in _ALIAS_KEYS and k not in _NEWS_KEYS_IN_FLAT
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

    # Build the prompt
    news_index_block = ""
    if news_flat_list:
        lines = [f"  [{item['index']}] [{item['source']}] {item['title']} — {item['url']}" for item in news_flat_list]
        news_index_block = "\n## Flattened News Article Index (for news_article_analysis):\n" + "\n".join(lines)

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

    # Compact the payload before serialising — this is the primary token saver.
    slim_data = _slim_data_for_llm(aggregated_data)

    prompt = f"""You are a KYB (Know Your Business) due diligence analyst.
Analyze the provided data and return a structured JSON object with three keys: findings, section_analysis, and news_article_analysis.
{category_block}

## Data Sources in this payload:
- opencorporates: Company registry lookup
- opensanctions: Sanctions / PEP screening on legal name + all directors
- gdelt: Global news search (company + CEO/founder + directors)
- serper: Adverse web search (fraud/scam)
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
- authbridge_enrichment.by_alternate_name[NAME] / sandbox_enrichment.by_alternate_name[NAME]: For each alternate/registered name recovered from GSTIN/PAN/MSMED, the FULL search graph re-run — serper_results (adverse), reviews_results, profile_results, news_results, newsapi_results (adverse media), regulatory_results (regulatory/penalty news), gdelt_results, sanctions_results, wikipedia, opencorporates. Treat adverse hits here as HIGH signal.
- authbridge_enrichment.gstin_address_places: Google Places result using the GSTIN-verified registered address
{news_index_block}

## Aggregated Data (compacted — long fields truncated, lists capped):
{json.dumps(slim_data, separators=(",", ":"))}

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
- sandbox_enrichment.by_alternate_name[X].gdelt: adverse news under an alternate name → HIGH risk

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

    try:
        logger.info(f"Calling Gemini ({GEMINI_MODEL}) for findings + section analysis + article analysis...")

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )
        response_text = response.text
        logger.info(f"Gemini raw response (first 500 chars): {response_text[:500]}")

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

        tokens_used = response.usage_metadata.total_token_count if response.usage_metadata else 0
        logger.info(f"Extracted {len(findings)} findings, {len(news_article_analysis)} article scores using {tokens_used} tokens")

        return findings, tokens_used, section_analysis, news_article_analysis

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        return [], 0, {"_ai_unavailable": True}, []
    except Exception as e:
        logger.error(f"Gemini API error: {type(e).__name__}: {e}")
        return [], 0, {"_ai_unavailable": True}, []
