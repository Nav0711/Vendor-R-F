from anthropic import AsyncAnthropic
import json
import os
import logging

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true"
api_key = os.getenv("ANTHROPIC_API_KEY")
client = AsyncAnthropic(api_key=api_key) if api_key else None

async def extract_findings_from_data(aggregated_data: dict) -> list:
    """
    Send aggregated API data to Claude and extract adverse findings.
    Returns list of Finding dictionaries.
    """
    
    if MOCK_MODE or not client:
        logger.info("Using mock LLM response because MOCK_MODE is true or no API key is provided.")
        return [
            {
                "finding_type": "sanctions_match",
                "severity": "critical",
                "title": "Mock: Possible Sanctions Match",
                "description": "This is a mock finding. A potential match was found on an international watch list.",
                "source_api": "opensanctions",
                "confidence_score": 0.85
            },
            {
                "finding_type": "news_adverse",
                "severity": "medium",
                "title": "Mock: Adverse Media Coverage",
                "description": "Mock finding: Recent news articles indicate possible involvement in a regulatory dispute.",
                "source_api": "gdelt",
                "confidence_score": 0.60
            }
        ]
    
    # Build the prompt
    prompt = f"""You are a KYB (Know Your Business) due diligence analyst.
Analyze the provided data and extract ONLY adverse findings (negative information that increases risk).
We have gathered data from OpenCorporates, OpenSanctions, GDELT (News), WHOIS, and SSL APIs.

## Data Provided:
{json.dumps(aggregated_data, indent=2)}

## Task:
For EACH adverse finding, output a JSON object with:
- finding_type: (sanctions_match | news_adverse | regulatory_issue | pep_match | domain_risk | other)
- severity: (critical | high | medium | low)
- title: short summary
- description: detailed explanation
- source_api: (opensanctions | gdelt | opencorporates | whois | ssl | sandbox_tsp)
- confidence_score: 0.0 to 1.0

## Specific Rules for Sandbox TSP (Indian Data):
- If Sandbox TSP reports GSTIN status as 'Cancelled' or 'Suspended' or valid=false, flag as HIGH risk (regulatory_issue).
- If Sandbox TSP reports PAN is Inactive or name mismatch, flag as MEDIUM or HIGH risk (regulatory_issue).
- If Sandbox TSP reports MSMED is invalid, flag as MEDIUM risk.

## Output:
Return ONLY a valid JSON array. No preamble. Example:
[
  {{"finding_type": "news_adverse", "severity": "high", "title": "...", "description": "...", "source_api": "gdelt", "confidence_score": 0.85}},
  {{"finding_type": "sanctions_match", "severity": "critical", "title": "...", "description": "...", "source_api": "opensanctions", "confidence_score": 0.92}}
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
        
        logger.info(f"Extracted {len(findings)} findings")
        return findings
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return []
