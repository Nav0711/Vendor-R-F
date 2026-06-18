from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, engine
from models import VendorInput, VendorRiskReport, Base
from data_aggregator import aggregate_vendor_data
from llm_service import extract_findings_from_data
from risk_scorer import score_findings
import json
import pandas as pd
from typing import Optional
import io
import math

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VendorLens Prototype")

# Enable CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ PYDANTIC MODELS ============

class VendorIntakeResponse(BaseModel):
    input_id: str
    legal_name: str
    message: str

class FindingResponse(BaseModel):
    finding_type: str
    severity: str
    title: str
    description: str
    source_api: str
    confidence_score: float

class RiskReportResponse(BaseModel):
    report_id: str
    overall_risk_tier: str
    risk_score: float
    summary: str
    findings: list[FindingResponse]
    recommendations: str

# ============ ENDPOINTS ============

def _clean_str(val) -> Optional[str]:
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None

def _split_list(val) -> list[str]:
    if pd.isna(val):
        return []
    s = str(val).strip()
    return [v.strip() for v in s.split(";") if v.strip()] if s else []

@app.post("/api/v1/vendor/intake", response_model=VendorIntakeResponse)
async def intake_vendor_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept vendor data via Excel upload and store in DB."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Vendor_Intake", dtype=str)
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel template has no data row")
        
        row = df.iloc[0] # Single vendor per upload
        
        legal_name = _clean_str(row.get("legal_name"))
        website_domain = _clean_str(row.get("website_domain"))
        
        if not legal_name or not website_domain:
            raise HTTPException(status_code=400, detail="Excel must contain legal_name and website_domain")
            
        social_handles = {}
        for col, platform in [("linkedin_handle", "linkedin"), ("twitter_handle", "twitter"), ("facebook_handle", "facebook")]:
            val = _clean_str(row.get(col))
            if val:
                social_handles[platform] = val

        vendor = VendorInput(
            legal_name=legal_name,
            website_domain=website_domain,
            registration_number=_clean_str(row.get("registration_number")),
            jurisdiction_country=_clean_str(row.get("jurisdiction_country")),
            tax_identifier=_clean_str(row.get("tax_identifier")),
            registered_address=_clean_str(row.get("registered_address")),
            director_names=_split_list(row.get("director_names")),
            director_din=_split_list(row.get("director_din")),
            founder_ceo_name=_clean_str(row.get("founder_ceo_name")),
            social_handles=social_handles,
            corporate_email_domain=_clean_str(row.get("corporate_email_domain")),
            pan_number=_clean_str(row.get("pan_number")),
            city=_clean_str(row.get("city")),
            mobile_number=_clean_str(row.get("mobile_number")),
            msmed_certificate_number=_clean_str(row.get("msmed_certificate_number")),
            source_method="excel",
            source_filename=file.filename
        )
        
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        
        return VendorIntakeResponse(
            input_id=vendor.input_id,
            legal_name=vendor.legal_name,
            message="Vendor intake recorded from Excel. Call /scan to start screening."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to process Excel file: {str(e)}")

@app.post("/api/v1/scan/{input_id}", response_model=RiskReportResponse)
async def scan_vendor(input_id: str, db: Session = Depends(get_db)):
    """
    Scan a vendor: aggregate data + LLM analysis + scoring.
    """
    try:
        # 1. Get vendor input
        vendor = db.query(VendorInput).filter(VendorInput.input_id == input_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # 2. Aggregate data
        aggregated_data = await aggregate_vendor_data(
            legal_name=vendor.legal_name,
            website_domain=vendor.website_domain,
            registration_number=vendor.registration_number,
            jurisdiction_country=vendor.jurisdiction_country,
            director_names=vendor.director_names or [],
            director_din=vendor.director_din or [],
            founder_ceo_name=vendor.founder_ceo_name,
            tax_identifier=vendor.tax_identifier,
            pan_number=vendor.pan_number,
            msmed_certificate_number=vendor.msmed_certificate_number
        )
        
        # 3. Extract findings via LLM
        findings = await extract_findings_from_data(aggregated_data)
        
        # 4. Score findings
        risk_result = score_findings(findings)
        
        # 5. Save report
        report = VendorRiskReport(
            input_id=input_id,
            overall_risk_tier=risk_result["tier"],
            risk_score=risk_result["score"],
            summary=risk_result["summary"],
            critical_count=risk_result["critical"],
            high_count=risk_result["high"],
            medium_count=risk_result["medium"],
            low_count=risk_result["low"],
            findings_count=len(findings),
            findings_json=findings,
            recommendations=risk_result["recommendations"],
            raw_api_data=aggregated_data
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return RiskReportResponse(
            report_id=report.report_id,
            overall_risk_tier=report.overall_risk_tier,
            risk_score=float(report.risk_score),
            summary=report.summary,
            findings=[FindingResponse(**f) for f in report.findings_json],
            recommendations=report.recommendations
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/api/v1/report/{report_id}")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    """Retrieve a previous report."""
    report = db.query(VendorRiskReport).filter(VendorRiskReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "report_id": report.report_id,
        "overall_risk_tier": report.overall_risk_tier,
        "risk_score": float(report.risk_score),
        "summary": report.summary,
        "findings": report.findings_json,
        "recommendations": report.recommendations,
        "created_at": report.created_at.isoformat(),
        "input_id": report.input_id
    }

@app.get("/health")
async def health_check():
    """Health check for load balancer."""
    return {"status": "healthy"}
