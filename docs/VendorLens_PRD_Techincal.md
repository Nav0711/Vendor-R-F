# Product Requirements Document (PRD)
## VendorLens — Automated KYB & Vendor Due Diligence Platform
**Version:** 2.0  
**Status:** Engineering-Ready Draft  
**Classification:** Internal — Confidential  
**Last Updated:** June 2026

> **v2.0 changelog:** Replaced the two-tier *progressive disclosure* input model (Tier 1 form unlocking a Tier 2 form) with a **single-pass intake**. The user now provides all vendor data — manually or via one Excel upload — exactly once. **Scan depth (Quick Scan vs. Deep Diligence) is a separate, user-selected processing choice made *after* intake**, not a function of how the data was entered. The same captured input can be run through Quick Scan, then later upgraded to Deep Diligence, with zero re-entry.

---

## Table of Contents

1. [Executive Summary & Product Vision](#1-executive-summary--product-vision)
2. [Target Personas & User Journeys](#2-target-personas--user-journeys)
3. [Product Requirements & Input Schema](#3-product-requirements--input-schema)
4. [System Architecture & Tech Stack](#4-system-architecture--tech-stack)
5. [API Integration Specifications](#5-api-integration-specifications)
6. [AI/ML & NLP Specifications](#6-aiml--nlp-specifications)
7. [Risk Scoring Logic](#7-risk-scoring-logic)
8. [Data Storage — Store Only Negatives Pattern](#8-data-storage--store-only-negatives-pattern)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Out of Scope](#10-out-of-scope)
11. [Open Questions & Decisions](#11-open-questions--decisions)

---

## 1. Executive Summary & Product Vision

### 1.1 The Problem

Procurement and compliance teams performing vendor due diligence today face a three-way failure:

**Fragile custom scrapers** break every time a target website changes its HTML structure, requiring constant engineering maintenance. **Manual review processes** are inconsistent, slow (days per vendor), and non-auditable. **Point solutions** (one tool for sanctions, another for news, another for company registry) create data siloes with no unified risk view.

The result: either vendors slip through without adequate screening, or the screening process becomes an expensive bottleneck that delays commercial operations.

### 1.2 The Solution

**VendorLens** replaces fragile scrapers with a structured, API-first intelligence pipeline that aggregates public data from authoritative sources — corporate registries, sanctions lists, WHOIS databases, global news indices, and court records — then uses a Large Language Model as a due diligence analyst to synthesize the raw data into a structured, actionable risk report.

The platform is purpose-built for **Know Your Business (KYB)** and **Third-Party Risk Management (TPRM)** workflows, meaning it screens not just the legal entity but the entire control structure behind it: directors, ultimate beneficial owners (UBOs), and related entities.

### 1.3 Product Vision Statement

> *"Capture every vendor's data once — by hand or by Excel upload — then let the user decide, on demand, whether to run a 3-minute Quick Scan or a 15-minute Deep Diligence on that same data, storing only confirmed negative findings and surfacing them in a clear dashboard that requires zero manual data hunting and zero re-entry."*

### 1.4 Strategic Principles

| Principle | Implication |
|---|---|
| **Single intake, dual-depth output** | Vendor data is captured once (manual form or Excel upload); Quick Scan vs. Deep Diligence is a separate choice the user makes on that same stored data, as many times as needed |
| **API-first, no scrapers** | Zero maintenance overhead from HTML structure changes |
| **Store only negatives** | Minimal storage footprint; every DB row is a risk item |
| **LLM as analyst, not classifier** | Prompt-driven flexibility without ML model retraining |
| **Multi-layer entity screening** | Entity + Directors + UBOs all screened in one workflow |
| **Jurisdiction-agnostic** | Works for any country using global public data sources |

---

## 2. Target Personas & User Journeys


### 2.1 Single-Pass Intake, Then User-Selected Scan Depth

The UI no longer gates input behind two tiers. Instead, it splits the workflow into two independent steps: **Step A — Intake** (done once per vendor, by hand or by Excel upload, covering every field the platform can use) and **Step B — Scan Depth** (a choice the user makes every time they want a report, reusing the same saved intake). This removes re-entry entirely: a vendor can be Quick-Scanned today and Deep-Diligenced next week without typing anything twice.

```
┌───────────────────────────────────────────────────────────────┐
│  STEP A — INTAKE (once per vendor)                             │
│                                                                  │
│  Option 1: Manual Form            Option 2: Excel Upload        │
│  One page, every field from        VendorLens_Intake_Template.  │
│  Section 3.1 (Categories 1–4).     xlsx — one row, same fields, │
│  Fill what you have; leave the     parsed automatically.        │
│  rest blank.                                                     │
│                                                                  │
│  + Optional: attach GST cert / invoice / license — OCR auto-fills│
│    any fields still missing from either path above               │
│                                                                  │
│  → Output: one normalized VendorInputRecord, saved as `input_id`│
└───────────────────────────┬──────────────────────────────────────┘
                            │ Saved once — reused by every scan below
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  STEP B — CHOOSE SCAN DEPTH (any time, any number of times)     │
│                                                                  │
│  [ Quick Scan ]                    [ Deep Diligence ]            │
│  ~3 min                            ~12–15 min                   │
│  Entity + Sanctions + Domain        Everything Quick Scan covers,│
│  + News                            PLUS regulatory IDs, director/│
│                                     UBO screening, address &     │
│                                     digital-footprint checks      │
│                                                                  │
│  → Same input_id, run as Quick now and Deep later — no re-entry │
└───────────────────────────────────────────────────────────────┘
```

#### Scan Depth Comparison (the choice the user makes in Step B)

| | Quick Scan | Deep Diligence |
|---|---|---|
| Time SLA | < 3 minutes | < 15 minutes |
| Input categories used | Category 1 only (legal name + domain) | Categories 1–4 (everything captured at intake) |
| APIs triggered | OpenCorporates, GLEIF, WHOIS, GDELT, OpenSanctions, Google CSE | All of Quick Scan, plus MCA/Companies House officer lookups, OpenOwnership, Google Geocoding/Places, social-platform/SERP checks |
| Relative processing cost | Baseline (1×) — 4 API categories + 1 LLM synthesis call | Higher (≈3–4× baseline) — 8 API categories + UBO/director fan-out + 1 LLM synthesis call |
| Typical use case | Fast triage on a new or low-value vendor | Onboarding decision for a high-value or long-term vendor |
| Re-runnable on same input? | Yes, any time | Yes, any time — including immediately after a Quick Scan, with no new data entry |

> Exact dollar costs per scan depend on per-vendor API pricing tiers and are tracked as an open item in Section 11 (e.g., OpenCorporates and Google CSE volume pricing). The relative multiplier above is the planning figure until Finance confirms contracted rates.

### 2.2 User Journey — Manual Intake → Quick Scan → Upgrade to Deep Diligence Later

```
1. User navigates to /new-vendor
2. Fills the single intake form: "Apex Trading LLC" + "apextrading.com"
   (the only two required fields), plus whatever else is on hand —
   registration number, director names, social handles, etc. — all
   optional at this step
3. Clicks "Save Vendor" → system returns an input_id; no scan has
   run yet, nothing has been screened
4. User clicks "Run Quick Scan" on that saved vendor
5. Frontend shows progress tracker:
   [Entity Check ✓] [Sanctions ✓] [Domain Check...] [News Scan...]
6. Results render in ~3 min: Entity card, Sanctions card, Domain
   anomaly card, Top 5 adverse news snippets, Overall risk badge
7. User downloads a PDF summary, OR clicks "Run Deep Diligence on
   this vendor" — no new form, no re-upload; the system reuses the
   same input_id and simply runs the remaining categories
```

### 2.3 User Journey — Excel Intake → Deep Diligence Directly (with OCR Enrichment)

```
1. User downloads VendorLens_Intake_Template.xlsx
2. Fills one row with everything known about the vendor: legal name,
   domain, registration number, tax ID, address, director
   names/DINs, social handles, corporate email domain
3. Uploads the file at /new-vendor → system parses it, validates
   required columns, and returns an input_id — no manual typing
4. User reviews the auto-populated summary, optionally attaches a
   GST certificate so OCR can cross-check or fill any still-empty
   field, then clicks "Run Deep Diligence"
5. System runs the full pipeline (12–15 min) using only the data
   captured in step 2 — nothing is asked twice
6. Results page shows: corporate structure tree (entity → directors
   → UBOs), per-subject risk cards, full adverse findings table
   (filterable by severity/category), contamination path for each
   finding, Excel export button
7. All adverse findings are stored in DB; clean signals are
   discarded; the vendor's input_id remains saved for any future
   re-screen (Quick or Deep) without re-uploading anything
```

---

## 3. Product Requirements & Input Schema

### 3.1 Input Categories & Data Dictionary

All four categories below are presented in **one** intake step (Section 2.1, Step A) — either as one manual form or as one Excel upload. Category 1 is mandatory to save an intake at all; Categories 2–4 are optional at intake time but determine how much of the pipeline a later **Deep Diligence** run can actually execute (see 3.5).

#### Category 1 — Primary Identifiers (Required at intake; used by both Quick Scan and Deep Diligence)

| Field | Format | Validation | API Triggered |
|---|---|---|---|
| `legal_name` | String, 2–200 chars | Non-empty, strip legal suffixes for search | OpenCorporates, GLEIF, GDELT, NewsAPI, OpenSanctions |
| `website_domain` | String (domain only, no protocol) | Regex: `^[a-zA-Z0-9][a-zA-Z0-9\-]{1,61}\.[a-zA-Z]{2,}$` | WHOIS API, SSL Labs, VirusTotal (domain) |

#### Category 2 — Regulatory & Corporate Identifiers (Optional at intake; used only when the user selects Deep Diligence)

| Field | Format | Examples | API Triggered |
|---|---|---|---|
| `registration_number` | Alphanumeric | CIN (IN), EIN (US), CRN (UK), HRB (DE) | OpenCorporates `/companies/search`, MCA, Companies House |
| `jurisdiction_country` | ISO 3166-1 alpha-2 | `IN`, `US`, `GB`, `AE` | Determines which registry API to call |
| `tax_identifier` | Alphanumeric | GSTIN, PAN, VAT, TIN | Country-specific: GST API (IN), VIES (EU) |
| `registered_address` | Full address string | "123 Trade Tower, Mumbai 400001" | Google Geocoding API + Places API (shell company cluster detection) |

#### Category 3 — Key Personnel & Leadership (Optional at intake; used only when the user selects Deep Diligence)

| Field | Format | Notes | API Triggered |
|---|---|---|---|
| `director_names` | Array of strings | Up to 10 directors | OpenSanctions, GDELT, OpenOwnership |
| `director_din` | Array of alphanumeric | DIN (India-specific) | MCA DIN lookup, cross-entity risk check |
| `founder_ceo_name` | String | Primary individual for PEP check | OpenSanctions PEP dataset, Wikidata SPARQL |

#### Category 4 — Digital Footprint (Optional at intake; used only when the user selects Deep Diligence)

| Field | Format | Notes | API Triggered |
|---|---|---|---|
| `social_handles` | Object `{platform: handle}` | LinkedIn, Twitter/X, Facebook | Platform public APIs or SERP API scrape |
| `corporate_email_domain` | String | `@acmesolutions.com` | MX record check; flag if `@gmail.com` / `@outlook.com` |
| `ocr_documents` | File array (PDF/JPG/PNG) | GST cert, invoice, trade license — **not** part of the Excel template (binary files can't live in spreadsheet cells); always a separate, optional upload control alongside either intake path | Internal Tesseract/AWS Textract OCR pipeline |

### 3.2 Unified Intake — Manual Form

A single page/wizard exposes every field from Categories 1–4 at once. There is no gating between sections: a user can skip straight to Category 4 without filling Category 2 first. Only `legal_name` and `website_domain` are marked required; everything else is "optional now, needed later if you want Deep Diligence." Submitting the form produces one `VendorInputRecord` and an `input_id` — no scan runs yet.

### 3.3 Unified Intake — Excel Upload Template Schema

Users who already track vendor data in a spreadsheet can skip the form entirely and upload `VendorLens_Intake_Template.xlsx`. The template is a single sheet, `Vendor_Intake`, with one header row and **one data row per vendor** (v1.0 scope — see Section 10 for multi-row batch as a future enhancement). Array-valued fields are encoded as semicolon-delimited text in a single cell so the template stays one row wide; the parser splits them back into arrays during ingestion.

| Excel Column Header | Maps to Field | Category | Required in Template? | Encoding Notes |
|---|---|---|---|---|
| `legal_name` | `legal_name` | 1 | Yes | Plain text |
| `website_domain` | `website_domain` | 1 | Yes | No protocol, e.g. `apextrading.com` |
| `registration_number` | `registration_number` | 2 | No | Plain text |
| `jurisdiction_country` | `jurisdiction_country` | 2 | No | ISO 3166-1 alpha-2; template ships with a data-validation dropdown |
| `tax_identifier` | `tax_identifier` | 2 | No | Plain text |
| `registered_address` | `registered_address` | 2 | No | Single-line full address |
| `director_names` | `director_names` | 3 | No | Semicolon-separated, e.g. `Jane Doe; Ahmed Al-Rashid` |
| `director_din` | `director_din` | 3 | No | Semicolon-separated, same order as `director_names` |
| `founder_ceo_name` | `founder_ceo_name` | 3 | No | Plain text |
| `linkedin_handle` | `social_handles.linkedin` | 4 | No | Handle or profile slug only |
| `twitter_handle` | `social_handles.twitter` | 4 | No | Handle without `@` |
| `facebook_handle` | `social_handles.facebook` | 4 | No | Page slug |
| `corporate_email_domain` | `corporate_email_domain` | 4 | No | e.g. `@acmesolutions.com` |

The three social columns are flattened (rather than a single JSON cell) so the template stays spreadsheet-friendly; the parser reassembles them into the `social_handles` object on ingestion. `ocr_documents` has no column — supporting documents are attached as a separate file upload alongside the Excel file, not embedded in it.

### 3.4 Internal Normalization — One Schema, Two Entry Paths

Whichever path the user takes, both resolve to the same internal object before anything touches the orchestration layer, so downstream code never needs to know whether a vendor came in by hand or by spreadsheet:

```python
# app/schemas/vendor_input.py
from pydantic import BaseModel
from typing import Optional, Literal

class VendorInputRecord(BaseModel):
    legal_name: str
    website_domain: str
    registration_number: Optional[str] = None
    jurisdiction_country: Optional[str] = None
    tax_identifier: Optional[str] = None
    registered_address: Optional[str] = None
    director_names: list[str] = []
    director_din: list[str] = []
    founder_ceo_name: Optional[str] = None
    social_handles: dict[str, str] = {}
    corporate_email_domain: Optional[str] = None
    source_method: Literal["manual", "excel"]
    source_filename: Optional[str] = None   # original .xlsx name, if applicable

    def has_deep_fields(self) -> bool:
        """True if at least one Category 2–4 field was captured at intake."""
        return any([
            self.registration_number, self.jurisdiction_country,
            self.tax_identifier, self.registered_address,
            self.director_names, self.founder_ceo_name,
            self.social_handles, self.corporate_email_domain,
        ])

    def missing_deep_fields(self) -> list[str]:
        """Used to populate data_quality_notes when Deep Diligence runs on a partial intake."""
        checks = {
            "registration_number": self.registration_number,
            "registered_address": self.registered_address,
            "director_names": self.director_names,
            "social_handles": self.social_handles,
        }
        return [name for name, value in checks.items() if not value]
```

### 3.5 Partial Input Handling for Deep Diligence

Because intake is decoupled from scan depth, a user can request Deep Diligence on a vendor whose intake only ever filled Category 1. The platform does **not** block this — it runs every category for which data exists and records the gap instead of erroring out:

- If `has_deep_fields()` is `False`, Deep Diligence behaves identically to a Quick Scan for this run, and `data_quality_notes` in the LLM output (Section 6.1) records *"Deep Diligence requested but no Category 2–4 data was captured at intake — director/UBO/address/digital-footprint checks skipped."*
- If some but not all Category 2–4 fields are present, only the corresponding tasks fire (e.g., directors were given but no address → director screening runs, address verification is skipped and noted).
- The UI surfaces this as a banner: *"This report is based on partial data. Add registration number, address, or directors to your saved intake for a fuller Deep Diligence."* — with a link back to the same saved `input_id` so the user edits the existing record rather than starting over.

### 3.6 Field-to-API Mapping Matrix

```
INPUT FIELD              │ PRIMARY API           │ FALLBACK            │ RISK SIGNAL
─────────────────────────┼───────────────────────┼─────────────────────┼──────────────────────
legal_name               │ OpenCorporates        │ GLEIF               │ Not found = unverified
legal_name               │ OpenSanctions         │ OFAC XML            │ Match = CRITICAL
legal_name               │ GDELT + NewsAPI       │ Google CSE          │ Negative tone articles
website_domain           │ WHOIS API             │ —                   │ Age < claimed = RED FLAG
website_domain           │ SSL Labs API          │ —                   │ No SSL / expired = MEDIUM
registration_number      │ OpenCorporates direct │ Country registry    │ Dissolved = HIGH
tax_identifier           │ GST/VAT verify API    │ —                   │ Inactive = HIGH
registered_address       │ Google Geocoding      │ —                   │ Known shell address = HIGH
director_names           │ OpenSanctions PEP     │ Wikidata SPARQL     │ PEP status = REVIEW
director_names           │ GDELT + Google CSE    │ NewsAPI             │ Adverse media = HIGH
director_din             │ MCA API (India)       │ —                   │ Linked to defaulted cos
social_handles           │ Platform APIs / SERP  │ —                   │ Bot inflation, complaints
corporate_email_domain   │ MX lookup (DNS)       │ —                   │ Free email = MEDIUM flag
```

---

## 4. System Architecture & Tech Stack

### 4.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  React 18 + TypeScript                                           │
│  Unified Intake (Form | Excel) · Scan-Depth Selector · Dashboard │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS / REST
┌──────────────────────────▼───────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  FastAPI (Python 3.11+)                                          │
│  /vendor/intake   /scan   /scan/{id}/status   /scan/{id}/report  │
└──────┬──────────────────────────────────────────────┬───────────┘
       │ Step A — intake (once)            Step B — scan (per run) │
┌──────▼──────────────────┐                  ┌─────────▼──────────┐
│  INTAKE INGESTION       │  writes ONE       │   TASK QUEUE       │
│  Excel parser           │  VendorInput      │  Celery + Redis    │
│  (pandas/openpyxl)      │  Record to        │                    │
│  Manual form validator  │  vendor_inputs,   │  slow_queue:       │
│  OCR pipeline           │  reused by every  │  - SpiderFoot      │
│  (Tesseract / AWS       │  scan below ────► │  - Maigret         │
│  Textract) — optional   │                   │  fast_queue:       │
│  enrichment only        │                   │  - HIBP / WHOIS    │
└──────────────────────────┘                  │  - NewsAPI / GDELT │
                                              │  - OpenSanctions    │
                                              └─────────┬───────────┘
                                                        │
┌───────────────────────────────────────────────────────▼──────────┐
│                  EXTERNAL API INTEGRATION LAYER                  │
│                                                                  │
│  Entity:      OpenCorporates │ GLEIF │ Companies House           │
│  Sanctions:   OpenSanctions  │ OFAC XML │ UN Consolidated List   │
│  Domain:      WHOIS API      │ SSL Labs │ VirusTotal             │
│  News/Media:  GDELT          │ NewsAPI  │ Google CSE             │
│  Ownership:   OpenOwnership  │ UK PSC   │ GLEIF L2               │
│  PEP:         OpenSanctions PEP dataset │ Wikidata SPARQL        │
│  Address:     Google Geocoding + Places                          │
└──────┬──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                      LLM SYNTHESIS LAYER                         │
│  Anthropic Claude / OpenAI GPT-4o                               │
│  Input: Merged raw JSON from all API calls                       │
│  Output: Structured adverse_findings JSON                        │
└──────┬──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                      DATA PERSISTENCE LAYER                      │
│  PostgreSQL 15                                                   │
│  STORE ONLY NEGATIVES pattern                                    │
│  Tables: vendor_inputs │ kyb_scans │ adverse_findings │ scan_subjects │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack Specification

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Frontend | React + TypeScript | 18.x | Component-based, typed, strong ecosystem |
| UI Components | shadcn/ui + Tailwind CSS | Latest | Rapid, consistent, accessible UI |
| State Management | TanStack Query | v5 | Server state / polling scan status |
| Backend Framework | FastAPI | 0.111+ | Async-first, auto OpenAPI docs, Python 3.11 |
| Task Queue | Celery | 5.3+ | Distributed task execution, chord/group support |
| Message Broker | Redis | 7.x | Celery broker + result backend + scan status |
| Database | PostgreSQL | 15.x | JSONB for raw data, relational for findings |
| ORM | SQLAlchemy 2.0 + Alembic | Latest | Async ORM + migrations |
| Spreadsheet Parsing | pandas + openpyxl | Latest | Parses the Excel intake template into a VendorInputRecord |
| OCR | Tesseract 5 + pytesseract | Latest | Local OCR; AWS Textract as fallback — optional enrichment only |
| HTTP Client | httpx | 0.27+ | Async HTTP with proxy support |
| LLM | Anthropic Claude API | claude-sonnet | Structured JSON output via tool use |
| Proxy Layer | Oxylabs Residential | — | For Maigret / Holehe anti-block |
| Monitoring | Flower + Sentry | Latest | Task monitoring + error tracking |
| Containerization | Docker + Docker Compose | Latest | Reproducible environments |

### 4.3 Backend 3-Step Core Workflow (Code Architecture)

#### Step 1 — Data Ingestion (Intake Layer + Orchestration Layer)

```python
# fastapi/routers/intake.py
# Single intake endpoint — runs ONCE per vendor, regardless of which
# scan depth is requested later. Accepts either a manual form payload
# or an Excel upload; both normalize to the same VendorInputRecord.

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.vendor_input import VendorInputRecord
from app.intake.excel_parser import parse_vendor_excel
import uuid

router = APIRouter()

@router.post("/vendor/intake")
async def create_intake(
    excel_file: UploadFile | None = File(default=None),
    manual_fields: VendorInputRecord | None = Form(default=None),
):
    if excel_file is not None:
        record = await parse_vendor_excel(excel_file)
    elif manual_fields is not None:
        record = manual_fields
    else:
        raise HTTPException(400, "Provide either excel_file or manual_fields")

    input_id = str(uuid.uuid4())
    await db.save_vendor_input(input_id, record)

    return {
        "input_id": input_id,
        "source_method": record.source_method,
        "deep_diligence_ready": record.has_deep_fields(),
    }
```

```python
# fastapi/routers/scan.py
# Single /scan endpoint — input was already captured at /vendor/intake.
# scan_type only decides WHICH tasks fire against that same stored
# record; it never asks the user for data again.

from fastapi import APIRouter, HTTPException
from celery import chord, group
from app.tasks import (
    verify_entity_task, check_sanctions_task,
    check_domain_task, scan_adverse_media_task,
    resolve_ubo_task, screen_directors_task,
    verify_address_task, check_social_footprint_task,
    synthesize_findings_task
)
import uuid

router = APIRouter()

QUICK_SCAN_TASKS = [verify_entity_task, check_sanctions_task,
                    check_domain_task, scan_adverse_media_task]
DEEP_DILIGENCE_TASKS = QUICK_SCAN_TASKS + [
    resolve_ubo_task, screen_directors_task,
    verify_address_task, check_social_footprint_task,
]

@router.post("/scan")
async def run_scan(payload: ScanRequest):  # {input_id, scan_type: "quick"|"deep"}
    record = await db.get_vendor_input(payload.input_id)
    if record is None:
        raise HTTPException(404, "Unknown input_id — call /vendor/intake first")

    scan_id = str(uuid.uuid4())
    tasks = DEEP_DILIGENCE_TASKS if payload.scan_type == "deep" else QUICK_SCAN_TASKS

    if payload.scan_type == "deep" and not record.has_deep_fields():
        # Don't block — run what's available and flag the gap (Section 3.5)
        await db.flag_partial_deep_diligence(scan_id, record.missing_deep_fields())

    task_group = group(t.s(record, scan_id) for t in tasks)
    workflow = chord(task_group)(
        synthesize_findings_task.s(scan_id, payload.scan_type)
    )
    workflow.apply_async()

    await db.set_scan_status(scan_id, "RUNNING")
    return {
        "scan_id": scan_id, "input_id": payload.input_id,
        "status": "RUNNING", "scan_type": payload.scan_type,
    }


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    return await db.get_scan_status(scan_id)


@router.get("/scan/{scan_id}/report")
async def get_report(scan_id: str, format: str = "json"):
    findings = await db.get_adverse_findings(scan_id)
    if format == "excel":
        return generate_excel_response(findings)
    return findings
```

#### Step 2 — AI Analysis (NLP Layer)

```python
# app/tasks/synthesize.py

@celery_app.task
def synthesize_findings_task(parallel_results: list, scan_id: str, scan_type: str):
    """
    Called by Celery chord after ALL parallel tasks complete.
    parallel_results is a list of dicts, one per tool.
    scan_type ("quick" | "deep") only affects which tools ran upstream —
    by this point it's just a label for the report header.
    """
    # Merge all tool outputs into one JSON blob
    merged_raw = {}
    for result in parallel_results:
        if result and "tool" in result:
            merged_raw[result["tool"]] = result["data"]
    
    # Call LLM with system prompt (see Section 6)
    adverse_findings = call_llm_synthesis(merged_raw, scan_id, scan_type)
    
    # STORE ONLY NEGATIVES — write only adverse findings
    if adverse_findings["adverse_findings"]:
        db.bulk_insert_findings(scan_id, adverse_findings["adverse_findings"])
    
    # Always update scan summary
    db.update_scan_summary(
        scan_id=scan_id,
        risk_level=adverse_findings["risk_summary"]["overall_risk_level"],
        total_findings=adverse_findings["risk_summary"]["total_adverse_findings"]
    )
    
    return scan_id
```

#### Step 3 — Output & Reporting

```python
# app/reports/excel_generator.py
import pandas as pd
from openpyxl.styles import PatternFill, Font

def generate_excel_report(scan_id: str, findings: list[dict]) -> bytes:
    COLOR_MAP = {
        "CRITICAL": "FF0000",
        "HIGH":     "FF6600", 
        "MEDIUM":   "FFCC00",
        "LOW":      "99CC00",
    }
    
    df = pd.DataFrame(findings)
    
    with pd.ExcelWriter("/tmp/report.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Adverse Findings", index=False)
        ws = writer.sheets["Adverse Findings"]
        
        # Color-code rows by severity
        for row_idx, finding in enumerate(findings, start=2):
            color = COLOR_MAP.get(finding["severity"], "FFFFFF")
            for col_idx in range(1, len(df.columns) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = \
                    PatternFill("solid", fgColor=color)
    
    with open("/tmp/report.xlsx", "rb") as f:
        return f.read()
```

---

## 5. API Integration Specifications

### 5.1 Entity Verification APIs

#### OpenCorporates API
```
Endpoint:  GET https://api.opencorporates.com/v0.4/companies/search
Params:    q={legal_name}&jurisdiction_code={ISO}&api_token={key}
Response:  {companies: [{company: {company_number, name, jurisdiction_code,
                         current_status, incorporation_date, registered_address,
                         officers: [...], filings: [...]}}]}
Risk signals:
  - current_status = "Dissolved" or "Struck Off" → HIGH
  - incorporation_date < 1 year ago → MEDIUM (new entity)
  - registered_address matches known shell cluster → HIGH
```

#### GLEIF (Global LEI)
```
Endpoint:  GET https://api.gleif.org/api/v1/fuzzycompletions?field=fullLegalName&q={name}
           GET https://api.gleif.org/api/v1/lei-records/{lei}  (for ownership data)
Response:  {data: [{attributes: {lei, entity: {legalName, legalAddress,
                   registeredAt, status, entityCategory}}}]}
Risk signals:
  - status = "LAPSED" → company stopped maintaining LEI → MEDIUM
  - entityCategory = "BRANCH" → may be non-independent → flag for review
```

### 5.2 Sanctions & Watchlist API

#### OpenSanctions (Primary Sanctions Source)
```
Endpoint:  GET https://api.opensanctions.org/match/default
Method:    POST
Body:      {"queries": {"q1": {"schema": "Company", "properties": 
                               {"name": ["{legal_name}"]}}}}
Headers:   Authorization: ApiKey {key}
Response:  {responses: {q1: {results: [{id, caption, schema, score,
                              datasets: ["us_ofac_sdn", "un_sc_sanctions"],
                              properties: {name, birthDate, nationality,
                                           program, sanctionedFrom}}]}}}
Risk signals:
  - score > 0.85 → HIGH confidence match → CRITICAL finding
  - score 0.60–0.85 → possible match → REQUIRES_REVIEW
  - datasets includes "us_ofac_sdn" or "un_sc_sanctions" → CRITICAL
  - datasets includes "eu_fsf" or "gb_hmt" → HIGH
```

### 5.3 Domain Intelligence APIs

#### WHOIS API
```
Endpoint:  GET https://www.whoisxmlapi.com/whoisserver/WhoisService
Params:    domainName={domain}&apiKey={key}&outputFormat=JSON
Response:  {WhoisRecord: {createdDate, updatedDate, expiresDate,
                          registrantContact, administrativeContact,
                          registrarName, domainAvailability,
                          registryData: {dnsSec}}}
Risk signals:
  - createdDate < 1 year ago + company claims 5+ years experience → CRITICAL
  - registrantContact.email is privacy-masked + no SSL → HIGH
  - domainAvailability = "AVAILABLE" → domain doesn't exist → HIGH
```

#### SSL Labs / Certificate Check
```
Endpoint:  GET https://api.ssllabs.com/api/v3/analyze?host={domain}&all=done
Risk signals:
  - No HTTPS response → MEDIUM
  - Certificate expired → MEDIUM  
  - Grade F or T → HIGH (trust error / self-signed)
```

### 5.4 Adverse Media APIs

#### GDELT 2.0 (Free, No Key Required)
```
Endpoint:  GET https://api.gdeltproject.org/api/v2/doc/doc
Params:    query="{name}" (fraud OR corruption OR lawsuit OR arrested OR sanctioned)
           &mode=artlist&maxrecords=250&format=json&sort=DateDesc
Response:  {articles: [{url, title, seendate, domain, language, 
                        sourcecountry, tone, negative_score}]}
Risk signals:
  - tone < -5.0 → strongly adverse coverage
  - title contains name + legal keyword → flag
  - sourcecountry can flag jurisdiction-specific legal issues
```

#### NewsAPI
```
Endpoint:  GET https://newsapi.org/v2/everything
Params:    q="{name}" AND (fraud OR scam OR arrested OR convicted OR lawsuit)
           &from=2015-01-01&sortBy=relevancy&pageSize=100
Headers:   X-Api-Key: {key}
Risk signals:
  - totalResults > 0 for adverse query → investigate articles
  - source.id from tier-1 outlets (reuters, ap, bbc) → higher confidence
```

#### Google Programmable Search Engine
```
Endpoint:  GET https://www.googleapis.com/customsearch/v1
Params:    key={key}&cx={cx_id}&q="{name}" (site:courtlistener.com OR 
           site:sec.gov OR site:justice.gov OR site:ofac.treas.gov)
           &num=10
Risk signals:
  - Any result from court/regulatory domains → HIGH-CRITICAL
  - "v." pattern in title (Name v. Agency) → litigation finding
```

### 5.5 Beneficial Ownership & Director APIs

#### OpenOwnership (BODS Standard)
```
Endpoint:  GET https://register.openownership.org/entities?q={name}
Response:  {results: [{identifier, name, type, relationships: 
                       [{entity, ownership_percentage, start_date}]}]}
Risk signals:
  - UBO in high-risk jurisdiction (FATF blacklist) → HIGH
  - Circular ownership detected → shell company flag → CRITICAL
  - Nominee director pattern (same director on 50+ companies) → HIGH
```

#### UK Companies House (Free, Global Model)
```
Endpoint:  GET https://api.company-information.service.gov.uk/search/companies?q={name}
           GET https://api.company-information.service.gov.uk/company/{number}/officers
Headers:   Authorization: Basic {base64(api_key:)}
Risk signals:
  - company_status = "dissolved" → HIGH
  - Officer with significant_control = true → screen that individual
  - Filing date gaps > 2 years → compliance failure → MEDIUM
```

### 5.6 Address Verification API (Shell Company Detection)

#### Google Geocoding + Places
```
Geocoding:  GET https://maps.googleapis.com/maps/api/geocode/json
            ?address={registered_address}&key={key}

Places:     GET https://maps.googleapis.com/maps/api/place/details/json
            ?place_id={id}&fields=name,types,rating,user_ratings_total&key={key}

Risk signals:
  - place types = ["establishment"] but no business name → suspicious
  - Address resolves to known registered-agent mass-address clusters
    (maintain a blocklist: e.g., "1209 Orange St, Wilmington DE" = 285,000 companies)
  - Street View API returns residential building for claimed commercial HQ → MEDIUM
```

### 5.7 Document OCR Pipeline (Optional Enrichment)

This pipeline is **not** a separate input tier — it is an optional convenience that fills gaps in the single unified intake (manual form or Excel) whenever the user attaches a supporting document. Its output merges into the same `VendorInputRecord`, never a separate record.

```python
# app/ocr/extractor.py
import pytesseract
from PIL import Image
import anthropic
import pdf2image

def extract_entities_from_document(file_bytes: bytes, mime_type: str) -> dict:
    """
    Converts uploaded document → text → LLM entity extraction
    """
    # Convert PDF to images if needed
    if mime_type == "application/pdf":
        images = pdf2image.convert_from_bytes(file_bytes, dpi=300)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
    else:
        img = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(img)
    
    # Use LLM to extract structured entities from raw OCR text
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Extract all business entities from this OCR text.
Output ONLY JSON: {{
  "legal_name": "...",
  "registration_number": "...",
  "tax_identifier": "...",
  "registered_address": "...",
  "directors": ["..."],
  "registration_date": "YYYY-MM-DD or null",
  "issuing_authority": "..."
}}
OCR TEXT:
{text}"""
        }]
    )
    
    return json.loads(message.content[0].text)
```

### 5.8 Excel Intake Parser

Parses `VendorLens_Intake_Template.xlsx` (Section 3.3) into the same `VendorInputRecord` used by the manual form, validates required columns, and splits semicolon-delimited array fields.

```python
# app/intake/excel_parser.py
import pandas as pd
from app.schemas.vendor_input import VendorInputRecord

REQUIRED_COLUMNS = ["legal_name", "website_domain"]
SOCIAL_COLUMNS = {
    "linkedin_handle": "linkedin",
    "twitter_handle": "twitter",
    "facebook_handle": "facebook",
}

async def parse_vendor_excel(file) -> VendorInputRecord:
    df = pd.read_excel(file.file, sheet_name="Vendor_Intake", dtype=str).fillna("")

    if df.empty:
        raise ValueError("Excel template has no data row")
    row = df.iloc[0]  # v1.0: exactly one vendor per upload

    for col in REQUIRED_COLUMNS:
        if not row.get(col, "").strip():
            raise ValueError(f"Excel template missing required column: {col}")

    return VendorInputRecord(
        legal_name=row["legal_name"].strip(),
        website_domain=row["website_domain"].strip().lower(),
        registration_number=row.get("registration_number") or None,
        jurisdiction_country=row.get("jurisdiction_country") or None,
        tax_identifier=row.get("tax_identifier") or None,
        registered_address=row.get("registered_address") or None,
        director_names=_split_list(row.get("director_names")),
        director_din=_split_list(row.get("director_din")),
        founder_ceo_name=row.get("founder_ceo_name") or None,
        social_handles={
            mapped: row[col] for col, mapped in SOCIAL_COLUMNS.items() if row.get(col)
        },
        corporate_email_domain=row.get("corporate_email_domain") or None,
        source_method="excel",
        source_filename=file.filename,
    )

def _split_list(cell: str) -> list[str]:
    return [v.strip() for v in cell.split(";") if v.strip()] if cell else []
```

---

## 6. AI/ML & NLP Specifications

### 6.1 LLM System Prompt — KYB Adverse Findings Extraction

```
SYSTEM PROMPT — KYB DUE DILIGENCE ANALYST v1.0
===============================================

You are an expert corporate due diligence and KYB (Know Your Business) analyst. 
You will receive a raw JSON object containing data collected about a vendor entity 
from multiple public intelligence sources.

YOUR ONLY TASKS:
1. Extract ADVERSE findings only — signals indicating legal risk, financial risk, 
   reputational risk, sanctions exposure, or fraudulent behavior.
2. Ignore neutral or positive signals. Do not report that a company "was found" 
   in a registry — only report if the finding is adverse.
3. Normalize and deduplicate across sources.
4. Assess the corporate structure risk (entity + directors + UBOs as a whole).
5. Output ONLY valid JSON — no preamble, no explanation, no markdown backticks.

─────────────────────────────────────────────────────
INPUT DATA SCHEMA (what you will receive):
─────────────────────────────────────────────────────
{
  "subject": {
    "legal_name": "string",
    "domain": "string",
    "jurisdiction": "string",
    "scan_type": "quick | deep",
    "input_source": "manual | excel"
  },
  "entity_verification": {
    "opencorporates": {...},
    "gleif": {...},
    "companies_house": {...}
  },
  "sanctions": {
    "opensanctions_entity": [...],
    "opensanctions_directors": {...},
    "ofac_raw": {...}
  },
  "domain_intelligence": {
    "whois": {...},
    "ssl_check": {...}
  },
  "adverse_media": {
    "gdelt": {articles: [...]},
    "newsapi": {articles: [...]},
    "google_cse": [...]
  },
  "beneficial_ownership": {
    "openownership": {...},
    "uk_psc": {...}
  },
  "address_verification": {
    "geocoding": {...},
    "places": {...}
  },
  "director_screening": [
    {"name": "...", "sanctions": [...], "pep": {...}, "media": [...]}
  ]
}

─────────────────────────────────────────────────────
ADVERSE CLASSIFICATION RULES:
─────────────────────────────────────────────────────

SANCTIONS (Always CRITICAL if confirmed):
- Entity name match on OFAC SDN, UN Consolidated, EU FSF, UK OFSI → CRITICAL
- Match score > 0.85 on OpenSanctions → CRITICAL
- Match score 0.60–0.85 → HIGH (report as "Possible Match — Human Review Required")
- Director or UBO on any sanctions list → CRITICAL (contamination)

ENTITY INTEGRITY:
- Company status = Dissolved / Struck Off / Liquidation → HIGH
- Company incorporated < 12 months ago AND high-value contract context → MEDIUM
- No LEI record found for company claiming international operations → MEDIUM
- Registered address = known mass-registration shell address → HIGH
- Director listed as nominee on > 30 other companies → HIGH (nominee red flag)
- Circular ownership detected → CRITICAL (shell company structure)
- UBO resides in FATF blacklisted jurisdiction → HIGH

DOMAIN INTELLIGENCE:
- Domain age < company claimed age by > 2 years → HIGH
  (e.g., company says "founded 2010" but domain registered 2022)
- No valid SSL certificate or expired SSL on commercial domain → MEDIUM
- Domain registrant privacy-masked with no verifiable contact → MEDIUM
- Domain not found / not registered → HIGH

ADVERSE MEDIA — apply ALL of the following:
- Only flag articles where subject's legal name appears in title or first 
  paragraph combined with a legal/crime keyword
- Acceptable legal keywords: fraud, bribery, corruption, money laundering, 
  embezzlement, arrested, convicted, indicted, sued, sanction, debarred, 
  investigation, default, insolvency, Ponzi
- GDELT tone < -5.0 combined with legal keyword → HIGH
- GDELT tone < -3.0 combined with legal keyword → MEDIUM
- Source from tier-1 outlet (Reuters, AP, BBC, Bloomberg, FT) → confidence +2
- Deduplicate articles covering the same event (cluster by title similarity)
- Reject articles from low-authority domains (DA < 30 equivalent, SEO farms)
- Only include articles dated within last 10 years; weight last 3 years higher

COURT & REGULATORY RECORDS (from Google CSE):
- Result from courtlistener.com, pacer.gov, sec.gov/litigation, 
  justice.gov, ofac.treas.gov, interpol.int → CRITICAL
- Result from any country's financial regulator or court domain → HIGH
- Distinguish: company as DEFENDANT → adverse; company as PLAINTIFF → neutral

FINANCIAL / TAX RED FLAGS:
- Tax identifier inactive or deregistered → HIGH
- GST/VAT registration lapsed → MEDIUM
- No public financial filings for company > 3 years old → MEDIUM

PEOPLE / PEP:
- Director or UBO confirmed PEP (Politically Exposed Person) → REQUIRES_REVIEW
  (Not itself adverse, but must be flagged for enhanced due diligence)
- Director adverse media (same rules as entity above) → HIGH, contaminate entity

─────────────────────────────────────────────────────
CONFIDENCE SCORING (assign to every finding):
─────────────────────────────────────────────────────
10  — Official government source, verified breach DB, court record
8-9 — Tier-1 news outlet, official registry, OpenSanctions verified dataset
6-7 — Tier-2 news outlet, unverified breach, minor regulatory body
4-5 — Single-source, forum/social media, circumstantial
1-3 — Weak signal, speculative, no corroboration

─────────────────────────────────────────────────────
DEDUPLICATION RULES:
─────────────────────────────────────────────────────
- Same event in GDELT + NewsAPI → merge into one finding, list both sources
- Same sanctions list entry appearing in OpenSanctions + OFAC XML → report once
- Same director adverse finding from multiple media sources → one finding, 
  list all source URLs in evidence array

─────────────────────────────────────────────────────
OUTPUT SCHEMA (strict — output this exact structure):
─────────────────────────────────────────────────────
{
  "subject": {
    "legal_name": "string",
    "domain": "string",
    "scan_timestamp": "ISO8601",
    "scan_type": "quick | deep"
  },
  "risk_summary": {
    "overall_risk_level": "CRITICAL | HIGH | MEDIUM | LOW | CLEAN",
    "total_adverse_findings": integer,
    "findings_by_category": {
      "sanctions_watchlist": integer,
      "entity_integrity": integer,
      "adverse_media": integer,
      "court_regulatory": integer,
      "domain_anomaly": integer,
      "director_ubo_risk": integer,
      "financial_tax": integer
    },
    "requires_human_review": true | false
  },
  "adverse_findings": [
    {
      "finding_id": "F001",
      "subject_type": "ENTITY | DIRECTOR | UBO | RELATED_ENTITY",
      "subject_name": "exact name that triggered the finding",
      "contamination_path": "Apex Trading LLC → Director → Ahmed Al-Rashid → OFAC SDN",
      "category": "sanctions_watchlist | entity_integrity | adverse_media | 
                   court_regulatory | domain_anomaly | director_ubo_risk | financial_tax",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "confidence_score": 1-10,
      "title": "one-line concise description (max 100 chars)",
      "detail": "2-3 sentence factual summary — no speculation, no invention",
      "evidence": {
        "source_tool": "opensanctions | opencorporates | gdelt | newsapi | 
                        google_cse | whois | gleif | openownership",
        "source_urls": ["url1", "url2"],
        "source_name": "OFAC SDN List / Reuters / CourtListener",
        "finding_date": "YYYY-MM-DD or null",
        "raw_excerpt": "verbatim key field from raw input, max 300 chars"
      },
      "excel_flags": {
        "highlight_color": "RED | ORANGE | YELLOW | GREEN",
        "requires_human_review": true | false,
        "recommended_action": "Block | Escalate | Monitor | Flag"
      }
    }
  ],
  "credibility_concerns": [
    "string — factual credibility gap (e.g., domain age vs claimed founding year)"
  ],
  "fraud_risk_indicators": [
    "string — specific fraud signals (e.g., nominee directors, shell address)"
  ],
  "operational_grey_areas": [
    "string — ambiguous findings needing human judgment (e.g., PEP director)"
  ],
  "data_quality_notes": [
    "string — APIs that returned no data, rate limit errors, coverage gaps, or Category 2–4 fields missing from intake (see Section 3.5)"
  ]
}

─────────────────────────────────────────────────────
ABSOLUTE RULES:
─────────────────────────────────────────────────────
- Output ONLY the JSON object. No markdown, no explanation, no code fences.
- NEVER invent or hallucinate findings. Only extract from provided input data.
- NEVER include findings where the subject's name does not appear in the source data.
- If zero adverse findings: set overall_risk_level = "CLEAN", adverse_findings = [].
- Cap output at 50 findings max — prioritize by severity DESC, then recency DESC.
- Never include raw passwords, personal financial data, or PII beyond name/email.
- PEP status alone is NOT adverse — flag in operational_grey_areas only.
```

### 6.2 Entity Resolution Logic

Before passing data to the LLM, the backend performs entity resolution to canonicalize names across sources:

```python
# app/intelligence/entity_resolver.py

import re
from difflib import SequenceMatcher

LEGAL_SUFFIXES = [
    r"\bPvt\.?\s*Ltd\.?\b", r"\bLimited\b", r"\bLtd\.?\b",
    r"\bLLC\b", r"\bInc\.?\b", r"\bCorp\.?\b", r"\bGmbH\b",
    r"\bS\.?A\.?\b", r"\bB\.?V\.?\b", r"\bPte\.?\s*Ltd\.?\b"
]

def normalize_company_name(name: str) -> str:
    """Strip legal suffixes and punctuation for fuzzy matching"""
    name = name.upper().strip()
    for suffix in LEGAL_SUFFIXES:
        name = re.sub(suffix, "", name, flags=re.IGNORECASE)
    name = re.sub(r"[^\w\s]", "", name)
    return " ".join(name.split())

def fuzzy_match_score(name_a: str, name_b: str) -> float:
    a = normalize_company_name(name_a)
    b = normalize_company_name(name_b)
    return SequenceMatcher(None, a, b).ratio()

def is_same_entity(name_a: str, name_b: str, threshold: float = 0.85) -> bool:
    return fuzzy_match_score(name_a, name_b) >= threshold
```

### 6.3 Anomaly Detection — Rule Engine (Pre-LLM)

A deterministic rule engine runs before LLM synthesis to flag hard signals with 100% precision:

```python
# app/intelligence/anomaly_detector.py

class AnomalyDetector:
    
    FATF_BLACKLIST = ["IR", "KP", "MM", "SY", "RU", "BY", "VE"]
    SHELL_ADDRESSES = [
        "1209 orange st wilmington",  # Delaware registered agents
        "251 little falls dr wilmington",
        # ... maintain list
    ]
    
    def detect(self, raw_data: dict) -> list[dict]:
        findings = []
        
        # Hard rule: Domain age vs company age mismatch
        whois = raw_data.get("domain_intelligence", {}).get("whois", {})
        entity = raw_data.get("entity_verification", {}).get("opencorporates", {})
        
        if whois.get("createdDate") and entity.get("incorporation_date"):
            domain_year = int(whois["createdDate"][:4])
            company_year = int(entity["incorporation_date"][:4])
            if domain_year > company_year + 2:
                findings.append({
                    "category": "domain_anomaly",
                    "severity": "HIGH",
                    "title": f"Domain registered {domain_year - company_year}yr after company incorporation",
                    "confidence_score": 9,
                })
        
        # Hard rule: UBO in FATF blacklisted country
        ubo_data = raw_data.get("beneficial_ownership", {})
        for ubo in ubo_data.get("owners", []):
            if ubo.get("nationality") in self.FATF_BLACKLIST:
                findings.append({
                    "category": "director_ubo_risk",
                    "severity": "HIGH",
                    "subject_name": ubo.get("name"),
                    "title": f"UBO nationality in FATF high-risk jurisdiction: {ubo.get('nationality')}",
                    "confidence_score": 8,
                })
        
        # Hard rule: Corporate email on free domain
        email_domain = raw_data.get("subject", {}).get("corporate_email_domain", "")
        free_providers = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
        if any(email_domain.endswith(p) for p in free_providers):
            findings.append({
                "category": "entity_integrity",
                "severity": "MEDIUM",
                "title": f"High-value vendor using free email domain: {email_domain}",
                "confidence_score": 7,
            })
        
        return findings
```

---

## 7. Risk Scoring Logic

### 7.1 Risk Score Computation

The final risk level is computed from the adverse findings using a weighted severity model — NOT from the LLM's own assessment (which is advisory only). This ensures the score is deterministic and auditable.

```python
# app/scoring/risk_calculator.py

SEVERITY_WEIGHTS = {
    "CRITICAL": 100,
    "HIGH":      40,
    "MEDIUM":    10,
    "LOW":        2,
}

CATEGORY_MULTIPLIERS = {
    "sanctions_watchlist": 2.0,   # Sanctions = always escalate
    "court_regulatory":    1.5,
    "director_ubo_risk":   1.3,
    "adverse_media":       1.0,
    "entity_integrity":    1.0,
    "domain_anomaly":      0.8,
    "financial_tax":       0.9,
}

RISK_THRESHOLDS = {
    "CRITICAL": 100,   # Any single CRITICAL finding = CRITICAL overall
    "HIGH":      60,
    "MEDIUM":    20,
    "LOW":        5,
    "CLEAN":      0,
}

def compute_risk_score(findings: list[dict]) -> tuple[int, str]:
    # Any single CRITICAL finding overrides the score
    if any(f["severity"] == "CRITICAL" for f in findings):
        return 100, "CRITICAL"
    
    total_score = 0
    for finding in findings:
        base = SEVERITY_WEIGHTS[finding["severity"]]
        multiplier = CATEGORY_MULTIPLIERS.get(finding["category"], 1.0)
        confidence_factor = finding["confidence_score"] / 10
        total_score += base * multiplier * confidence_factor
    
    if total_score >= RISK_THRESHOLDS["HIGH"]:
        return min(int(total_score), 99), "HIGH"
    elif total_score >= RISK_THRESHOLDS["MEDIUM"]:
        return int(total_score), "MEDIUM"
    elif total_score >= RISK_THRESHOLDS["LOW"]:
        return int(total_score), "LOW"
    else:
        return 0, "CLEAN"
```

### 7.2 Risk Level Decision Matrix

| Scenario | Computed Level | Recommended Action |
|---|---|---|
| OFAC/UN sanctions match (score > 0.85) | **CRITICAL** | Immediately block; legal notification required |
| Director on sanctions list | **CRITICAL** | Block; enhanced due diligence |
| Multiple HIGH findings (3+) | **HIGH** | Escalate to compliance officer; do not contract until resolved |
| Adverse court/regulatory record | **HIGH** | Escalate; request explanation from vendor |
| Domain age mismatch + no SSL | **MEDIUM** | Request documentation; proceed with caution |
| Single low-credibility news mention | **LOW** | Monitor; no action required |
| No adverse findings | **CLEAN** | Approved for onboarding (subject to periodic re-screen) |

### 7.3 Risk Categories — Definition Reference

| Category | What It Represents | Key Sources |
|---|---|---|
| **Credibility Concerns** | Gaps between claimed identity and verifiable facts | WHOIS vs incorporation date; domain not found; missing filings |
| **Fraud Risks** | Active indicators of deceptive or criminal behavior | Sanctions hits; court records; adverse media with crime keywords |
| **Operational Grey Areas** | Ambiguous signals requiring human judgment | PEP directors; single-source allegations; new company for niche contract |

---

## 8. Data Storage — Store Only Negatives Pattern

### 8.1 PostgreSQL Schema

```sql
-- =============================================
-- VENDOR INPUT TABLE — single source of truth
-- Captured ONCE via manual form or Excel upload;
-- referenced by any number of subsequent scans,
-- so Quick Scan and Deep Diligence never re-ask
-- the user for the same data
-- =============================================
CREATE TABLE vendor_inputs (
    input_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name             TEXT NOT NULL,
    website_domain         TEXT,
    registration_number    TEXT,
    jurisdiction_country   VARCHAR(2),
    tax_identifier         TEXT,
    registered_address     TEXT,
    director_names         TEXT[],
    director_din           TEXT[],
    founder_ceo_name       TEXT,
    social_handles         JSONB,      -- {platform: handle}
    corporate_email_domain TEXT,
    source_method          VARCHAR(10) CHECK (source_method IN ('manual','excel')),
    source_filename        TEXT,       -- original .xlsx filename, if applicable
    created_by              UUID,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- SCAN MASTER TABLE
-- =============================================
CREATE TABLE kyb_scans (
    scan_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_id            UUID NOT NULL REFERENCES vendor_inputs(input_id),
    scan_type           VARCHAR(10) CHECK (scan_type IN ('quick','deep')),
    scan_timestamp      TIMESTAMPTZ DEFAULT NOW(),
    status              VARCHAR(20) DEFAULT 'PENDING',
    overall_risk_level  VARCHAR(10) CHECK (overall_risk_level 
                            IN ('CRITICAL','HIGH','MEDIUM','LOW','CLEAN')),
    risk_score          INTEGER DEFAULT 0,
    total_findings      INTEGER DEFAULT 0,
    requires_review     BOOLEAN DEFAULT FALSE,
    partial_input_flags TEXT[],     -- Category 2-4 fields missing at intake, if any (Section 3.5)
    resolved_entity     JSONB,      -- {reg_number, lei, address, status}
    raw_data_summary    JSONB,      -- metadata only, NOT full raw data
    created_by          UUID,       -- user who initiated this specific scan
    completed_at        TIMESTAMPTZ
);

-- =============================================
-- ADVERSE FINDINGS — CORE TABLE
-- Only rows that are adverse ever written here
-- =============================================
CREATE TABLE adverse_findings (
    finding_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id             UUID NOT NULL REFERENCES kyb_scans(scan_id) ON DELETE CASCADE,
    
    -- Who the finding is about
    subject_type        VARCHAR(20) CHECK (subject_type IN 
                            ('ENTITY','DIRECTOR','UBO','RELATED_ENTITY')),
    subject_name        TEXT NOT NULL,
    contamination_path  TEXT,   -- e.g. "Company → Director → John → OFAC SDN"
    
    -- Finding classification
    category            VARCHAR(30) NOT NULL,
    severity            VARCHAR(10) NOT NULL CHECK (severity IN 
                            ('CRITICAL','HIGH','MEDIUM','LOW')),
    confidence_score    SMALLINT CHECK (confidence_score BETWEEN 1 AND 10),
    
    -- Human-readable content
    title               TEXT NOT NULL,
    detail              TEXT,
    
    -- Evidence
    source_tool         VARCHAR(30),
    source_urls         TEXT[],
    source_name         TEXT,
    finding_date        DATE,
    raw_excerpt         TEXT,
    
    -- Actions
    requires_human_review BOOLEAN DEFAULT TRUE,
    recommended_action  VARCHAR(20),   -- Block | Escalate | Monitor | Flag
    excel_highlight     VARCHAR(10),   -- RED | ORANGE | YELLOW
    
    -- Metadata
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- SUBJECTS DISCOVERED DURING SCAN
-- (Directors, UBOs found via entity resolution)
-- =============================================
CREATE TABLE scan_subjects (
    subject_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id             UUID REFERENCES kyb_scans(scan_id) ON DELETE CASCADE,
    subject_type        VARCHAR(20),
    name                TEXT NOT NULL,
    role                TEXT,       -- "Director", "UBO 60%", "CEO"
    nationality         VARCHAR(2),
    is_pep              BOOLEAN DEFAULT FALSE,
    screened_at         TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================
CREATE INDEX idx_findings_scan_id     ON adverse_findings(scan_id);
CREATE INDEX idx_findings_severity    ON adverse_findings(severity);
CREATE INDEX idx_findings_category    ON adverse_findings(category);
CREATE INDEX idx_findings_subject     ON adverse_findings(subject_name);
CREATE INDEX idx_findings_date        ON adverse_findings(created_at DESC);
CREATE INDEX idx_scans_risk           ON kyb_scans(overall_risk_level);
CREATE INDEX idx_scans_input_id       ON kyb_scans(input_id);
CREATE INDEX idx_scans_timestamp      ON kyb_scans(scan_timestamp DESC);
CREATE INDEX idx_vendor_inputs_name   ON vendor_inputs(legal_name);
```

### 8.2 Data Retention Policy

| Data Type | What's Stored | Retention | Rationale |
|---|---|---|---|
| `vendor_inputs` | The unified intake record (manual or Excel-derived) | 5 years | Single source of truth, re-screen without re-entry |
| `kyb_scans` | Scan metadata + resolved entity, linked to `vendor_inputs.input_id` | 5 years | Audit trail |
| `adverse_findings` | All negative findings | 5 years | Compliance evidence |
| `scan_subjects` | Directors/UBOs discovered | 5 years | Relationship mapping |
| Raw API responses | NOT stored in DB | Discarded after synthesis | Privacy + storage |
| Clean signals | NOT stored anywhere | Discarded immediately | Store-only-negatives pattern |
| Uploaded Excel file (raw .xlsx) | NOT stored after parsing | Discarded within 24 hours | Privacy by design — only the parsed `vendor_inputs` row persists |
| OCR documents | Deleted after extraction | 24 hours | Privacy by design |

---

## 9. Non-Functional Requirements

### 9.1 Performance Targets

| Operation | Target SLA |
|---|---|
| Vendor intake — manual form submission | < 500ms |
| Vendor intake — Excel upload, parse & validate | < 5 seconds |
| Quick Scan (end to end, after intake) | < 3 minutes |
| Deep Diligence (end to end, after intake) | < 15 minutes |
| API response to scan initiation | < 500ms |
| Status polling endpoint | < 100ms |
| Excel report generation | < 5 seconds |
| Dashboard page load | < 2 seconds |

### 9.2 Scalability

- Backend must handle **50 concurrent deep scans** without degradation
- Celery worker pool: 4 workers minimum, auto-scale to 20 under load
- Redis must be deployed in cluster mode for high availability

### 9.3 Security Requirements

- All external API keys stored in environment variables (never in code/DB)
- PostgreSQL connections via SSL only
- User authentication via JWT (RS256)
- All scan data scoped to authenticated organization (multi-tenant isolation)
- OCR documents never persisted to disk beyond 24 hours
- Audit log of every scan initiation with user ID and timestamp

### 9.4 Compliance Considerations

- GDPR Article 22: System outputs are advisory only; human review required before adverse action
- Data minimization: Raw API responses discarded; only adverse findings stored
- Right to explanation: Every finding must have an evidence trail (source_url + raw_excerpt)

---

## 10. Out of Scope (v1.0)

| Feature | Rationale |
|---|---|
| Batch Excel upload (multiple vendor rows per file) | v1.0 template supports exactly one vendor row per upload; multi-row batch intake deferred to v1.1 |
| Paid data vendor integration (Refinitiv World-Check, Dow Jones) | Deferred to v2 — public data first |
| Real-time monitoring / re-screening alerts | Deferred to v2 |
| Custom ML fraud classifier | Not needed; LLM prompt covers this |
| Mobile application | Web-only for v1 |
| API access for external consumers | Internal tool only for v1 |
| Dark web monitoring | Requires specialized vendor; out of public-data scope |

---

## 11. Open Questions & Decisions

| # | Question | Owner | Priority |
|---|---|---|---|
| 1 | Which LLM provider? Claude vs GPT-4o — cost/latency tradeoff at scale | Arch Team | HIGH |
| 2 | OpenCorporates free tier limits (10 req/min) — do we need paid plan at launch volume? | Product | HIGH |
| 3 | GDELT returns articles in 100+ languages — do we need translation before LLM synthesis? | Eng | MEDIUM |
| 4 | MCA (India) DIN API has no official public endpoint — scraper needed or skip? | Eng | MEDIUM |
| 5 | Define "known shell address" blocklist — who maintains this list? | Compliance | HIGH |
| 6 | Google CSE pricing at 10K+ queries/month — budget approval needed | Finance | MEDIUM |
| 7 | Re-screening cadence — how often should existing vendors be re-screened? | Compliance | LOW |
| 8 | Define multi-tenant isolation model — one DB schema per org or row-level security? | Arch | HIGH |
| 9 | Should Deep Diligence be allowed to run on a partial intake (Section 3.5), or should the UI block the request until Category 2–4 fields are filled in? | Product | HIGH |
| 10 | Excel template versioning — how do we handle older `VendorLens_Intake_Template.xlsx` versions re-uploaded after a schema change? | Eng | MEDIUM |
| 11 | Confirm illustrative Quick Scan vs. Deep Diligence cost multiplier (Section 2.1) against actual contracted API rates | Finance | MEDIUM |

---

*Document Owner: Product & Architecture Team*  
*Review Cycle: Before each sprint planning*  
*Next Review: Prior to Engineering Kickoff*