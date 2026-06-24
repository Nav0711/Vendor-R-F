import asyncio
import pandas as pd
import io
import sys
import os
from fastapi.testclient import TestClient
from dotenv import load_dotenv
from pathlib import Path

# Add the parent directory to sys.path so we can import from the main app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env from the parent directory before importing app
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from main import app

client = TestClient(app)

def test_sandbox_integration():
    print("Preparing dummy Excel upload for Sandbox Integration test...")
    # 1. Create a dummy Excel file in memory
    df = pd.DataFrame([{
        "legal_name": "Indian Vendor Pvt Ltd",
        "website_domain": "indianvendor.in",
        "jurisdiction_country": "IN",
        "tax_identifier": "07AABCU9603INVALID",  # Should trigger high/medium risk
        "pan_number": "INVALIDPAN", # Should trigger high/medium risk
        "msmed_certificate_number": "UDYAM-MH-18-INVALID" # Should trigger risk
    }])
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Vendor_Intake", index=False)
    
    excel_buffer.seek(0)
    
    # 2. Upload the Excel file to /api/v1/vendor/intake
    files = {"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    print("Uploading to /api/v1/vendor/intake...")
    response = client.post("/api/v1/vendor/intake", files=files)
    
    if response.status_code != 200:
        print(f"Failed Intake Response ({response.status_code}):", response.text)
        return
        
    print("Intake Response:", response.status_code, response.text)
    input_id = response.json()["input_id"]
    
    # 3. Call the scan endpoint
    print(f"\nRunning AI Scan for input_id: {input_id}...")
    print("Please wait, this will call the Anthropic API if ANTHROPIC_API_KEY is present in .env...")
    scan_response = client.post(f"/api/v1/scan/{input_id}")
    
    print("\nScan Response Code:", scan_response.status_code)
    import json
    print(json.dumps(scan_response.json(), indent=2))

if __name__ == "__main__":
    test_sandbox_integration()
