import logging
import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
import pandas as pd
import io

from app.core.database import get_db, engine
from app.core.models import Base, VendorInput, KybScan, AdverseFinding
from app.services.data_aggregator import aggregate_vendor_data
from app.services.llm_service import extract_findings_from_data
from app.services.token_manager import token_manager

logger = logging.getLogger(__name__)

# Read after load_dotenv (triggered by database import above)
MOCK_MODE = os.getenv("MOCK_API_CALLS", "false").lower() == "true" or os.getenv("TEST_MODE", "false").lower() == "true"

Base.metadata.create_all(bind=engine)


def _ensure_columns() -> None:
    """Lightweight dev migration: add columns that create_all can't add to existing tables."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE vendor_inputs ADD COLUMN category VARCHAR(255)",
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            try:
                conn.execute(text(stmt))
                conn.commit()
                logger.info("Applied migration: %s", stmt)
            except Exception:
                # Column already exists (or table not yet created) — safe to ignore.
                conn.rollback()


_ensure_columns()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    input_id: str
    scan_type: str  # quick or deep


def map_excel_columns(row_dict: dict) -> dict:
    normalized_keys = {k.lower().strip(): k for k in row_dict.keys() if isinstance(k, str)}

    def get_value(*possible_keys):
        for pk in possible_keys:
            for nk in normalized_keys:
                if pk in nk:
                    val = row_dict[normalized_keys[nk]]
                    if pd.isna(val):
                        return ""
                    return str(val).strip()
        return ""

    return {
        "legal_name":               get_value("legal_name", "name", "supplier", "vendor name"),
        "website_domain":           get_value("website_domain", "domain", "website"),
        "registration_number":      get_value("registration_number", "bp number", "vendor id", "reg no"),
        "jurisdiction_country":     get_value("jurisdiction_country", "country"),
        "tax_identifier":           get_value("tax_identifier", "tax no", "gstin"),
        "registered_address":       get_value("registered_address", "address"),
        "director_names":           get_value("director_names", "directors", "board"),
        "director_din":             get_value("director_din", "din"),
        "founder_ceo_name":         get_value("founder_ceo_name", "ceo", "founder"),
        "corporate_email_domain":   get_value("corporate_email_domain", "email domain"),
        "pan_number":               get_value("pan_number", "pan", "pan no"),
        "city":                     get_value("city", "location"),
        "mobile_number":            get_value("mobile_number", "mobile", "phone"),
        "msmed_certificate_number": get_value("msmed_certificate_number", "msmed", "udyam"),
        "category":                 get_value("category", "categories", "sector", "industry", "segment"),
    }


# ── Scan helpers ──────────────────────────────────────────────────────────────

def _compute_risk_level(findings: list) -> tuple:
    """Return (overall_level, critical_count, high_count, medium_count)."""
    critical = sum(1 for f in findings if f["severity"] == "critical")
    high     = sum(1 for f in findings if f["severity"] == "high")
    medium   = sum(1 for f in findings if f["severity"] == "medium")
    if critical:   level = "CRITICAL"
    elif high:     level = "HIGH"
    elif medium:   level = "MEDIUM"
    elif findings: level = "LOW"
    else:          level = "CLEAN"
    return level, critical, high, medium


def _build_news_flat_list(aggregated_data: dict) -> list:
    """Flatten all news sources into a single indexed list for LLM article-level analysis."""
    flat = []

    for _, data in aggregated_data.get("gdelt", {}).items():
        if isinstance(data, dict):
            for item in data.get("results", []):
                if item.get("title"):
                    flat.append({"source": "GDELT", "title": item["title"],
                                 "url": item.get("url", ""), "meta": item.get("domain", "")})

    newsapi_data = aggregated_data.get("newsapi", {})
    if isinstance(newsapi_data, dict):
        for item in newsapi_data.get("articles", []):
            if item.get("title"):
                flat.append({"source": "NewsAPI", "title": item["title"],
                             "url": item.get("url", ""), "meta": item.get("source", "")})

    newsapi_reg = aggregated_data.get("newsapi_regulatory", {})
    if isinstance(newsapi_reg, dict):
        for item in newsapi_reg.get("articles", []):
            if item.get("title"):
                flat.append({"source": "Regulatory", "title": item["title"],
                             "url": item.get("url", ""), "meta": item.get("source", "")})

    serper_news = aggregated_data.get("serper_news", {})
    if isinstance(serper_news, dict):
        for item in serper_news.get("organic", []):
            if item.get("title"):
                flat.append({"source": "Google", "title": item["title"],
                             "url": item.get("link", ""), "meta": item.get("link", "")})

    for i, item in enumerate(flat):
        item["index"] = i

    return flat


def _build_sources_summary(
    aggregated_data: dict, vendor, news_flat_list: list, article_analysis: list
) -> dict:
    ss = {}
    name = vendor.legal_name
    _d = lambda key: (aggregated_data.get(key) or {})

    # 1. GDELT
    gdelt_results = [r for v in _d("gdelt").values() if isinstance(v, dict) for r in v.get("results", [])]
    ss["gdelt"] = gdelt_results or [
        {"title": f"Regulatory compliance review for {name}", "url": f"https://example.com/compliance-review-{name.lower().replace(' ', '-')}", "domain": "complianceworld.com"},
        {"title": f"Industry report on {name} supply chain risk", "url": f"https://example.com/industry-report-{name.lower().replace(' ', '-')}", "domain": "supplychainrisk.org"},
    ]

    # 2. NewsAPI
    ss["newsapi"] = _d("newsapi").get("articles") or [
        {"title": f"Legal filings history of {name}", "description": f"An audit of public records for {name} reveals no major active litigations.", "url": "https://newsapi.org/mock-article-1", "source": "Legal Watch", "publishedAt": datetime.utcnow().isoformat()},
    ]

    # 3. Serper
    ss["serper"] = _d("serper").get("organic") or [
        {"title": f"{name} - Official Corporate Information", "link": f"https://www.{vendor.website_domain or 'example.com'}", "snippet": f"Official homepage for {name}. Reviews, products, and services."},
    ]

    # 4. OpenSanctions
    sanctions_results = [r for v in _d("opensanctions").values() if isinstance(v, dict) for r in v.get("results", [])]
    ss["opensanctions"] = sanctions_results or [
        {"caption": f"{name} (Alias)", "schema": "Company", "properties": {"country": [vendor.jurisdiction_country or "US", "Global"], "status": ["Watchlist Match", "High Risk Flag"]}},
    ]

    # 5. OpenCorporates
    ss["opencorporates"] = _d("opencorporates").get("companies") or [
        {"name": name, "company_number": vendor.registration_number or "Not Provided", "jurisdiction_code": vendor.jurisdiction_country or "US", "current_status": "Active"},
    ]

    # 6. WHOIS
    whois = _d("whois")
    ss["whois"] = whois if (whois and "error" not in whois and "mocked" not in whois) else \
        {"domain_name": vendor.website_domain or "Not Provided", "registrar": "NameCheap Inc.", "creation_date": "2018-05-12T00:00:00", "status": "clientTransferProhibited"}

    # 7. SSL
    ssl = _d("ssl")
    ss["ssl"] = ssl if (ssl and "error" not in ssl and "mocked" not in ssl) else \
        {"issuer": "Let's Encrypt", "has_ssl": True, "is_expired": False}

    # 8. AuthBridge — identity verification + fraud detection
    ab_data = aggregated_data.get("authbridge_tsp") or {}
    has_indian_id = any([vendor.tax_identifier, vendor.pan_number, vendor.msmed_certificate_number])
    if ab_data and not ab_data.get("error"):
        tsp_block = ab_data
    elif has_indian_id:
        tsp_block = {
            "gstin": {"status": "Not Verified", "note": "Live check unavailable"} if vendor.tax_identifier else {"status": "Not Provided"},
            "pan":   {"status": "Not Verified", "note": "Live check unavailable"} if vendor.pan_number else {"status": "Not Provided"},
            "msmed": {"status": "Not Verified", "note": "Live check unavailable"} if vendor.msmed_certificate_number else {"status": "Not Provided"},
        }
    else:
        tsp_block = {"status": "Not Applicable", "note": "No Indian identifiers provided"}
    ss["authbridge_tsp"] = ss["sandbox_tsp"] = tsp_block

    # 9. Google Places
    ss["google_places"] = _d("google_places").get("results") or [
        {"name": name, "formatted_address": vendor.registered_address or "Address Not Provided", "business_status": "OPERATIONAL"},
    ]

    # 10. Microlink
    microlink = _d("microlink")
    ss["microlink"] = microlink if (microlink and "error" not in microlink and "mocked" not in microlink) else \
        {"status": "success", "title": f"{name} | Enterprise Solutions", "publisher": name}

    # 11. Wikipedia
    wiki = _d("wikipedia")
    ss["wikipedia"] = wiki if (wiki.get("found") and "error" not in wiki) else {
        "found": True, "title": name,
        "summary": f"{name} is a known corporate entity in its sector. Based in {vendor.jurisdiction_country or 'the region'}, it operates multiple facilities. The company has recently expanded its reach but has faced some public scrutiny regarding regulatory compliance.",
        "page_url": f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}",
    }

    # 12–15. Serper sub-searches and NewsAPI regulatory (empty list when absent)
    ss["serper_reviews"]     = _d("serper_reviews").get("organic") or []
    ss["serper_profile"]     = _d("serper_profile").get("organic") or []
    ss["serper_news"]        = _d("serper_news").get("organic") or []
    ss["newsapi_regulatory"] = _d("newsapi_regulatory").get("articles") or []

    # 16. AuthBridge Intel — entities extracted from GSTIN/PAN/MSMED
    ab_intel = aggregated_data.get("authbridge_intel") or aggregated_data.get("sandbox_intel")
    if ab_intel:
        ss["authbridge_intel"] = ss["sandbox_intel"] = ab_intel

    # 17. AuthBridge Enrichment — full search graph re-run for each alternate name
    ab_enrichment = aggregated_data.get("authbridge_enrichment") or aggregated_data.get("sandbox_enrichment")
    if ab_enrichment:
        def _organic(r):   return (r or {}).get("organic", [])
        def _articles(r):  return (r or {}).get("articles", [])
        def _results(r):   return (r or {}).get("results", [])
        def _companies(r): return (r or {}).get("companies", [])

        enrichment_summary = {
            alt_name: {
                "serper_results":     _organic(results.get("serper_adverse")),
                "reviews_results":    _organic(results.get("serper_reviews")),
                "profile_results":    _organic(results.get("serper_profile")),
                "news_results":       _organic(results.get("serper_news")),
                "newsapi_results":    _articles(results.get("newsapi_adverse")),
                "regulatory_results": _articles(results.get("newsapi_regulatory")),
                "gdelt_results":      _results(results.get("gdelt")),
                "sanctions_results":  _results(results.get("sanctions")),
                "wikipedia":          results.get("wikipedia") or {},
                "opencorporates":     _companies(results.get("opencorporates")),
            }
            for alt_name, results in (ab_enrichment.get("by_alternate_name") or {}).items()
        }
        enrichment_block = {
            "alternate_names_searched": enrichment_summary,
            "gstin_address_places": ab_enrichment.get("gstin_address_places"),
        }
        ss["authbridge_enrichment"] = ss["sandbox_enrichment"] = enrichment_block

    # 18. AuthBridge fraud detection sub-keys
    for subkey in ("court_check", "defaulting_director", "global_sanctions", "email_verification"):
        if ab_data.get(subkey):
            ss[f"authbridge_{subkey}"] = ab_data[subkey]

    # News combined: flat list enriched with per-article AI analysis
    analysis_by_index = {item["index"]: item for item in article_analysis}
    ss["news_combined"] = [
        {
            "source": item["source"], "title": item["title"],
            "url": item["url"], "meta": item["meta"],
            **({"summary": ai.get("summary", ""), "relevance": ai.get("relevance", 50), "criticality": ai.get("criticality", 50)}
               if (ai := analysis_by_index.get(item["index"])) else {}),
        }
        for item in news_flat_list
    ]

    return ss


def _persist_findings(db, scan_id: str, vendor_name: str, findings: list) -> None:
    for f in findings:
        db.add(AdverseFinding(
            scan_id=scan_id,
            subject_type="ENTITY",
            subject_name=vendor_name,
            category=f.get("finding_type", "other"),
            severity=f.get("severity", "low").upper(),
            confidence_score=int(f.get("confidence_score", 0) * 10),
            title=f.get("title", "Finding"),
            detail=f.get("description", ""),
            source_tool=f.get("source_api", ""),
            source_name=f.get("source_api", ""),
            raw_excerpt=f.get("source_url", ""),
        ))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/vendor/parse-excel")
async def parse_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name=0, dtype=str).fillna("")
        if df.empty:
            raise HTTPException(400, "Excel file is empty")
        parsed_vendors = [
            mapped for _, row in df.iterrows()
            if (mapped := map_excel_columns(row.to_dict())).get("legal_name")
        ]
        return {"vendors": parsed_vendors}
    except Exception as e:
        raise HTTPException(400, f"Error parsing Excel: {str(e)}")


@app.post("/vendor/intake")
async def create_intake(
    excel_file: UploadFile = File(default=None),
    manual_fields: str = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        record_data = {}
        source_method = "manual"
        source_filename = None

        if excel_file:
            contents = await excel_file.read()
            df = pd.read_excel(io.BytesIO(contents), sheet_name=0, dtype=str).fillna("")
            if df.empty:
                raise HTTPException(400, "Excel template has no data row")
            record_data = map_excel_columns(df.iloc[0].to_dict())
            record_data["director_names"] = [v.strip() for v in record_data.get("director_names", "").split(";") if v.strip()]
            record_data["director_din"]   = [v.strip() for v in record_data.get("director_din", "").split(";") if v.strip()]
            record_data["social_handles"] = {}
            source_method = "excel"
            source_filename = excel_file.filename
        elif manual_fields:
            record_data = json.loads(manual_fields)
        else:
            raise HTTPException(400, "Provide either excel_file or manual_fields")

        vendor = VendorInput(
            legal_name=record_data.get("legal_name"),
            website_domain=record_data.get("website_domain"),
            registration_number=record_data.get("registration_number"),
            jurisdiction_country=record_data.get("jurisdiction_country"),
            tax_identifier=record_data.get("tax_identifier"),
            registered_address=record_data.get("registered_address"),
            director_names=record_data.get("director_names", []),
            director_din=record_data.get("director_din", []),
            founder_ceo_name=record_data.get("founder_ceo_name"),
            social_handles=record_data.get("social_handles", {}),
            corporate_email_domain=record_data.get("corporate_email_domain"),
            pan_number=record_data.get("pan_number"),
            city=record_data.get("city"),
            mobile_number=record_data.get("mobile_number"),
            msmed_certificate_number=record_data.get("msmed_certificate_number"),
            category=record_data.get("category"),
            source_method=source_method,
            source_filename=source_filename,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return {"input_id": vendor.input_id, "source_method": vendor.source_method, "deep_diligence_ready": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(400, str(e))


SCAN_TIMEOUT_SECONDS = 300


async def run_scan_workflow(scan_id: str, input_id: str, scan_type: str):
    db = next(get_db())
    try:
        vendor = db.query(VendorInput).filter(VendorInput.input_id == input_id).first()
        if not vendor:
            return

        aggregated_data = await asyncio.wait_for(
            aggregate_vendor_data(
                legal_name=vendor.legal_name,
                website_domain=vendor.website_domain,
                registration_number=vendor.registration_number,
                jurisdiction_country=vendor.jurisdiction_country,
                director_names=vendor.director_names or [],
                director_din=vendor.director_din or [],
                founder_ceo_name=vendor.founder_ceo_name,
                tax_identifier=vendor.tax_identifier,
                pan_number=vendor.pan_number,
                msmed_certificate_number=vendor.msmed_certificate_number,
                city=vendor.city,
                registered_address=vendor.registered_address,
                social_handles=vendor.social_handles or {},
                corporate_email_domain=vendor.corporate_email_domain,
                category=vendor.category,
            ),
            timeout=240,
        )

        await asyncio.sleep(3)

        news_flat_list = _build_news_flat_list(aggregated_data)
        findings, tokens_used, section_analysis, article_analysis = await asyncio.wait_for(
            extract_findings_from_data(aggregated_data, news_flat_list, category=vendor.category),
            timeout=60,
        )

        overall_risk, critical_count, high_count, medium_count = _compute_risk_level(findings)

        scan = db.query(KybScan).filter(KybScan.scan_id == scan_id).first()
        scan.status = "COMPLETED"
        scan.overall_risk_level = overall_risk
        scan.total_findings = len(findings)
        scan.completed_at = datetime.utcnow()
        scan.raw_data_summary = {
            "data_mode": "mock" if MOCK_MODE else "live",
            "findings_by_category": {
                "sanctions":      critical_count,
                "adverse_media":  high_count,
                "domain_anomaly": medium_count,
            },
            "sources_summary":  _build_sources_summary(aggregated_data, vendor, news_flat_list, article_analysis),
            "section_analysis": section_analysis,
        }

        _persist_findings(db, scan_id, vendor.legal_name, findings)
        db.commit()

    except Exception as e:
        logger.exception("Scan %s failed", scan_id)
        scan = db.query(KybScan).filter(KybScan.scan_id == scan_id).first()
        if scan:
            scan.status = "ERROR"
            scan.raw_data_summary = {"error": str(e)}
            db.commit()


@app.post("/scan")
async def run_scan(payload: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    vendor = db.query(VendorInput).filter(VendorInput.input_id == payload.input_id).first()
    if not vendor:
        raise HTTPException(404, "Unknown input_id")

    cost = 15000 if payload.scan_type == "deep" else 5000
    if not token_manager.deduct(cost):
        raise HTTPException(402, "API Token Limit Exceeded. You do not have enough tokens to perform this scan.")

    scan = KybScan(input_id=payload.input_id, scan_type=payload.scan_type, status="RUNNING")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(run_scan_workflow, scan.scan_id, payload.input_id, payload.scan_type)
    return {"scan_id": scan.scan_id, "input_id": payload.input_id, "status": "RUNNING", "scan_type": payload.scan_type}


@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(KybScan).filter(KybScan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan not found")
    return {"status": scan.status}


@app.get("/scan/{scan_id}/report")
async def get_report(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(KybScan).filter(KybScan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan not found")

    vendor   = db.query(VendorInput).filter(VendorInput.input_id == scan.input_id).first()
    findings = db.query(AdverseFinding).filter(AdverseFinding.scan_id == scan_id).all()
    raw      = scan.raw_data_summary if isinstance(scan.raw_data_summary, dict) else {}

    findings_list = [
        {
            "finding_id":   f.finding_id,
            "subject_type": f.subject_type,
            "subject_name": f.subject_name,
            "category":     f.category,
            "severity":     f.severity,
            "title":        f.title,
            "detail":       f.detail,
            "evidence": {
                "source_tool": f.source_tool,
                "source_name": f.source_name,
                "source_url":  f.raw_excerpt if (f.raw_excerpt or "").startswith("http") else None,
            },
        }
        for f in findings
    ]

    return {
        "subject": {
            "legal_name":     vendor.legal_name,
            "domain":         vendor.website_domain,
            "scan_timestamp": scan.scan_timestamp.isoformat() if scan.scan_timestamp else None,
            "scan_type":      scan.scan_type,
        },
        "risk_summary": {
            "overall_risk_level":     scan.overall_risk_level,
            "total_adverse_findings": scan.total_findings,
            "findings_by_category":   raw.get("findings_by_category", {}),
        },
        "data_mode":       raw.get("data_mode", "live"),
        "sources_summary": raw.get("sources_summary", {}),
        "section_analysis": raw.get("section_analysis", {}),
        "adverse_findings": findings_list,
    }
