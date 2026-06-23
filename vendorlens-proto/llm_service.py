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
We have gathered data from: OpenCorporates, OpenSanctions, GDELT (News), WHOIS, SSL APIs, Serper (adverse search, reviews, profile, latest news), NewsAPI (adverse + regulatory angles), Google Places, Microlink, and Wikipedia.

## Data Provided:
{json.dumps(aggregated_data, indent=2)}

## Task:
For EACH adverse finding, output a JSON object with:
- finding_type: (sanctions_match | news_adverse | regulatory_issue | pep_match | domain_risk | address_risk | review_risk | other)
- severity: (critical | high | medium | low)
- title: short summary
- description: detailed explanation citing the specific source data
- source_api: (opensanctions | gdelt | opencorporates | whois | ssl | sandbox_tsp | serper | serper_reviews | serper_profile | serper_news | newsapi | newsapi_regulatory | google_places | microlink | wikipedia)
- confidence_score: 0.0 to 1.0

## Analysis Rules:
**Regulatory / Compliance (regulatory_issue):**
- Sandbox TSP: GSTIN 'Cancelled' or 'Suspended' or valid=false → HIGH risk.
- Sandbox TSP: PAN Inactive or name mismatch → MEDIUM or HIGH risk.
- Sandbox TSP: MSMED invalid → MEDIUM risk.
- newsapi_regulatory: Penalty, SEBI/SEC action, compliance violation → MEDIUM–HIGH risk.

**Adverse Media (news_adverse):**
- NewsAPI or GDELT: fraud, lawsuits, or scandals → HIGH or CRITICAL risk.
- serper_news: Recent negative news (layoffs, shutdowns, investigations) → MEDIUM–HIGH risk.

**Customer / Reputational Risk (review_risk):**
- serper_reviews: Consistently poor ratings (1–2 stars) on Trustpilot, Glassdoor, G2, or AmbitionBox → MEDIUM risk.
- serper_reviews: Widespread fraud, scam, or non-payment complaints from customers/employees → HIGH risk.
- serper (adverse): Multiple fraud allegations or scam accusations in web results → HIGH risk.

**Company Profile Anomalies (other / address_risk):**
- serper_profile: Company claims large scale but has no verifiable web presence, no employees listed, or contradictory founding dates → MEDIUM risk.
- Wikipedia: Company described as defunct, acquired (and dissolved), or associated with known fraud → HIGH risk.

**Domain / Web Presence (domain_risk):**
- Microlink: Website unreachable or newly registered → MEDIUM risk.
- Google Places: Business permanently closed or address matches a known shell company cluster → HIGH risk (address_risk).

## Output:
Return ONLY a valid JSON array. No preamble. Example:
[
  {{"finding_type": "news_adverse", "severity": "high", "title": "...", "description": "...", "source_api": "newsapi", "confidence_score": 0.85}},
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
