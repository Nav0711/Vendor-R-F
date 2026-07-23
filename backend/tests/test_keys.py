import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return "No Key"
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        urllib.request.urlopen(url)
        return "Status: OK"
    except urllib.error.HTTPError as e:
        return f"Status: {e.code}"
    except Exception as e:
        return str(e)

def test_serper():
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key: return "No Key"
    url = "https://google.serper.dev/search"
    req = urllib.request.Request(url, data=json.dumps({"q": "apple"}).encode('utf-8'), headers={'X-API-KEY': api_key, 'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
        return "Status: OK"
    except urllib.error.HTTPError as e:
        return f"Status: {e.code}"
    except Exception as e:
        return str(e)

def test_newsapi():
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key: return "No Key"
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        urllib.request.urlopen(req)
        return "Status: OK"
    except urllib.error.HTTPError as e:
        return f"Status: {e.code}"
    except Exception as e:
        return str(e)

def test_anthropic():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key: return "No Key"
    url = "https://api.anthropic.com/v1/messages"
    req = urllib.request.Request(url, data=json.dumps({"model": "claude-3-haiku-20240307", "max_tokens": 10, "messages": [{"role": "user", "content": "hello"}]}).encode('utf-8'), headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req)
        return "Status: OK"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        return f"Status: {e.code} - {err_body}"
    except Exception as e:
        return str(e)

def test_opensanctions():
    api_key = os.getenv("OPENSANCTIONS_API_KEY")
    if not api_key: return "No Key"
    url = "https://api.opensanctions.org/match/default"
    req = urllib.request.Request(url, data=json.dumps({"queries": {"q1": {"schema": "Person", "properties": {"name": ["John Doe"]}}}}).encode('utf-8'), headers={"Authorization": f"ApiKey {api_key}", "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        return "Status: OK"
    except urllib.error.HTTPError as e:
        return f"Status: {e.code}"
    except Exception as e:
        return str(e)

def test_ecourts():
    api_key = os.getenv("ECOURTS_API_KEY")
    if not api_key: return "No Key"
    base_url = os.getenv("ECOURTS_BASE_URL", "https://api.ecourtsindia.com/v1").rstrip("/")
    url = f"{base_url}/search/party"
    req = urllib.request.Request(url, data=json.dumps({"party_name": "reliance"}).encode('utf-8'), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        return "Status: OK"
    except urllib.error.HTTPError as e:
        return f"Status: {e.code}"
    except Exception as e:
        return str(e)

print("Gemini:", test_gemini())
print("Serper:", test_serper())
print("NewsAPI:", test_newsapi())
print("Anthropic:", test_anthropic())
print("OpenSanctions:", test_opensanctions())
print("ECourtsIndia:", test_ecourts())
