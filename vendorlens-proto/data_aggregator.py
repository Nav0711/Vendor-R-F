from apis import opencorp, opensanctions, gdelt
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def aggregate_vendor_data(
    legal_name: str,
    registration_number: Optional[str],
    website_url: Optional[str],
    directors: list[str],
    ubo: list[str]
) -> dict:
    """
    Call all 3 APIs sequentially and aggregate results.
    For prototype, we don't parallelize to keep it simple.
    """
    
    aggregated = {
        "opencorporates": {},
        "opensanctions": {},
        "gdelt": {}
    }
    
    try:
        # 1. OpenCorporates: Search for company
        logger.info(f"Searching OpenCorporates for {legal_name}...")
        aggregated["opencorporates"] = await opencorp.search_company(legal_name)
    except Exception as e:
        logger.error(f"OpenCorporates Aggregation failed: {e}")
        aggregated["opencorporates"] = {"error": str(e)}

    try:
        # 2. OpenSanctions: Check entity + directors + UBO
        logger.info(f"Searching OpenSanctions for {legal_name} and officers...")
        all_names = [legal_name] + directors + ubo
        aggregated["opensanctions"] = await opensanctions.search_entity(legal_name)
    except Exception as e:
        logger.error(f"OpenSanctions Aggregation failed: {e}")
        aggregated["opensanctions"] = {"error": str(e)}

    try:
        # 3. GDELT: Search for adverse news
        logger.info(f"Searching GDELT for news about {legal_name}...")
        aggregated["gdelt"] = await gdelt.search_news(legal_name)
    except Exception as e:
        logger.error(f"GDELT Aggregation failed: {e}")
        aggregated["gdelt"] = {"error": str(e)}
        
    return aggregated
