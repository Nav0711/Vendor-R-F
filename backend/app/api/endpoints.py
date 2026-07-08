import httpx
import os
import logging
import whois
import ssl
import socket
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)
MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true" or os.getenv("TEST_MODE", "false").lower() == "true"

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
                data = response.json()
                results = data.get("results", {}).get("companies", [])[:10]
                return {
                    "companies": [
                        {
                            "name": c.get("company", {}).get("name"),
                            "company_number": c.get("company", {}).get("company_number"),
                            "jurisdiction_code": c.get("company", {}).get("jurisdiction_code"),
                            "incorporation_date": c.get("company", {}).get("incorporation_date"),
                            "dissolution_date": c.get("company", {}).get("dissolution_date"),
                            "company_type": c.get("company", {}).get("company_type"),
                            "current_status": c.get("company", {}).get("current_status")
                        }
                        for c in results
                    ]
                }
        except Exception as e:
            logger.error(f"OpenCorporates error: {e}")
            return {"error": str(e)}

class OpenSanctionsAPI:
    def __init__(self):
        self.api_key = os.getenv("OPENSANCTIONS_API_KEY")
        # Correct yente-based hosted API — no version prefix, dataset in path
        self.base_url = "https://api.opensanctions.org"

    async def search_entity(self, name: str) -> dict:
        """Search for sanctions/PEP matches."""
        if MOCK_MODE:
            return {"mocked": True, "data": {}}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {"Accept": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"ApiKey {self.api_key}"
                response = await client.get(
                    f"{self.base_url}/search/default",
                    params={"q": name, "fuzzy": "true", "limit": 10},
                    headers=headers
                )
                if response.status_code in (401, 403):
                    return {"mocked_due_to_auth_error": True, "error": f"API Key Issue ({response.status_code})"}
                if response.status_code == 404:
                    logger.warning(f"OpenSanctions 404 for query '{name}' — returning no results")
                    return {"results": []}
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])[:10]
                return {
                    "results": [
                        {
                            "id": item.get("id"),
                            "caption": item.get("caption"),
                            "schema": item.get("schema"),
                            "properties": {
                                "name": item.get("properties", {}).get("name"),
                                "country": item.get("properties", {}).get("country"),
                                "status": item.get("properties", {}).get("status")
                            }
                        }
                        for item in results
                    ]
                }
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
                data = response.json()
                results = data.get("result", [])[:10]
                return {
                    "results": [
                        {"title": item.get("title"), "url": item.get("url"), "domain": item.get("domain")}
                        for item in results
                    ]
                }
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

class AuthBridgeAPI:
    """
    AuthBridge — Indian KYC/fraud-detection API provider.

    Covers:
      India identity: GSTIN / PAN / MSME verification
      Utilities:      Email Verification
      Fraud Detection: Court Check, Defaulting Director Check, Global Sanctions Check

    Required env vars:
      AUTHBRIDGE_API_KEY    — your AuthBridge API key
      AUTHBRIDGE_API_SECRET — your AuthBridge API secret
      AUTHBRIDGE_BASE_URL   — base URL (confirm with AuthBridge; default below)

    NOTE: endpoint paths below are marked # CONFIRM — verify each against your
    AuthBridge API documentation before going live.
    """
    def __init__(self):
        self.api_key    = os.getenv("AUTHBRIDGE_API_KEY")
        self.api_secret = os.getenv("AUTHBRIDGE_API_SECRET")
        self.base_url   = os.getenv("AUTHBRIDGE_BASE_URL", "https://api.authbridge.ai")
        self.access_token  = None
        self.token_expiry  = None

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        if not self.api_key:
            raise ValueError("AUTHBRIDGE_API_KEY not set in .env")
        if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.access_token
        response = await client.post(
            f"{self.base_url}/v1/token",          # CONFIRM with AuthBridge docs
            headers={"x-api-key": self.api_key, "x-api-secret": self.api_secret or ""},
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data.get("access_token") or data.get("token")
        self.token_expiry = datetime.utcnow()
        return self.access_token

    async def _headers(self, client: httpx.AsyncClient) -> dict:
        token = await self._authenticate(client)
        return {
            "Authorization": f"Bearer {token}",
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    # ── India Identity Verification ───────────────────────────────────────

    async def verify_gstin(self, gstin: str) -> dict:
        if not gstin:
            return {"error": "No GSTIN provided"}
        if MOCK_MODE:
            if "INVALID" in gstin.upper():
                return {"valid": False, "status": "Cancelled", "taxpayer_name": None}
            return {
                "valid": True, "status": "Active",
                "taxpayer_name": "Mocked Taxpayer Pvt Ltd",
                "registration_date": "2020-01-01", "taxpayer_type": "Regular", "gstin": gstin,
                "raw_response": {
                    "tradeNam": "Mocked Taxpayer Pvt Ltd", "lgnm": "Mocked Legal Name Pvt Ltd",
                    "sts": "Active",
                    "pradr": {"adr": "123 Mock Street", "dst": "Mumbai", "stcd": "Maharashtra", "pncd": "400001"},
                },
            }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._headers(client)
                response = await client.post(
                    f"{self.base_url}/v1/gst/gstin",   # CONFIRM with AuthBridge docs
                    headers=headers,
                    json={"gstin": gstin, "consent": "Y"},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                status = data.get("sts", "")
                return {
                    "valid": status.upper() == "ACTIVE",
                    "status": status,
                    "taxpayer_name": data.get("tradeNam") or data.get("lgnm"),
                    "registration_date": data.get("rgdt"),
                    "gstin": gstin,
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge GSTIN error: {e}")
            return {"error": str(e), "valid": False}

    async def verify_pan(self, pan: str) -> dict:
        if not pan:
            return {"error": "No PAN provided"}
        if MOCK_MODE:
            if "INVALID" in pan.upper():
                return {"valid": False, "name": None, "status": "Inactive"}
            return {"valid": True, "status": "Active", "name": "Mocked Taxpayer Pvt Ltd", "pan": pan}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._headers(client)
                response = await client.post(
                    f"{self.base_url}/v1/kyc/pan",     # CONFIRM with AuthBridge docs
                    headers=headers,
                    json={"pan": pan, "consent": "Y", "reason": "KYB Due Diligence"},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                status = data.get("status", "")
                return {
                    "valid": status.upper() in ("VALID", "ACTIVE"),
                    "status": status,
                    "name": data.get("full_name") or data.get("name"),
                    "pan": pan,
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge PAN error: {e}")
            return {"error": str(e), "valid": False}

    async def verify_msmed(self, msmed_num: str) -> dict:
        if not msmed_num:
            return {"error": "No MSMED number provided"}
        if MOCK_MODE:
            if "INVALID" in msmed_num.upper():
                return {"valid": False, "enterprise_type": None}
            return {"valid": True, "enterprise_type": "Micro", "name": "Mocked Taxpayer Pvt Ltd",
                    "msmed_number": msmed_num, "status": "Active"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._headers(client)
                response = await client.post(
                    f"{self.base_url}/v1/kyc/msme",    # CONFIRM with AuthBridge docs
                    headers=headers,
                    json={"udyam_number": msmed_num, "consent": "Y"},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return {
                    "valid": bool(data),
                    "enterprise_type": data.get("enterprise_type", "Unknown"),
                    "name": data.get("enterprise_name") or data.get("company_name"),
                    "district": data.get("district"),
                    "state": data.get("state"),
                    "activity": data.get("major_activity") or data.get("activity"),
                    "msmed_number": msmed_num,
                    "status": "Active" if data else "Inactive",
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge MSMED error: {e}")
            return {"error": str(e), "valid": False}

    # ── Utilities ─────────────────────────────────────────────────────────

    async def verify_email(self, email_or_domain: str) -> dict:
        """Email/domain verification — deliverability, MX records, disposable-domain flag."""
        if not email_or_domain:
            return {"error": "No email/domain provided"}
        if MOCK_MODE:
            disposable = email_or_domain.lower().split("@")[-1] in (
                "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com"
            )
            return {
                "valid": True, "deliverable": not disposable, "disposable": disposable,
                "mx_records": not disposable, "domain": email_or_domain,
                "risk": "high" if disposable else "low",
            }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._headers(client)
                response = await client.post(
                    f"{self.base_url}/v1/utilities/email-verification",  # CONFIRM with AuthBridge docs
                    headers=headers,
                    json={"email": email_or_domain, "consent": "Y"},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return {
                    "valid":       data.get("is_valid", False),
                    "deliverable": data.get("is_deliverable", False),
                    "disposable":  data.get("is_disposable", False),
                    "mx_records":  data.get("has_mx_records", False),
                    "domain":      email_or_domain,
                    "risk":        data.get("risk_level", "unknown"),
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge email verification error: {e}")
            return {"error": str(e)}

    # ── Fraud Detection ───────────────────────────────────────────────────

    async def check_court(self, name: str, entity_type: str = "company") -> dict:
        """Court Check — litigation/court records in Indian courts for entity or individual."""
        if not name:
            return {"error": "No name provided"}
        if MOCK_MODE:
            return {"name": name, "entity_type": entity_type, "cases_found": 0, "cases": [], "risk": "low"}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                headers = await self._headers(client)
                response = await client.post(
                    f"{self.base_url}/v1/fraud/court-check",  # CONFIRM with AuthBridge docs
                    headers=headers,
                    json={"name": name, "type": entity_type, "consent": "Y"},
                )
                response.raise_for_status()
                data  = response.json().get("data", {})
                cases = data.get("cases", data.get("court_records", []))
                return {
                    "name": name, "entity_type": entity_type,
                    "cases_found": len(cases), "cases": cases,
                    "risk": "high" if cases else "low",
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge court check error for '{name}': {e}")
            return {"error": str(e), "name": name, "cases_found": 0, "cases": []}

    async def check_defaulting_director(self, name: str, din: Optional[str] = None) -> dict:
        """Defaulting Director Check — MCA database check for disqualified/defaulting directors."""
        if not name:
            return {"error": "No name provided"}
        if MOCK_MODE:
            return {"name": name, "din": din, "is_defaulter": False,
                    "disqualification_reason": None, "risk": "low"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._headers(client)
                payload = {"name": name, "consent": "Y"}
                if din:
                    payload["din"] = din
                response = await client.post(
                    f"{self.base_url}/v1/fraud/defaulting-director",  # CONFIRM with AuthBridge docs
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                is_defaulter = data.get("is_defaulter", False) or data.get("disqualified", False)
                return {
                    "name": name, "din": din,
                    "is_defaulter": is_defaulter,
                    "disqualification_reason": data.get("reason") or data.get("disqualification_reason"),
                    "risk": "critical" if is_defaulter else "low",
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge defaulting director error for '{name}': {e}")
            return {"error": str(e), "name": name, "is_defaulter": False}

    async def check_global_sanctions(self, name: str, entity_type: str = "company") -> dict:
        """Global Sanctions Check — screens against international sanctions lists via AuthBridge."""
        if not name:
            return {"error": "No name provided"}
        if MOCK_MODE:
            return {"name": name, "entity_type": entity_type,
                    "matches": [], "is_sanctioned": False, "risk": "low"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = await self._headers(client)
                response = await client.post(
                    f"{self.base_url}/v1/fraud/global-sanctions",  # CONFIRM with AuthBridge docs
                    headers=headers,
                    json={"name": name, "type": entity_type, "consent": "Y"},
                )
                response.raise_for_status()
                data    = response.json().get("data", {})
                matches = data.get("matches", data.get("sanctions_matches", []))
                return {
                    "name": name, "entity_type": entity_type,
                    "matches": matches, "is_sanctioned": bool(matches),
                    "risk": "critical" if matches else "low",
                    "raw_response": data,
                }
        except Exception as e:
            logger.error(f"AuthBridge global sanctions error for '{name}': {e}")
            return {"error": str(e), "name": name, "matches": [], "is_sanctioned": False}

class SerperAPI:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev/search"

    async def search(self, query: str) -> dict:
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        if not self.api_key:
            return {"error": "Missing SERPER_API_KEY"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                    json={"q": query}
                )
                response.raise_for_status()
                data = response.json()
                organic = data.get("organic", [])[:10]
                return {
                    "organic": [
                        {"title": item.get("title"), "link": item.get("link"), "snippet": item.get("snippet")}
                        for item in organic
                    ]
                }
        except Exception as e:
            logger.error(f"Serper API error: {e}")
            return {"error": str(e)}

class NewsAPIClient:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"

    async def search_news(self, query: str) -> dict:
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        if not self.api_key:
            return {"error": "Missing NEWS_API_KEY"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self.base_url,
                    params={"q": query, "apiKey": self.api_key, "language": "en", "pageSize": 10}
                )
                response.raise_for_status()
                data = response.json()
                articles = data.get("articles", [])[:10]
                return {
                    "articles": [
                        {
                            "title": item.get("title"),
                            "description": item.get("description"),
                            "url": item.get("url"),
                            "publishedAt": item.get("publishedAt"),
                            "source": item.get("source", {}).get("name")
                        }
                        for item in articles
                    ]
                }
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return {"error": str(e)}

class GooglePlacesAPI:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    async def search_address(self, query: str) -> dict:
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        if not self.api_key:
            return {"error": "Missing GOOGLE_MAPS_API_KEY"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self.base_url,
                    params={"query": query, "key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])[:5]
                return {
                    "results": [
                        {
                            "name": item.get("name"),
                            "formatted_address": item.get("formatted_address"),
                            "rating": item.get("rating"),
                            "business_status": item.get("business_status")
                        }
                        for item in results
                    ]
                }
        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            return {"error": str(e)}

class MicrolinkAPI:
    def __init__(self):
        self.api_key = os.getenv("MICROLINK_API_KEY")
        self.base_url = "https://api.microlink.io/"

    async def get_metadata(self, url: str) -> dict:
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        try:
            headers = {"x-api-key": self.api_key} if self.api_key else {}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self.base_url,
                    params={"url": f"http://{url}" if not url.startswith("http") else url},
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                sub_data = data.get("data", {})
                return {
                    "status": data.get("status"),
                    "title": sub_data.get("title"),
                    "description": sub_data.get("description"),
                    "publisher": sub_data.get("publisher"),
                    "logo": sub_data.get("logo", {}).get("url") if isinstance(sub_data.get("logo"), dict) else None
                }
        except Exception as e:
            logger.error(f"Microlink API error: {e}")
            return {"error": str(e)}

class WikipediaAPI:
    """Free Wikipedia REST API — no auth required."""
    async def get_summary(self, company_name: str) -> dict:
        if MOCK_MODE:
            return {"mocked": True, "data": {}}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                search_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "opensearch",
                        "search": company_name,
                        "limit": 3,
                        "namespace": 0,
                        "format": "json"
                    },
                    headers={"User-Agent": "VendorLens/1.0 (KYB due diligence tool)"}
                )
                search_resp.raise_for_status()
                search_data = search_resp.json()
                titles = search_data[1] if len(search_data) > 1 else []
                if not titles:
                    return {"found": False}
                title = titles[0]
                summary_resp = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
                    headers={"User-Agent": "VendorLens/1.0 (KYB due diligence tool)"}
                )
                if summary_resp.status_code == 404:
                    return {"found": False}
                summary_resp.raise_for_status()
                data = summary_resp.json()
                return {
                    "found": True,
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "summary": data.get("extract", "")[:1000],
                    "page_url": data.get("content_urls", {}).get("desktop", {}).get("page")
                }
        except Exception as e:
            logger.error(f"Wikipedia error: {e}")
            return {"error": str(e)}


# Initialize API clients
opencorp = OpenCorporatesAPI()
opensanctions = OpenSanctionsAPI()
gdelt = GDELTNewsAPI()
whois_api = WHOISAPI()
ssl_api = SSLCheckAPI()
authbridge_api = AuthBridgeAPI()
sandbox_api = authbridge_api  # legacy alias — internal callers still use sandbox_api
serper_api = SerperAPI()
news_api = NewsAPIClient()
google_places_api = GooglePlacesAPI()
microlink_api = MicrolinkAPI()
wikipedia_api = WikipediaAPI()
