import httpx
import os
import logging
import whois
import ssl
import socket
from datetime import datetime
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
                if response.status_code == 401 or response.status_code == 403:
                    # If unauthorized or forbidden due to invalid key, return a mocked response 
                    # so the prototype can still function for demonstration
                    return {"mocked_due_to_auth_error": True, "error": f"API Key Issue ({response.status_code})"}
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
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"ApiKey {self.api_key}"
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": name, "fuzzy": "true"},
                    headers=headers
                )
                if response.status_code == 401 or response.status_code == 403:
                    return {"mocked_due_to_auth_error": True, "error": f"API Key Issue ({response.status_code})"}
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

class WHOISAPI:
    """Uses python-whois to get domain registration data locally for free."""
    async def search_domain(self, domain: str) -> dict:
        if not domain:
            return {"error": "No domain provided"}
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        
        try:
            domain_info = whois.whois(domain)
            
            # whois returns a dict-like object but dates can be lists or single items
            def get_first_date(d):
                if isinstance(d, list):
                    return d[0].isoformat() if d and hasattr(d[0], 'isoformat') else str(d[0])
                if hasattr(d, 'isoformat'):
                    return d.isoformat()
                return str(d)

            creation_date = get_first_date(domain_info.creation_date) if domain_info.creation_date else None
            expiration_date = get_first_date(domain_info.expiration_date) if domain_info.expiration_date else None
            
            return {
                "domain_name": domain_info.domain_name,
                "registrar": domain_info.registrar,
                "creation_date": creation_date,
                "expiration_date": expiration_date,
                "emails": domain_info.emails,
                "status": domain_info.status
            }
        except Exception as e:
            logger.error(f"WHOIS error: {e}")
            return {"error": str(e)}

class SSLCheckAPI:
    """Checks SSL certificate validity using Python's ssl module."""
    async def check_ssl(self, domain: str) -> dict:
        if not domain:
            return {"error": "No domain provided"}
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    not_before = cert.get('notBefore')
                    not_after = cert.get('notAfter')
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    
                    # Convert to datetime to check expiration
                    expires = ssl.cert_time_to_seconds(not_after)
                    is_expired = datetime.utcnow().timestamp() > expires
                    
                    return {
                        "issuer": issuer.get('organizationName'),
                        "not_before": not_before,
                        "not_after": not_after,
                        "is_expired": is_expired,
                        "has_ssl": True
                    }
        except Exception as e:
            logger.error(f"SSL error for {domain}: {e}")
            return {
                "error": str(e),
                "has_ssl": False
            }

class SandboxAPI:
    """Mock implementation for Sandbox.co.in TSP."""
    def __init__(self):
        self.api_key = os.getenv("SANDBOX_API_KEY", "dummy_key")
        self.base_url = "https://api.sandbox.co.in/v1"

    async def verify_gstin(self, gstin: str) -> dict:
        """Dummy response for GSTIN verification."""
        if not gstin:
            return {"error": "No GSTIN provided"}
        
        # Mock logic based on input string
        if "INVALID" in gstin.upper():
            return {"valid": False, "status": "Cancelled", "taxpayer_name": None}
            
        return {
            "valid": True,
            "status": "Active",
            "taxpayer_name": "Mocked Taxpayer Pvt Ltd",
            "registration_date": "2020-01-01",
            "taxpayer_type": "Regular",
            "gstin": gstin
        }
        
    async def verify_pan(self, pan: str) -> dict:
        """Dummy response for PAN verification."""
        if not pan:
            return {"error": "No PAN provided"}
            
        if "INVALID" in pan.upper():
            return {"valid": False, "name": None, "status": "Inactive"}
            
        return {
            "valid": True,
            "status": "Active",
            "name": "Mocked Taxpayer Pvt Ltd",
            "pan": pan
        }
        
    async def verify_msmed(self, msmed_num: str) -> dict:
        """Dummy response for MSMED/Udyam verification."""
        if not msmed_num:
            return {"error": "No MSMED number provided"}
            
        if "INVALID" in msmed_num.upper():
            return {"valid": False, "enterprise_type": None}
            
        return {
            "valid": True,
            "enterprise_type": "Micro",
            "name": "Mocked Taxpayer Pvt Ltd",
            "msmed_number": msmed_num,
            "status": "Active"
        }

# Initialize API clients
opencorp = OpenCorporatesAPI()
opensanctions = OpenSanctionsAPI()
gdelt = GDELTNewsAPI()
whois_api = WHOISAPI()
ssl_api = SSLCheckAPI()
sandbox_api = SandboxAPI()
