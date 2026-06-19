# Product Requirements Document (PRD)
## VendorLens — Automated KYB & Vendor Due Diligence Platform
**Version:** 3.0
**Status:** Engineering-Ready Draft
**Classification:** Internal — Confidential
**Last Updated:** June 2026

> **v3.0 changelog (this revision):** VendorLens is converted from a hosted web application to a **Windows desktop application** for internal procurement users on corporate laptops. All web-hosting, browser-client, and server-deployment requirements are replaced with local installation, local data storage, offline-capable workflows, and an auto-update mechanism. Vendor risk analysis functionality (API integrations, enrichment, risk scoring, document management, reporting) is unchanged. New: SAP vendor master data import (Excel/CSV). Sections changed from v2.0 are marked **[MODIFIED v3.0]**; unchanged sections are marked **[UNCHANGED]**.

---

## Table of Contents

1. [Executive Summary & Product Vision](#1-executive-summary--product-vision) — **[MODIFIED v3.0]**
2. [Target Personas & User Journeys](#2-target-personas--user-journeys) — **[MODIFIED v3.0]**
3. [Product Requirements & Input Schema](#3-product-requirements--input-schema) — **[MODIFIED v3.0 — Section 3.7 added]**
4. [System Architecture & Tech Stack](#4-system-architecture--tech-stack) — **[MODIFIED v3.0]**
5. [API Integration Specifications](#5-api-integration-specifications) — **[MODIFIED v3.0 — offline behavior added]**
6. [AI/ML & NLP Specifications](#6-aiml--nlp-specifications) — **[UNCHANGED]**
7. [Risk Scoring Logic](#7-risk-scoring-logic) — **[UNCHANGED]**
8. [Data Storage — Store Only Negatives Pattern](#8-data-storage--store-only-negatives-pattern) — **[MODIFIED v3.0]**
9. [Non-Functional Requirements](#9-non-functional-requirements) — **[MODIFIED v3.0]**
10. [Installation, Deployment & Update Model](#10-installation-deployment--update-model) — **[NEW v3.0]**
11. [Security Considerations](#11-security-considerations) — **[NEW v3.0 — replaces former web security sub-section]**
12. [Out of Scope](#12-out-of-scope) — **[MODIFIED v3.0]**
13. [Open Questions & Decisions](#13-open-questions--decisions) — **[MODIFIED v3.0]**

---

## 1. Executive Summary & Product Vision **[MODIFIED v3.0]**

### 1.1 The Problem **[UNCHANGED]**

Procurement and compliance teams performing vendor due diligence today face a three-way failure:

**Fragile custom scrapers** break every time a target website changes its HTML structure, requiring constant engineering maintenance. **Manual review processes** are inconsistent, slow (days per vendor), and non-auditable. **Point solutions** (one tool for sanctions, another for news, another for company registry) create data siloes with no unified risk view.

The result: either vendors slip through without adequate screening, or the screening process becomes an expensive bottleneck that delays commercial operations.

### 1.2 The Solution **[MODIFIED v3.0]**

**VendorLens** is a **Windows desktop application**, installed locally on each procurement team member's corporate laptop, that replaces fragile scrapers with a structured, API-first intelligence pipeline. It aggregates public data from authoritative sources — corporate registries, sanctions lists, WHOIS databases, global news indices, and court records — then uses a Large Language Model as a due diligence analyst to synthesize the raw data into a structured, actionable risk report. All vendor data, scan history, and findings are stored **locally on the user's machine**, with API enrichment occurring whenever the laptop has internet access.

The platform is purpose-built for **Know Your Business (KYB)** and **Third-Party Risk Management (TPRM)** workflows, meaning it screens not just the legal entity but the entire control structure behind it: directors, ultimate beneficial owners (UBOs), and related entities.

### 1.3 Product Vision Statement **[MODIFIED v3.0]**

> *"Install once on a procurement laptop. Capture every vendor's data once — by hand, by SAP export, or by Excel upload — then let the user decide, on demand, whether to run a 3-minute Quick Scan or a 15-minute Deep Diligence on that same data, working offline where possible and enriching automatically the moment a connection is available, storing only confirmed negative findings locally and surfacing them in a clear dashboard that requires zero manual data hunting and zero re-entry."*

### 1.4 Strategic Principles **[MODIFIED v3.0]**

| Principle | Implication |
|---|---|
| **Single intake, dual-depth output** | Vendor data is captured once (manual form, Excel upload, or SAP export); Quick Scan vs. Deep Diligence is a separate choice the user makes on that same stored data, as many times as needed |
| **Local-first, desktop-native** | Runs as an installed Windows application; no hosted web server or browser client required for core use |
| **API-first, no scrapers** | Zero maintenance overhead from HTML structure changes |
| **Offline-capable, online-enriched** | Intake, browsing, and report review work without internet; live screening requires connectivity and queues automatically when offline |
| **Store only negatives** | Minimal storage footprint on the local database; every DB row is a risk item |
| **LLM as analyst, not classifier** | Prompt-driven flexibility without ML model retraining |
| **Multi-layer entity screening** | Entity + Directors + UBOs all screened in one workflow |
| **Jurisdiction-agnostic** | Works for any country using global public data sources |
| **SAP-aware intake** | Vendor master records already maintained in SAP can be imported directly, avoiding duplicate data entry by procurement |

---

## 2. Target Personas & User Journeys **[MODIFIED v3.0]**

### 2.1 Target Users **[NEW v3.0]**

VendorLens v3.0 is built for **procurement team members working on corporate-issued Windows laptops**, typically operating in environments with intermittent VPN/internet access (e.g., supplier site visits, travel, secure facilities). Primary personas:

| Persona | Role | Primary Need |
|---|---|---|
| Procurement Analyst | Runs day-to-day vendor screenings | Fast Quick Scans during vendor selection meetings, including offline |
| Procurement Manager | Approves/escalates high-risk vendors | Deep Diligence reports, Excel/PDF exports for sign-off packets |
| Compliance Reviewer | Reviews CRITICAL/HIGH findings | Local audit trail, evidence drill-down, exportable reports |

### 2.2 Single-Pass Intake, Then User-Selected Scan Depth **[MODIFIED v3.0]**

The application UI does not gate input behind two tiers. Instead, the workflow splits into two independent steps performed locally on the desktop app: **Step A — Intake** (done once per vendor, by hand, Excel upload, or SAP export, covering every field the platform can use) and **Step B — Scan Depth** (a choice the user makes every time they want a report, reusing the same locally saved intake). This removes re-entry entirely: a vendor can be Quick-Scanned today and Deep-Diligenced next week — even on a different day with different connectivity — without typing anything twice.

```
┌───────────────────────────────────────────────────────────────┐
│  STEP A — INTAKE (once per vendor, runs locally)                │
│                                                                  │
│  Option 1: Manual Form     Option 2: Excel Upload   Option 3:   │
│  One page, every field      VendorLens_Intake_       SAP Vendor │
│  from Section 3.1           Template.xlsx — one      Master     │
│  (Categories 1–4).          row, same fields,        Export     │
│  Fill what you have;        parsed automatically.    (.xlsx/    │
│  leave the rest blank.      Works fully offline.     .csv) —    │
│                                                       see 3.7.   │
│                                                       Works      │
│                                                       offline.   │
│                                                                  │
│  + Optional: attach GST cert / invoice / license — OCR auto-    │
│    fills any fields still missing from any path above (local    │
│    OCR engine, no internet required)                            │
│                                                                  │
│  → Output: one normalized VendorInputRecord, saved to the local │
│    database as `input_id` — available immediately, no network   │
└───────────────────────────┬──────────────────────────────────────┘
                            │ Saved once locally — reused by every scan below
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  STEP B — CHOOSE SCAN DEPTH (any time, any number of times,     │
│  requires internet/VPN connectivity for live API enrichment)    │
│                                                                  │
│  [ Quick Scan ]                    [ Deep Diligence ]            │
│  ~3 min                            ~12–15 min                   │
│  Entity + Sanctions + Domain        Everything Quick Scan covers,│
│  + News                            PLUS regulatory IDs, director/│
│                                     UBO screening, address &     │
│                                     digital-footprint checks      │
│                                                                  │
│  If offline: scan request is queued locally and auto-runs the   │
│  moment connectivity is detected (see Section 5.9)               │
│                                                                  │
│  → Same input_id, run as Quick now and Deep later — no re-entry │
└───────────────────────────────────────────────────────────────┘
```

#### Scan Depth Comparison (the choice the user makes in Step B) **[UNCHANGED logic, connectivity note added]**

| | Quick Scan | Deep Diligence |
|---|---|---|
| Time SLA (online) | < 3 minutes | < 15 minutes |
| Connectivity required | Yes — live API calls | Yes — live API calls |
| Input categories used | Category 1 only (legal name + domain) | Categories 1–4 (everything captured at intake) |
| APIs triggered | OpenCorporates, GLEIF, WHOIS, GDELT, OpenSanctions, Google CSE | All of Quick Scan, plus MCA/Companies House officer lookups, OpenOwnership, Google Geocoding/Places, social-platform/SERP checks |
| Relative processing cost | Baseline (1×) — 4 API categories + 1 LLM synthesis call | Higher (≈3–4× baseline) — 8 API categories + UBO/director fan-out + 1 LLM synthesis call |
| Typical use case | Fast triage on a new or low-value vendor | Onboarding decision for a high-value or long-term vendor |
| Re-runnable on same input? | Yes, any time, including offline-queued | Yes, any time, including offline-queued — including immediately after a Quick Scan, with no new data entry |

> Exact dollar costs per scan depend on per-vendor API pricing tiers and are tracked as an open item in Section 13 (e.g., OpenCorporates and Google CSE volume pricing). The relative multiplier above is the planning figure until Finance confirms contracted rates.

### 2.3 User Journey — Manual Intake (Offline) → Quick Scan (Online) → Upgrade to Deep Diligence Later **[MODIFIED v3.0]**

```
1. User opens VendorLens on their laptop (no internet required to launch)
2. Fills the single intake form: "Apex Trading LLC" + "apextrading.com"
   (the only two required fields), plus whatever else is on hand —
   registration number, director names, social handles, etc. — all
   optional at this step. Works fully offline; saved to local DB.
3. Clicks "Save Vendor" → system returns an input_id; no scan has
   run yet, nothing has been screened
4. User clicks "Run Quick Scan" on that saved vendor
5. If laptop is online: app shows progress tracker in real time:
   [Entity Check ✓] [Sanctions ✓] [Domain Check...] [News Scan...]
   If laptop is offline: scan is queued with status "Pending —
   Waiting for Connection"; app auto-runs it the next time it
   detects internet/VPN access, with a desktop notification
6. Results render in ~3 min (once online): Entity card, Sanctions
   card, Domain anomaly card, Top 5 adverse news snippets, Overall
   risk badge
7. User exports a PDF or Excel summary locally, OR clicks "Run Deep
   Diligence on this vendor" — no new form, no re-upload; the
   system reuses the same input_id and simply runs the remaining
   categories the next time connectivity allows
```

### 2.4 User Journey — SAP Vendor Master Import → Excel Intake Enrichment → Deep Diligence (with OCR Enrichment) **[MODIFIED v3.0 — SAP import added]**

```
1. User exports the relevant vendor records from SAP (vendor master
   table, e.g., transaction XK03/MK03 or a standard SAP report) to
   Excel or CSV
2. In VendorLens, user selects "Import from SAP Export" and points
   to the exported file (see Section 3.7 for the column-mapping
   logic) — works fully offline, no network call is made at this
   step
3. App maps recognized SAP columns (vendor name, SAP vendor number,
   tax ID, address, country) into one or more VendorInputRecords and
   shows a preview/reconciliation screen before saving
4. User reviews the auto-populated summary, optionally attaches a
   GST certificate so local OCR can cross-check or fill any still-
   empty field, then clicks "Run Deep Diligence" once online
5. System runs the full pipeline (12–15 min while connected) using
   only the data captured in step 3 — nothing is asked twice
6. Results page shows: corporate structure tree (entity → directors
   → UBOs), per-subject risk cards, full adverse findings table
   (filterable by severity/category), contamination path for each
   finding, Excel/PDF export buttons
7. All adverse findings are stored in the local database; clean
   signals are discarded; the vendor's input_id remains saved for
   any future re-screen (Quick or Deep) without re-uploading
   anything, even across laptop restarts
```

---

## 3. Product Requirements & Input Schema **[MODIFIED v3.0 — Section 3.7 added]**

### 3.1 Input Categories & Data Dictionary **[UNCHANGED]**

All four categories below are presented in **one** intake step (Section 2.2, Step A) — as a manual form, an Excel upload, or a SAP export import (Section 3.7). Category 1 is mandatory to save an intake at all; Categories 2–4 are optional at intake time but determine how much of the pipeline a later **Deep Diligence** run can actually execute (see 3.5).

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
| `ocr_documents` | File array (PDF/JPG/PNG) | GST cert, invoice, trade license — **not** part of the Excel/SAP templates (binary files can't live in spreadsheet cells); always a separate, optional upload control alongside any intake path | Local Tesseract OCR pipeline (runs on-device, no internet required) |

### 3.2 Unified Intake — Manual Form **[UNCHANGED]**

A single page/wizard exposes every field from Categories 1–4 at once. There is no gating between sections: a user can skip straight to Category 4 without filling Category 2 first. Only `legal_name` and `website_domain` are marked required; everything else is "optional now, needed later if you want Deep Diligence." Submitting the form produces one `VendorInputRecord` and an `input_id` — no scan runs yet, and the form works fully offline.

### 3.3 Unified Intake — Excel Upload Template Schema **[UNCHANGED]**

Users who already track vendor data in a spreadsheet can skip the form entirely and upload `VendorLens_Intake_Template.xlsx`. The template is a single sheet, `Vendor_Intake`, with one header row and **one data row per vendor** (v1.0 scope — see Section 12 for multi-row batch as a future enhancement). Array-valued fields are encoded as semicolon-delimited text in a single cell so the template stays one row wide; the parser splits them back into arrays during ingestion. This upload and parse step runs entirely on the local machine and requires no network connection.

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

### 3.4 Internal Normalization — One Schema, Three Entry Paths **[MODIFIED v3.0 — `sap` source method added]**

Whichever path the user takes, all resolve to the same internal object before anything touches the orchestration layer, so downstream code never needs to know whether a vendor came in by hand, by spreadsheet, or by SAP export:

```python
# app/schemas/vendor_input.py
from pydantic import BaseModel
from typing import Optional, Literal

class VendorInputRecord(BaseModel):
    legal_name: str
    website_domain: Optional[str] = None   # may be blank on SAP-sourced records; user fills in later
    registration_number: Optional[str] = None
    jurisdiction_country: Optional[str] = None
    tax_identifier: Optional[str] = None
    registered_address: Optional[str] = None
    director_names: list[str] = []
    director_din: list[str] = []
    founder_ceo_name: Optional[str] = None
    social_handles: dict[str, str] = {}
    corporate_email_domain: Optional[str] = None
    source_method: Literal["manual", "excel", "sap"]
    source_filename: Optional[str] = None        # original .xlsx/.csv name, if applicable
    sap_vendor_number: Optional[str] = None       # populated only when source_method == "sap"

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

    def is_scan_ready(self) -> bool:
        """website_domain is required before any scan (Quick or Deep) can run,
        even though it may be absent immediately after a SAP import."""
        return bool(self.legal_name and self.website_domain)
```

> **Note:** `website_domain` was a strictly required field at intake in prior versions. Because SAP vendor master data frequently lacks a website field, it is now nullable on the record itself but still required before a scan can be initiated (`is_scan_ready()`). The UI prompts the user to fill in the missing domain for any SAP-imported vendor before the "Run Scan" button is enabled.

### 3.5 Partial Input Handling for Deep Diligence **[UNCHANGED]**

Because intake is decoupled from scan depth, a user can request Deep Diligence on a vendor whose intake only ever filled Category 1. The platform does **not** block this — it runs every category for which data exists and records the gap instead of erroring out:

- If `has_deep_fields()` is `False`, Deep Diligence behaves identically to a Quick Scan for this run, and `data_quality_notes` in the LLM output (Section 6.1) records *"Deep Diligence requested but no Category 2–4 data was captured at intake — director/UBO/address/digital-footprint checks skipped."*
- If some but not all Category 2–4 fields are present, only the corresponding tasks fire (e.g., directors were given but no address → director screening runs, address verification is skipped and noted).
- The application surfaces this as a banner: *"This report is based on partial data. Add registration number, address, or directors to your saved intake for a fuller Deep Diligence."* — with a link back to the same saved `input_id` so the user edits the existing local record rather than starting over.

### 3.6 Field-to-API Mapping Matrix **[UNCHANGED]**

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

### 3.7 SAP Vendor Master Import **[NEW v3.0]**

Procurement teams typically maintain a vendor master record in SAP (e.g., via the MM-Purchasing or FI-Vendor module). VendorLens supports importing this data directly so analysts never retype information SAP already has.

#### 3.7.1 Supported Export Formats

- Excel (`.xlsx`) export from standard SAP vendor master reports (e.g., S_ALR_87012086, XK03 list view, or an equivalent custom ABAP/Fiori export)
- CSV export (UTF-8 or Windows-1252 encoded; both auto-detected)
- Multi-row files are supported for SAP import specifically (unlike the single-row Excel intake template in 3.3) — each row becomes one `VendorInputRecord`

#### 3.7.2 Column Mapping

SAP export column headers vary by configuration, so the import flow uses **fuzzy header matching with a manual override step**:

| Expected SAP Field (typical header variants) | Maps to Field | Required |
|---|---|---|
| `Name 1` / `Vendor Name` / `LIFNR_NAME` | `legal_name` | Yes |
| `Vendor` / `Vendor Number` / `LIFNR` | `sap_vendor_number` | Yes |
| `Tax Number 1` / `STCD1` / `VAT Reg. No.` | `tax_identifier` | No |
| `Country` / `LAND1` | `jurisdiction_country` | No (mapped to ISO alpha-2 via lookup table) |
| `Street`, `City`, `Postal Code` (concatenated) | `registered_address` | No |
| `Registration Number` / `Trade Reg. No.` | `registration_number` | No |

If a column cannot be confidently auto-mapped, the import wizard presents a side-by-side preview so the user manually assigns the remaining SAP columns to VendorLens fields before committing the import. `website_domain` is never present in standard SAP vendor master data, so every SAP-imported row is flagged `is_scan_ready() == False` until the user supplies a domain.

#### 3.7.3 Import Behavior

- Import parsing runs **entirely locally**; no SAP system connectivity (RFC, OData, or otherwise) is required — the user exports manually from SAP GUI/Fiori and feeds the file to VendorLens
- Duplicate detection: rows are matched against existing `vendor_inputs.sap_vendor_number` (when present) or fuzzy-matched against `legal_name` (Section 6.2 resolver) to avoid creating duplicate intake records on re-import
- A successful import produces one `input_id` per row and a local import summary (rows imported / skipped / flagged for manual domain entry)
- No live API calls are made during import — enrichment only happens when the user later initiates a Quick Scan or Deep Diligence on an imported record

---

## 4. System Architecture & Tech Stack **[MODIFIED v3.0]**

### 4.1 High-Level Architecture **[MODIFIED v3.0]**

```
┌──────────────────────────────────────────────────────────────────┐
│              WINDOWS DESKTOP APPLICATION (installed locally)      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  DESKTOP UI LAYER                                          │    │
│  │  Electron shell + React 18 + TypeScript                    │    │
│  │  Unified Intake (Form | Excel | SAP Import)                │    │
│  │  Scan-Depth Selector · Local Dashboard · Offline Queue View │    │
│  └───────────────────────────┬──────────────────────────────┘    │
│                              │ Local IPC (no network hop)          │
│  ┌───────────────────────────▼──────────────────────────────┐    │
│  │  LOCAL APPLICATION SERVICE LAYER                           │    │
│  │  Python 3.11 (FastAPI, running on 127.0.0.1, loopback only)│    │
│  │  Packaged with the app — not exposed to the network         │    │
│  │  /vendor/intake  /vendor/import-sap  /scan  /scan/{id}/...  │    │
│  └──────┬───────────────────────────────────────────┬────────┘    │
│         │ Step A — intake (once, offline-capable)    │ Step B —    │
│  ┌──────▼──────────────────┐                  ┌──────▼─────────┐  │
│  │  INTAKE INGESTION       │  writes ONE       │  LOCAL TASK     │  │
│  │  Excel/CSV parser       │  VendorInput      │  SCHEDULER      │  │
│  │  (pandas/openpyxl)      │  Record to local  │  (APScheduler / │  │
│  │  SAP export parser      │  DB, reused by    │  Python threads,│  │
│  │  + fuzzy column mapper  │  every scan       │  no Celery/     │  │
│  │  Manual form validator  │  below ────────►  │  Redis broker   │  │
│  │  Local OCR pipeline     │                   │  required)      │  │
│  │  (Tesseract, on-device, │                   │                 │  │
│  │  no internet required)  │                   │  Connectivity   │  │
│  └──────────────────────────┘                  │  monitor: queues│  │
│                                                 │  scans offline, │  │
│                                                 │  auto-fires on  │  │
│                                                 │  reconnect      │  │
│                                                 └──────┬──────────┘  │
│                                                        │             │
│  ┌─────────────────────────────────────────────────────▼─────────┐ │
│  │              LOCAL DATA PERSISTENCE LAYER                      │ │
│  │  SQLite (default, zero-config) or local PostgreSQL 15          │ │
│  │  (optional, for power users/larger datasets)                   │ │
│  │  STORE ONLY NEGATIVES pattern — unchanged                       │ │
│  │  Tables: vendor_inputs │ kyb_scans │ adverse_findings │         │ │
│  │          scan_subjects │ scan_queue (offline-pending scans)     │ │
│  │  File location: %LOCALAPPDATA%\VendorLens\data\                │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬────────────────────────────────────┘
                               │ HTTPS (outbound only, via corporate
                               │ proxy/VPN) — required only when a
                               │ scan is actively running
┌──────────────────────────────▼────────────────────────────────────┐
│                  EXTERNAL API INTEGRATION LAYER (cloud)            │
│                                                                     │
│  Entity:      OpenCorporates │ GLEIF │ Companies House              │
│  Sanctions:   OpenSanctions  │ OFAC XML │ UN Consolidated List      │
│  Domain:      WHOIS API      │ SSL Labs │ VirusTotal                │
│  News/Media:  GDELT          │ NewsAPI  │ Google CSE                │
│  Ownership:   OpenOwnership  │ UK PSC   │ GLEIF L2                  │
│  PEP:         OpenSanctions PEP dataset │ Wikidata SPARQL           │
│  Address:     Google Geocoding + Places                             │
│  LLM:         Anthropic Claude API (synthesis only — see Section 6) │
└─────────────────────────────────────────────────────────────────────┘
```

**Key architectural shift:** there is no central application server and no multi-tenant hosting. Each procurement laptop runs a fully self-contained instance: UI, application logic, task scheduling, and database all live on the local machine. The only outbound network dependency is the External API Integration Layer, called directly from the laptop when a scan is initiated and connectivity is available.

### 4.2 Technology Stack Specification **[MODIFIED v3.0]**

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Desktop Shell | Electron | 30.x | Packages the React UI + local Python service into a single installable Windows app |
| Frontend | React + TypeScript | 18.x | Component-based, typed, strong ecosystem; reused from prior web UI with minimal change |
| UI Components | shadcn/ui + Tailwind CSS | Latest | Rapid, consistent, accessible UI |
| Local State/Data Fetching | TanStack Query | v5 | Polling scan/queue status against the local loopback service |
| Local Application Service | FastAPI (Python 3.11+), bound to `127.0.0.1` only | 0.111+ | Async-first; same framework as before, now packaged for local execution instead of hosted deployment |
| Local Task Scheduling | APScheduler (in-process) | Latest | Replaces Celery/Redis — no distributed broker needed for a single-user desktop install |
| Connectivity Monitor | Custom Python service (network reachability poll) | — | Detects online/offline state; drives the offline scan queue |
| Local Database | SQLite (default) | 3.45+ | Zero-config, file-based, ships embedded with the installer |
| Local Database (optional) | PostgreSQL | 15.x | Optional for power users/teams who prefer a local Postgres instance; same schema as SQLite mode |
| ORM | SQLAlchemy 2.0 + Alembic | Latest | ORM + migrations; supports both SQLite and PostgreSQL backends |
| Spreadsheet/CSV Parsing | pandas + openpyxl | Latest | Parses the Excel intake template and SAP exports (.xlsx/.csv) into VendorInputRecords |
| OCR | Tesseract 5 + pytesseract | Latest | Fully local OCR; no cloud OCR fallback, by design, for offline support |
| HTTP Client | httpx | 0.27+ | Async HTTP for outbound API calls when online; respects corporate proxy settings |
| LLM | Anthropic Claude API | claude-sonnet | Structured JSON output via tool use; the one component that always requires connectivity |
| Local Caching | SQLite-backed response cache (TTL-based) | — | Caches recent API responses (e.g., sanctions list snapshots, geocoding results) to reduce repeat calls and support partial offline review |
| Auto-Update | Squirrel.Windows (via electron-builder) | Latest | Background update checks and silent/staged rollout to installed laptops |
| Packaging/Installer | electron-builder (NSIS installer, MSI variant for SCCM/Intune) | Latest | Produces a signed Windows installer for IT-managed deployment |
| Local Logging | Python `logging` + rotating file handler | — | Local log files under `%LOCALAPPDATA%\VendorLens\logs\` for support/diagnostics |
| Monitoring | Sentry (desktop SDK, crash/error reporting only) | Latest | Replaces Flower (no distributed workers to monitor); opt-in telemetry |

### 4.3 Backend 3-Step Core Workflow (Code Architecture) **[MODIFIED v3.0]**

#### Step 1 — Data Ingestion (Local Intake Layer + Local Orchestration Layer)

```python
# app/routers/intake.py
# Local FastAPI service bound to 127.0.0.1 — never exposed beyond the
# user's own machine. Single intake endpoint — runs ONCE per vendor,
# regardless of which scan depth is requested later. Accepts a manual
# form payload, an Excel upload, or a SAP export file; all normalize
# to the same VendorInputRecord and are written to the local DB.

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.vendor_input import VendorInputRecord
from app.intake.excel_parser import parse_vendor_excel
from app.intake.sap_parser import parse_sap_export
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
    await local_db.save_vendor_input(input_id, record)   # writes to local SQLite/Postgres

    return {
        "input_id": input_id,
        "source_method": record.source_method,
        "deep_diligence_ready": record.has_deep_fields(),
        "scan_ready": record.is_scan_ready(),
    }


@router.post("/vendor/import-sap")
async def import_sap_vendors(sap_file: UploadFile = File(...)):
    """Bulk import — unlike /vendor/intake, this accepts multiple
    vendor rows from a single SAP export and creates one
    VendorInputRecord per row. Runs entirely offline."""
    records = await parse_sap_export(sap_file)
    results = []
    for record in records:
        input_id = str(uuid.uuid4())
        await local_db.save_vendor_input(input_id, record)
        results.append({
            "input_id": input_id,
            "legal_name": record.legal_name,
            "sap_vendor_number": record.sap_vendor_number,
            "scan_ready": record.is_scan_ready(),  # False until domain is added
        })
    return {"imported": len(results), "vendors": results}
```

```python
# app/routers/scan.py
# Single /scan endpoint — input was already captured locally at
# /vendor/intake or /vendor/import-sap. scan_type only decides WHICH
# tasks fire against that same stored record. If the connectivity
# monitor reports offline, the scan is written to the local
# scan_queue table instead of dispatched immediately, and the local
# scheduler retries it once connectivity returns.

from fastapi import APIRouter, HTTPException
from app.scheduler import local_task_scheduler
from app.connectivity import is_online
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
    record = await local_db.get_vendor_input(payload.input_id)
    if record is None:
        raise HTTPException(404, "Unknown input_id — call /vendor/intake first")
    if not record.is_scan_ready():
        raise HTTPException(422, "website_domain is required before a scan can run")

    scan_id = str(uuid.uuid4())
    tasks = DEEP_DILIGENCE_TASKS if payload.scan_type == "deep" else QUICK_SCAN_TASKS

    if payload.scan_type == "deep" and not record.has_deep_fields():
        await local_db.flag_partial_deep_diligence(scan_id, record.missing_deep_fields())

    if not is_online():
        await local_db.enqueue_offline_scan(scan_id, payload.input_id, payload.scan_type)
        return {
            "scan_id": scan_id, "input_id": payload.input_id,
            "status": "QUEUED_OFFLINE", "scan_type": payload.scan_type,
        }

    local_task_scheduler.run_scan(record, scan_id, tasks, payload.scan_type)
    await local_db.set_scan_status(scan_id, "RUNNING")
    return {
        "scan_id": scan_id, "input_id": payload.input_id,
        "status": "RUNNING", "scan_type": payload.scan_type,
    }


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    return await local_db.get_scan_status(scan_id)


@router.get("/scan/{scan_id}/report")
async def get_report(scan_id: str, format: str = "json"):
    findings = await local_db.get_adverse_findings(scan_id)
    if format == "excel":
        return generate_excel_response(findings)
    if format == "pdf":
        return generate_pdf_response(findings)
    return findings
```

#### Step 2 — AI Analysis (NLP Layer) **[UNCHANGED — logic identical, runs locally and calls the cloud LLM API only]**

```python
# app/tasks/synthesize.py

def synthesize_findings_task(parallel_results: list, scan_id: str, scan_type: str):
    """
    Called by the local task scheduler after ALL parallel tasks complete.
    parallel_results is a list of dicts, one per tool.
    scan_type ("quick" | "deep") only affects which tools ran upstream —
    by this point it's just a label for the report header.
    Requires connectivity for the LLM API call; all other steps are local.
    """
    merged_raw = {}
    for result in parallel_results:
        if result and "tool" in result:
            merged_raw[result["tool"]] = result["data"]

    adverse_findings = call_llm_synthesis(merged_raw, scan_id, scan_type)

    # STORE ONLY NEGATIVES — write only adverse findings, to the local DB
    if adverse_findings["adverse_findings"]:
        local_db.bulk_insert_findings(scan_id, adverse_findings["adverse_findings"])

    local_db.update_scan_summary(
        scan_id=scan_id,
        risk_level=adverse_findings["risk_summary"]["overall_risk_level"],
        total_findings=adverse_findings["risk_summary"]["total_adverse_findings"]
    )

    return scan_id
```

#### Step 3 — Output & Reporting **[MODIFIED v3.0 — local file save + PDF export added]**

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
    local_tmp_path = local_app_paths.temp_dir() / f"{scan_id}_report.xlsx"

    with pd.ExcelWriter(local_tmp_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Adverse Findings", index=False)
        ws = writer.sheets["Adverse Findings"]
        for row_idx, finding in enumerate(findings, start=2):
            color = COLOR_MAP.get(finding["severity"], "FFFFFF")
            for col_idx in range(1, len(df.columns) + 1):
                ws.cell(row=row_idx, column=col_idx).fill = \
                    PatternFill("solid", fgColor=color)

    with open(local_tmp_path, "rb") as f:
        return f.read()


# app/reports/pdf_generator.py
# New in v3.0: one-click PDF export for sign-off packets, generated
# locally with WeasyPrint/ReportLab — no server round trip.
def generate_pdf_report(scan_id: str, findings: list[dict], risk_summary: dict) -> bytes:
    local_tmp_path = local_app_paths.temp_dir() / f"{scan_id}_report.pdf"
    render_pdf_template(
        template="kyb_report.html",
        context={"findings": findings, "risk_summary": risk_summary},
        output_path=local_tmp_path,
    )
    with open(local_tmp_path, "rb") as f:
        return f.read()
```

---

## 5. API Integration Specifications **[MODIFIED v3.0 — offline behavior added]**

### 5.0 Offline / Online Behavior **[NEW v3.0]**

All API integrations in this section require an active internet connection (typically via the corporate VPN or direct corporate network). VendorLens' local connectivity monitor checks reachability before dispatching any scan task:

- **Online:** API calls dispatch immediately as described in 5.1–5.8.
- **Offline:** the scan request is written to the local `scan_queue` table with status `QUEUED_OFFLINE`. No partial API calls are attempted. The desktop app shows a persistent "Offline — N scans queued" indicator in the UI.
- **Reconnect:** the connectivity monitor detects restored access (default poll interval: 30 seconds) and automatically dispatches queued scans in FIFO order, with a Windows toast notification per completed scan.
- **Cached read-only data:** previously completed scan results, saved vendor intakes, and exported reports remain fully accessible offline at all times, since they are stored in the local database.

### 5.1 Entity Verification APIs **[UNCHANGED]**

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

### 5.2 Sanctions & Watchlist API **[UNCHANGED]**

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

> **Local caching note:** sanctions list snapshots used in the most recent successful scan for a given entity are cached locally (TTL: 24 hours) so the report remains viewable offline, but the cache is never used to satisfy a *new* scan request — a fresh online check is always required to mark a scan as current.

### 5.3 Domain Intelligence APIs **[UNCHANGED]**

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

### 5.4 Adverse Media APIs **[UNCHANGED]**

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

### 5.5 Beneficial Ownership & Director APIs **[UNCHANGED]**

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

### 5.6 Address Verification API (Shell Company Detection) **[UNCHANGED]**

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

### 5.7 Document OCR Pipeline (Local, Offline-Capable) **[MODIFIED v3.0]**

This pipeline is **not** a separate input tier — it is an optional convenience that fills gaps in the single unified intake (manual form, Excel, or SAP import) whenever the user attaches a supporting document. Its output merges into the same `VendorInputRecord`, never a separate record. **Unlike the LLM extraction step below, the OCR text recognition itself runs fully on-device via Tesseract and requires no internet connection.** The subsequent entity-extraction call to Claude does require connectivity; if offline, raw OCR text is stored locally and entity extraction is queued for the next online session.

```python
# app/ocr/extractor.py
import pytesseract
from PIL import Image
import anthropic
import pdf2image
from app.connectivity import is_online

def extract_entities_from_document(file_bytes: bytes, mime_type: str) -> dict:
    """
    Converts uploaded document → text (local, offline) → LLM entity
    extraction (requires connectivity; queued locally if offline).
    """
    if mime_type == "application/pdf":
        images = pdf2image.convert_from_bytes(file_bytes, dpi=300)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
    else:
        img = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(img)

    if not is_online():
        local_db.queue_ocr_extraction(text)
        return {"status": "QUEUED_OFFLINE", "raw_text": text}

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

### 5.8 Excel Intake Parser **[UNCHANGED]**

Parses `VendorLens_Intake_Template.xlsx` (Section 3.3) into the same `VendorInputRecord` used by the manual form, validates required columns, and splits semicolon-delimited array fields. Runs fully locally, no network access required.

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
    row = df.iloc[0]  # v1.0: exactly one vendor per upload via this template

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

### 5.9 SAP Export Parser **[NEW v3.0]**

Parses an SAP vendor master export (Section 3.7) into one or more `VendorInputRecord` objects. Supports both `.xlsx` and `.csv`, with fuzzy column header matching and a manual-mapping fallback. Runs fully locally, no network access or SAP system connectivity required.

```python
# app/intake/sap_parser.py
import pandas as pd
from difflib import get_close_matches
from app.schemas.vendor_input import VendorInputRecord

FIELD_HEADER_CANDIDATES = {
    "legal_name": ["Name 1", "Vendor Name", "LIFNR_NAME"],
    "sap_vendor_number": ["Vendor", "Vendor Number", "LIFNR"],
    "tax_identifier": ["Tax Number 1", "STCD1", "VAT Reg. No."],
    "jurisdiction_country": ["Country", "LAND1"],
    "registration_number": ["Registration Number", "Trade Reg. No."],
}

async def parse_sap_export(file) -> list[VendorInputRecord]:
    if file.filename.lower().endswith(".csv"):
        df = pd.read_csv(file.file, dtype=str, encoding_errors="replace").fillna("")
    else:
        df = pd.read_excel(file.file, dtype=str).fillna("")

    column_map = _auto_map_columns(df.columns.tolist())
    # If legal_name or sap_vendor_number could not be auto-mapped,
    # the API returns a 422 with the unmapped headers so the desktop
    # UI can present the manual-mapping screen before retrying.
    _validate_required_mapping(column_map)

    records = []
    for _, row in df.iterrows():
        records.append(VendorInputRecord(
            legal_name=row[column_map["legal_name"]].strip(),
            website_domain=None,  # never present in SAP exports; user fills in later
            sap_vendor_number=row.get(column_map.get("sap_vendor_number"), "") or None,
            tax_identifier=row.get(column_map.get("tax_identifier"), "") or None,
            jurisdiction_country=_normalize_country(row.get(column_map.get("jurisdiction_country"), "")),
            registration_number=row.get(column_map.get("registration_number"), "") or None,
            source_method="sap",
            source_filename=file.filename,
        ))
    return records

def _auto_map_columns(headers: list[str]) -> dict[str, str]:
    mapped = {}
    for field, candidates in FIELD_HEADER_CANDIDATES.items():
        for header in headers:
            if header in candidates or get_close_matches(header, candidates, n=1, cutoff=0.8):
                mapped[field] = header
                break
    return mapped

def _validate_required_mapping(column_map: dict) -> None:
    required = ["legal_name", "sap_vendor_number"]
    missing = [f for f in required if f not in column_map]
    if missing:
        raise ValueError(f"Could not auto-map required SAP columns: {missing}")

def _normalize_country(raw: str) -> str | None:
    # Lookup against an ISO 3166-1 alpha-2 table; returns None if unrecognized
    return COUNTRY_LOOKUP.get(raw.strip().upper())
```

---

## 6. AI/ML & NLP Specifications **[UNCHANGED — see Section 0 changelog note]**

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
    "input_source": "manual | excel | sap"
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

Before passing data to the LLM, the local application performs entity resolution to canonicalize names across sources:

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

A deterministic rule engine runs locally before LLM synthesis to flag hard signals with 100% precision:

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

## 7. Risk Scoring Logic **[UNCHANGED]**

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

## 8. Data Storage — Store Only Negatives Pattern **[MODIFIED v3.0]**

### 8.1 Local Database Schema **[MODIFIED v3.0]**

VendorLens stores all data locally, in **SQLite** by default (zero-config, file at `%LOCALAPPDATA%\VendorLens\data\vendorlens.db`) or in a **local PostgreSQL 15** instance for users/teams who opt into that configuration during install. The schema below is identical across both backends; SQLite-specific type adjustments (e.g., `TEXT` for arrays/JSON instead of native `TEXT[]`/`JSONB`) are handled transparently by the ORM layer.

```sql
-- =============================================
-- VENDOR INPUT TABLE — single source of truth
-- Captured ONCE via manual form, Excel upload, or
-- SAP export import; referenced by any number of
-- subsequent scans, so Quick Scan and Deep
-- Diligence never re-ask the user for the same data.
-- Stored locally on the user's machine.
-- =============================================
CREATE TABLE vendor_inputs (
    input_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name             TEXT NOT NULL,
    website_domain         TEXT,            -- nullable; required before any scan (is_scan_ready)
    registration_number    TEXT,
    jurisdiction_country   VARCHAR(2),
    tax_identifier         TEXT,
    registered_address     TEXT,
    director_names         TEXT[],
    director_din           TEXT[],
    founder_ceo_name       TEXT,
    social_handles         JSONB,      -- {platform: handle}
    corporate_email_domain TEXT,
    source_method          VARCHAR(10) CHECK (source_method IN ('manual','excel','sap')),
    source_filename        TEXT,       -- original .xlsx/.csv filename, if applicable
    sap_vendor_number      TEXT,       -- populated only when source_method = 'sap'
    created_by              UUID,      -- local Windows user account identifier
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- OFFLINE SCAN QUEUE — new in v3.0
-- Holds scan requests created while the laptop
-- was offline; the local scheduler drains this
-- table automatically once connectivity returns
-- =============================================
CREATE TABLE scan_queue (
    queue_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id             UUID NOT NULL,
    input_id            UUID NOT NULL REFERENCES vendor_inputs(input_id),
    scan_type           VARCHAR(10) CHECK (scan_type IN ('quick','deep')),
    queued_at           TIMESTAMPTZ DEFAULT NOW(),
    status              VARCHAR(20) DEFAULT 'QUEUED_OFFLINE',
    dispatched_at       TIMESTAMPTZ
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
    created_by          UUID,       -- local Windows user account that initiated this scan
    completed_at        TIMESTAMPTZ
);

-- =============================================
-- ADVERSE FINDINGS — CORE TABLE
-- Only rows that are adverse ever written here
-- =============================================
CREATE TABLE adverse_findings (
    finding_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id             UUID NOT NULL REFERENCES kyb_scans(scan_id) ON DELETE CASCADE,

    subject_type        VARCHAR(20) CHECK (subject_type IN
                            ('ENTITY','DIRECTOR','UBO','RELATED_ENTITY')),
    subject_name        TEXT NOT NULL,
    contamination_path  TEXT,   -- e.g. "Company → Director → John → OFAC SDN"

    category            VARCHAR(30) NOT NULL,
    severity            VARCHAR(10) NOT NULL CHECK (severity IN
                            ('CRITICAL','HIGH','MEDIUM','LOW')),
    confidence_score    SMALLINT CHECK (confidence_score BETWEEN 1 AND 10),

    title               TEXT NOT NULL,
    detail              TEXT,

    source_tool         VARCHAR(30),
    source_urls         TEXT[],
    source_name         TEXT,
    finding_date        DATE,
    raw_excerpt         TEXT,

    requires_human_review BOOLEAN DEFAULT TRUE,
    recommended_action  VARCHAR(20),   -- Block | Escalate | Monitor | Flag
    excel_highlight     VARCHAR(10),   -- RED | ORANGE | YELLOW

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
-- LOCAL API RESPONSE CACHE — new in v3.0
-- TTL-based cache to reduce repeat API calls and
-- support partial offline review of recent lookups
-- =============================================
CREATE TABLE api_response_cache (
    cache_key           TEXT PRIMARY KEY,   -- hash of (api_name + query params)
    api_name             VARCHAR(30),
    response_json        JSONB,
    cached_at            TIMESTAMPTZ DEFAULT NOW(),
    expires_at            TIMESTAMPTZ
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
CREATE INDEX idx_vendor_inputs_sap    ON vendor_inputs(sap_vendor_number);
CREATE INDEX idx_scan_queue_status    ON scan_queue(status);
CREATE INDEX idx_api_cache_expiry     ON api_response_cache(expires_at);
```

### 8.2 Data Retention Policy **[MODIFIED v3.0]**

| Data Type | What's Stored | Retention | Rationale |
|---|---|---|---|
| `vendor_inputs` | The unified intake record (manual, Excel, or SAP-derived), stored locally | 5 years (local) | Single source of truth, re-screen without re-entry |
| `kyb_scans` | Scan metadata + resolved entity, linked to `vendor_inputs.input_id`, stored locally | 5 years | Audit trail |
| `adverse_findings` | All negative findings, stored locally | 5 years | Compliance evidence |
| `scan_subjects` | Directors/UBOs discovered, stored locally | 5 years | Relationship mapping |
| `scan_queue` | Pending offline scans | Until dispatched + 30 days | Troubleshooting/audit of offline behavior |
| `api_response_cache` | Recent API responses for offline report viewing | 24 hours (TTL) | Performance + limited offline review; never substitutes for a live re-scan |
| Raw API responses (full payload) | NOT stored in local DB | Discarded after synthesis | Privacy + storage footprint on the laptop |
| Clean signals | NOT stored anywhere | Discarded immediately | Store-only-negatives pattern |
| Uploaded Excel/SAP/CSV file (raw) | NOT stored after parsing | Discarded within 24 hours from local temp folder | Privacy by design — only the parsed `vendor_inputs` row(s) persist |
| OCR documents | Deleted after extraction | 24 hours, from local temp folder | Privacy by design |
| Local backup | Optional scheduled export of the local DB to a user-designated folder (e.g., a corporate-managed network drive or OneDrive sync folder) | User-configured | Protects against laptop loss/reimage; off by default, opt-in |

> **Note:** because data now resides on individual laptops rather than a central server, IT/Compliance should define a backup or sync policy (see Open Question in Section 13) to avoid data loss on device replacement, and a device-decommissioning procedure to securely wipe the local database when a laptop is retired or reassigned.

---

## 9. Non-Functional Requirements **[MODIFIED v3.0]**

### 9.1 Performance Targets **[MODIFIED v3.0]**

| Operation | Target SLA |
|---|---|
| Application cold start (launch to usable UI) | < 5 seconds |
| Vendor intake — manual form submission | < 500ms |
| Vendor intake — Excel upload, parse & validate | < 5 seconds |
| Vendor intake — SAP export import (up to 500 rows) | < 15 seconds |
| Quick Scan (end to end, after intake, while online) | < 3 minutes |
| Deep Diligence (end to end, after intake, while online) | < 15 minutes |
| Offline scan auto-dispatch after reconnect detected | < 30 seconds |
| API response to scan initiation | < 500ms |
| Status polling (local loopback call) | < 50ms |
| Excel report generation (local) | < 5 seconds |
| PDF report generation (local) | < 5 seconds |
| Dashboard / vendor list load (local DB query) | < 1 second |

### 9.2 Scalability **[MODIFIED v3.0]**

- Each installed instance is single-user/single-machine; no shared backend capacity planning is required
- Local SQLite/PostgreSQL must comfortably support **at least 10,000 vendor records and 50,000 adverse findings per laptop** without query degradation
- Deep Diligence scans run sequentially per laptop by default (one active scan at a time) to avoid saturating the user's network connection and corporate API rate limits; the offline queue allows multiple scans to be requested and processed in order
- No requirement for concurrent multi-user load on a single instance, since each laptop serves one user

### 9.3 Compatibility & Environment Requirements **[NEW v3.0]**

- **Operating System:** Windows 10 (21H2+) and Windows 11, 64-bit, on corporate-managed laptops
- **Hardware:** Minimum 8 GB RAM, 4 CPU cores, 2 GB free disk space (installer + local DB growth headroom)
- **Network:** Functions fully offline for intake/browsing/reporting; outbound HTTPS (443) required for scans and LLM synthesis, compatible with standard corporate proxy/VPN configurations
- **Permissions:** Installable and runable under standard (non-administrator) corporate user accounts once initially installed via IT-managed deployment (see Section 10)
- **Display:** Supports standard corporate laptop resolutions (1366×768 and above), including HiDPI scaling

### 9.4 Compliance Considerations **[UNCHANGED]**

- GDPR Article 22: System outputs are advisory only; human review required before adverse action
- Data minimization: Raw API responses discarded; only adverse findings stored
- Right to explanation: Every finding must have an evidence trail (source_url + raw_excerpt)

---

## 10. Installation, Deployment & Update Model **[NEW v3.0]**

### 10.1 Installation

- Distributed as a signed Windows installer (`.exe` via NSIS, or `.msi` for environments using SCCM/Intune for managed software deployment)
- IT can push the installer via standard enterprise software distribution tools, or users can self-install from an internal software portal, depending on corporate policy
- First-launch setup wizard prompts the user to choose the local database backend (SQLite default, or local PostgreSQL for advanced users) and configures the `%LOCALAPPDATA%\VendorLens\` directory structure (`data\`, `logs\`, `temp\`)
- API keys for external services (OpenCorporates, OpenSanctions, WHOIS, etc.) and the Anthropic API key are provisioned centrally by IT/Compliance and distributed via a secure configuration file or corporate secrets vault integration — never entered or stored in plaintext by end users (see Section 11)

### 10.2 Auto-Update Mechanism

- The application checks for updates on launch and periodically in the background (default: every 12 hours), using Squirrel.Windows via electron-builder
- Updates download in the background and apply on next application restart, minimizing workflow disruption
- IT can configure a staged rollout (pilot group → full fleet) and can pin an environment to a specific release channel if needed for change-control purposes
- Update checks and downloads respect the offline/online state — if offline, the check is silently deferred and retried later

### 10.3 Uninstall & Decommissioning

- Standard Windows "Apps & Features" uninstall removes the application binaries
- The local database is preserved by default on uninstall (in case of reinstall) but a "Remove all local data" option is available during uninstall for device decommissioning, securely deleting the `%LOCALAPPDATA%\VendorLens\data\` directory
- A documented IT decommissioning procedure should be followed when a laptop is reassigned or retired (see Open Question in Section 13)

---

## 11. Security Considerations **[NEW v3.0 — replaces prior web-hosted security model]**

- **No inbound network exposure:** the local FastAPI service binds exclusively to `127.0.0.1` and is never reachable from the corporate network or internet; there is no server-side attack surface to harden or patch
- **API key management:** external API keys and the Anthropic API key are not entered by end users; they are provisioned via a secure configuration mechanism managed by IT/Compliance (e.g., encrypted config file deployed alongside the installer, or integration with a corporate secrets manager) and stored encrypted at rest on the local disk using Windows DPAPI
- **Local database encryption:** the local SQLite/PostgreSQL database is encrypted at rest using Windows BitLocker (assumed standard on corporate-managed laptops) as the primary control; SQLCipher is evaluated as an additional application-level encryption layer (see Open Question in Section 13)
- **Authentication:** the application itself does not require a separate login; it relies on the existing Windows corporate login (Active Directory/Entra ID) as the access control boundary, consistent with other locally installed corporate tools. `created_by` fields are populated from the local Windows user identity
- **Outbound traffic only:** all external API calls are outbound HTTPS, routed through the existing corporate proxy/VPN, subject to existing corporate network monitoring and DLP controls
- **Document handling:** OCR source documents and any temporary export files are written only to the local `temp\` directory and deleted within 24 hours; nothing is uploaded to a third-party server except the specific enrichment APIs explicitly listed in Section 5
- **Audit logging:** every intake, import, and scan action is logged locally with the Windows user identity and timestamp, supporting compliance review even though there is no central server-side audit log
- **Code signing:** the installer and all auto-update packages are signed with a corporate code-signing certificate so Windows SmartScreen and corporate endpoint protection do not block installation or updates
- **Multi-tenant isolation:** not applicable in the desktop model — each laptop's data belongs to a single user/session by construction, removing the need for the row-level or schema-level tenant isolation required in the prior hosted architecture

---

## 12. Out of Scope (v1.0 Desktop Release) **[MODIFIED v3.0]**

| Feature | Rationale |
|---|---|
| Batch Excel upload via the single-row intake template (multiple vendor rows per `.xlsx` upload) | The single-row Excel intake template remains one-vendor-per-upload; bulk import is covered separately via the SAP export path (Section 3.7), which does support multiple rows |
| Central/shared server deployment, multi-user hosted mode | Out of scope for this release — v1.0 is a single-user local install; a future "team sync" mode is a candidate for a later phase |
| Paid data vendor integration (Refinitiv World-Check, Dow Jones) | Deferred to v2 — public data first |
| Real-time monitoring / re-screening alerts | Deferred to v2 |
| Custom ML fraud classifier | Not needed; LLM prompt covers this |
| macOS / Linux desktop builds | Windows-only for v1, consistent with corporate laptop fleet |
| Mobile application | Desktop-only for v1 |
| Direct SAP system connectivity (RFC/OData live connection) | v1.0 supports file-based SAP export import only; live SAP integration is a candidate for a later phase |
| API access for external consumers | Internal desktop tool only for v1 |
| Dark web monitoring | Requires specialized vendor; out of public-data scope |

---

## 13. Open Questions & Decisions **[MODIFIED v3.0]**

| # | Question | Owner | Priority |
|---|---|---|---|
| 1 | Which LLM provider? Claude vs GPT-4o — cost/latency tradeoff at scale | Arch Team | HIGH |
| 2 | OpenCorporates free tier limits (10 req/min) — do we need paid plan at launch volume? | Product | HIGH |
| 3 | GDELT returns articles in 100+ languages — do we need translation before LLM synthesis? | Eng | MEDIUM |
| 4 | MCA (India) DIN API has no official public endpoint — scraper needed or skip? | Eng | MEDIUM |
| 5 | Define "known shell address" blocklist — who maintains this list, and how is it distributed to installed laptops via auto-update? | Compliance | HIGH |
| 6 | Google CSE pricing at 10K+ queries/month — budget approval needed | Finance | MEDIUM |
| 7 | Re-screening cadence — how often should existing vendors be re-screened? | Compliance | LOW |
| 8 | How should IT back up or sync local laptop databases to protect against device loss/reimage — managed network drive, OneDrive sync, or a future optional team-sync server? | IT/Arch | HIGH |
| 9 | Should Deep Diligence be allowed to run on a partial intake (Section 3.5), or should the UI block the request until Category 2–4 fields are filled in? | Product | HIGH |
| 10 | Excel/SAP template versioning — how do we handle older template versions or changed SAP export layouts re-uploaded after a schema change? | Eng | MEDIUM |
| 11 | Confirm illustrative Quick Scan vs. Deep Diligence cost multiplier (Section 2.1) against actual contracted API rates | Finance | MEDIUM |
| 12 | Should the local database (SQLite/PostgreSQL) be additionally encrypted with SQLCipher, or is reliance on BitLocker full-disk encryption sufficient for compliance sign-off? | Security | HIGH |
| 13 | Device decommissioning procedure — who is responsible for confirming "Remove all local data" is run before a procurement laptop is reassigned or retired? | IT | HIGH |
| 14 | Should a future phase support live SAP system connectivity (RFC/OData) in place of manual export/import? | Product | LOW |
| 15 | What is the IT-approved distribution channel for the installer — SCCM, Intune, or a self-service internal portal? | IT | HIGH |

---

*Document Owner: Product & Architecture Team*
*Review Cycle: Before each sprint planning*
*Next Review: Prior to Engineering Kickoff*