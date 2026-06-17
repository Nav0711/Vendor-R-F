import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)
MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true"

class OpenCorporatesAPI:
    def __init__(self):
        self.api_key = os.getenv("OPENCORPORATES_API_KEY")
        self.base_url = "https://api.opencorporates.com/v0.4"
    
    async def search_company(self, name: str, jurisdiction: str = "us") -> dict:
        """Search for company by name."""
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/companies/search",
                    params={
                        "q": name,
                        "jurisdiction": jurisdiction,
                        "api_token": self.api_key
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"OpenCorporates error: {e}")
            return {"error": str(e)}

class OpenSanctionsAPI:
    def __init__(self):
        self.api_key = os.getenv("OPENSANCTIONS_API_KEY")
        self.base_url = "https://api.opensanctions.org/v2"
    
    async def search_entity(self, name: str) -> dict:
        """Search for sanctions/PEP matches."""
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": name},
                    headers={"Authorization": f"ApiKey {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"OpenSanctions error: {e}")
            return {"error": str(e)}

class GDELTNewsAPI:
    """Free global news API."""
    async def search_news(self, company_name: str) -> dict:
        """Search GDELT for recent adverse news."""
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        
        try:
            # GDELT has free API at: api.gdeltproject.org
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.gdeltproject.org/api/v2/search/web",
                    params={
                        "query": f'"{company_name}" (fraud OR bankruptcy OR scandal OR lawsuit)',
                        "format": "json",
                        "maxrecords": 10,
                        "sort": "DateDesc"
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"GDELT error: {e}")
            return {"error": str(e)}

# Initialize API clients
opencorp = OpenCorporatesAPI()
opensanctions = OpenSanctionsAPI()
gdelt = GDELTNewsAPI()
