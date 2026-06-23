from anthropic import AsyncAnthropic
import json
import os
import logging
import random

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true" or os.getenv("TEST_MODE", "false").lower() == "true"
api_key = os.getenv("ANTHROPIC_API_KEY")
client = AsyncAnthropic(api_key=api_key) if api_key else None

async def extract_findings_from_data(aggregated_data: dict) -> tuple[list, int]:
    """
    Send aggregated API data to Claude and extract adverse findings.
    Returns tuple: (list of Finding dictionaries, total_tokens_used)
    """
    
    if MOCK_MODE or not client:
        logger.info("Using mock LLM response because MOCK_MODE/TEST_MODE is true or no API key is provided.")
        
        # Define variable scenarios
        scenarios = [
            # Scenario 1: Clean
            [],
            # Scenario 2: Critical Sanctions Match
            [
                {
                    "finding_type": "sanctions_match",
                    "severity": "critical",
                    "title": "Mock: Possible Sanctions Match",
                    "description": "This is a mock finding. A potential match was found on an OFAC international watch list.",
                    "source_api": "opensanctions",
                    "confidence_score": 0.95
                }
            ],
            # Scenario 3: Medium Adverse Media
            [
                {
                    "finding_type": "news_adverse",
                    "severity": "medium",
                    "title": "Mock: Adverse Media Coverage",
                    "description": "Mock finding: Recent news articles indicate possible involvement in a minor regulatory dispute.",
                    "source_api": "gdelt",
                    "confidence_score": 0.65
                }
            ],
            # Scenario 4: High Fraud Risk + Domain Risk
            [
                {
                    "finding_type": "news_adverse",
                    "severity": "high",
                    "title": "Mock: Fraud Allegations",
                    "description": "Mock finding: Multiple search results allege fraudulent business practices and scams.",
                    "source_api": "serper",
                    "confidence_score": 0.88
                },
                {
                    "finding_type": "domain_risk",
                    "severity": "medium",
                    "title": "Mock: Suspicious Domain",
                    "description": "Mock finding: Website was registered very recently and lacks standard metadata.",
                    "source_api": "microlink",
                    "confidence_score": 0.70
                }
            ]
        ]
        
        selected_scenario = random.choice(scenarios)
        return selected_scenario, 1500  # Return mock findings and 1500 mock tokens
    
    # Build the prompt
    prompt = f"""You are a KYB (Know Your Business) due diligence analyst.
Analyze the provided data and extract ONLY adverse findings (negative information that increases risk).

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
- sandbox_tsp: India-specific — GSTIN / PAN / MSMED live verification
- sandbox_intel: Entities extracted from Sandbox — alternate trade names, registered address, business type, industry
- sandbox_enrichment.by_alternate_name[NAME]: For each alternate name found in GSTIN/PAN/MSMED, results from serper + gdelt + sanctions — treat this as high-signal since it covers operating names the vendor may not have disclosed
- sandbox_enrichment.gstin_address_places: Google Places result using the GSTIN-verified registered address

## Data Provided:
{json.dumps(aggregated_data, indent=2)}

## Task:
For EACH adverse finding, output a JSON object with:
- finding_type: (sanctions_match | news_adverse | regulatory_issue | pep_match | domain_risk | address_risk | review_risk | name_mismatch | other)
- severity: (critical | high | medium | low)
- title: short summary
- description: detailed explanation citing specific source fields and values
- source_api: the key from the data above that contains the evidence
- confidence_score: 0.0 to 1.0

## Analysis Rules:

**Regulatory / Compliance (regulatory_issue):**
- sandbox_tsp.gstin: status 'Cancelled' or 'Suspended' or valid=false → HIGH risk
- sandbox_tsp.pan: Inactive or name mismatch → MEDIUM–HIGH risk
- sandbox_tsp.msmed: invalid → MEDIUM risk
- newsapi_regulatory: Penalty, SEBI/SEC action, compliance violation → MEDIUM–HIGH risk

**Adverse Media (news_adverse):**
- newsapi or gdelt: fraud, lawsuits, or scandals → HIGH or CRITICAL risk
- serper_news: Recent shutdown, investigation, or negative development → MEDIUM–HIGH risk
- sandbox_enrichment.by_alternate_name[X].gdelt: adverse news under an alternate name → HIGH risk (harder to discover)
- sandbox_enrichment.by_alternate_name[X].serper: fraud/scam results for an alternate operating name → HIGH risk

**Sanctions / PEP (sanctions_match / pep_match):**
- opensanctions: Any match on legal name or director → CRITICAL risk
- sandbox_enrichment.by_alternate_name[X].sanctions: Sanctions match on a trade name not provided by the vendor → CRITICAL risk

**Name Mismatch (name_mismatch):**
- sandbox_intel.additional_names contains names not matching the submitted legal_name → flag as MEDIUM risk if ≥2 different names appear, since the vendor may be operating under undisclosed identities

**Customer / Reputational Risk (review_risk):**
- serper_reviews: Consistently 1–2 star ratings or widespread fraud/non-payment complaints → MEDIUM–HIGH risk
- serper (adverse): Multiple fraud allegations in web results → HIGH risk

**Address / Physical Presence (address_risk):**
- google_places or sandbox_enrichment.gstin_address_places: Business permanently closed, doesn't exist, or address is a virtual office cluster → HIGH risk
- serper_profile: No verifiable web presence or contradictory founding information → MEDIUM risk

**Domain / Web (domain_risk):**
- microlink: Unreachable or newly registered domain → MEDIUM risk
- wikipedia: Company defunct, dissolved, or linked to known fraud → HIGH risk

## Output:
Return ONLY a valid JSON array. No preamble. Example:
[
  {{"finding_type": "sanctions_match", "severity": "critical", "title": "...", "description": "...", "source_api": "sandbox_enrichment", "confidence_score": 0.95}},
  {{"finding_type": "name_mismatch", "severity": "medium", "title": "...", "description": "...", "source_api": "sandbox_intel", "confidence_score": 0.75}},
  {{"finding_type": "review_risk", "severity": "medium", "title": "...", "description": "...", "source_api": "serper_reviews", "confidence_score": 0.70}}
]

If NO adverse findings, return: []"""

    try:
        logger.info("Calling Claude for adverse findings extraction...")
        
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Parse response
        response_text = message.content[0].text
        logger.info(f"Claude raw response: {response_text}")
        
        # Clean response if LLM added markdown ticks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        # Extract JSON from response
        findings_data = json.loads(response_text)
        
        # Convert to finding dicts
        findings = []
        for f in findings_data:
            findings.append({
                "finding_type": f.get("finding_type"),
                "severity": f.get("severity", "low").lower(),
                "title": f.get("title"),
                "description": f.get("description"),
                "source_api": f.get("source_api"),
                "confidence_score": float(f.get("confidence_score", 0.0))
            })
        
        
        # Calculate tokens used
        tokens_used = message.usage.input_tokens + message.usage.output_tokens
        
        logger.info(f"Extracted {len(findings)} findings using {tokens_used} tokens")
        return findings, tokens_used
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        return [], 0
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return [], 0
