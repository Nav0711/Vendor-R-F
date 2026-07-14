# VendorLens

**Automated KYB & Vendor Due Diligence — Desktop Application**

VendorLens fans out to 12+ intelligence APIs in parallel, extracts adverse findings with Google Gemini AI, and surfaces risk across sanctions, litigation, media, and identity verification — all in a local Electron desktop app backed by FastAPI and MySQL.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Desktop app | Electron 42 · React 19 · TypeScript · Vite · Tailwind CSS 4 |
| Backend | Python 3.11 · FastAPI · asyncio · BackgroundTasks |
| Database | MySQL 9.x · SQLAlchemy ORM · pymysql |
| AI | Google Gemini 2.0 Flash (`google-genai`) |
| India KYC | AuthBridge (GSTIN · PAN · MSME · Court · Sanctions) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  VendorLens Desktop App                      │
│           Electron 42 · React 19 · TypeScript                │
│                                                              │
│  IntakeForm  ──▶  ScanSelector  ──▶  Dashboard              │
│  (manual / xlsx)   (quick / deep)   (5-tab report)          │
└───────────────────────────┬──────────────────────────────────┘
                            │  HTTP · localhost:8000
┌───────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                            │
│           Python 3.11 · asyncio · BackgroundTasks            │
│                                                              │
│  POST /intake        POST /scan        GET /scan/{id}/status │
│  POST /intake/excel                    GET /scan/{id}/report │
└───┬──────────────────────────────┬──────────────────────────┘
    │                              │
┌───▼──────────┐    ┌──────────────▼────────────────────────┐
│  MySQL 9.x   │    │  External API Layer (asyncio.gather)  │
│  4 tables    │    │  12+ providers · ~30 concurrent tasks │
└──────────────┘    └────────────────────┬──────────────────┘
                                         │
                             ┌───────────▼───────────┐
                             │   Gemini 2.0 Flash     │
                             │  findings + risk scores│
                             └───────────────────────┘
```

## Data Flow

```
Vendor Input  (manual form  OR  .xlsx batch upload)
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 1 · Parallel API Fan-out (~30 concurrent tasks)  │
│                                                         │
│  Corporate      Sanctions       News & Adverse Media    │
│  OpenCorp       OpenSanctions   GDELT · NewsAPI · Serper│
│                                                         │
│  Domain Intel   Address         India / AuthBridge      │
│  WHOIS · SSL    GooglePlaces    GSTIN · PAN · MSME      │
│  Microlink      Wikipedia       Court · Defaulting Dir  │
│                                 Global Sanctions · Email│
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼  (India vendors only)
┌─────────────────────────────────────────────────────────┐
│  Phase 2 · Alternate-name Enrichment                    │
│  GSTIN → registered trade names → full search re-run   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Gemini 2.0 Flash — Findings Extraction                 │
│  findings[]  ·  section_analysis{}  ·  article_scores[]│
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
             Risk Report → MySQL → Dashboard
```

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | 3.12 supported |
| Node.js | 20 LTS+ | For frontend & Electron |
| MySQL | 8.0+ or 9.x | Tables auto-created on first run |
| Git | any | |

---

## Setup

### Step 1 — MySQL

**Windows (user-local ZIP install, no admin required)**
```powershell
# Extract MySQL ZIP to C:\Users\<you>\Apps\mysql-9.x-winx64
# Initialize data directory (first time only):
C:\Users\<you>\Apps\mysql-9.x-winx64\bin\mysqld.exe --initialize-insecure --defaults-file="C:\Users\<you>\Apps\mysql-9.x-winx64\my.ini"

# Start MySQL (from project root):
.\start-mysql.ps1

# Set password + create database (first time only):
mysql -u root --connect-expired-password -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'vendorlens_dev'; FLUSH PRIVILEGES; CREATE DATABASE IF NOT EXISTS vendorlens CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

**macOS**
```bash
brew install mysql
brew services start mysql
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'vendorlens_dev'; FLUSH PRIVILEGES; CREATE DATABASE IF NOT EXISTS vendorlens CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

### Step 2 — Backend

**Windows**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Open .env and fill in your API keys

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**macOS / Linux**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Open .env and fill in your API keys

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 3 — Frontend

Open a **second terminal**. Backend must be running on port 8000 first.

**Windows**
```powershell
cd frontend
npm install
npm run dev             # Vite dev server → http://localhost:5173

# To run as Electron desktop app (third terminal):
npx electron .
```

**macOS / Linux**
```bash
cd frontend
npm install
npm run dev             # Vite dev server → http://localhost:5173

# To run as Electron desktop app (third terminal):
npx electron .
```

> **Mock mode** — Set `MOCK_API_CALLS=true` in `backend/.env` to run scans without consuming API credits. Returns realistic randomized findings for UI development.

---

## Environment File (`backend/.env`)

Copy from `backend/.env.example` and fill in your keys.

```env
# ── Database
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=vendorlens_dev
MYSQL_DB=vendorlens

# ── Required APIs
GEMINI_API_KEY=your_key
OPENSANCTIONS_API_KEY=your_key
SERPER_API_KEY=your_key
NEWS_API_KEY=your_key

# ── Optional APIs
OPENCORPORATES_API_KEY=
GOOGLE_MAPS_API_KEY=
MICROLINK_API_KEY=

# ── India only (AuthBridge)
AUTHBRIDGE_API_KEY=your_key
AUTHBRIDGE_API_SECRET=your_secret

# ── Dev
MOCK_API_CALLS=false
GEMINI_MODEL=gemini-2.0-flash
```

---

## API Keys

| Env Var | Provider | Status | Purpose |
|---------|----------|--------|---------|
| `GEMINI_API_KEY` | Google AI Studio (`AIza…`) *or* Vertex AI express mode (`AQ.Ab…`) | **Required** | LLM findings extraction & risk synthesis. The transport is auto-detected from the key prefix; set `GEMINI_API_BACKEND=studio\|vertex` to force it. |
| `OPENSANCTIONS_API_KEY` | OpenSanctions | **Required** | Sanctions & PEP screening |
| `SERPER_API_KEY` | Serper.dev | **Required** | Adverse web, reviews, profile, news |
| `NEWS_API_KEY` | NewsAPI.org | **Required** | Adverse media + regulatory news |
| `OPENCORPORATES_API_KEY` | OpenCorporates | Optional | Company registry (140+ jurisdictions) |
| `GOOGLE_MAPS_API_KEY` | Google Cloud | Optional | Address & operational status |
| `MICROLINK_API_KEY` | Microlink | Optional | Domain metadata (free tier available) |
| Wikipedia API | Wikimedia | Free | Always active — no key needed |
| `AUTHBRIDGE_API_KEY` | AuthBridge | India only | GSTIN · PAN · MSME verification |
| `AUTHBRIDGE_API_SECRET` | AuthBridge | India only | Court · Defaulting Director · Global Sanctions · Email |

> **Note** — All AuthBridge endpoint paths in `backend/app/api/endpoints.py` are marked `# CONFIRM with AuthBridge docs`. Verify each path against your plan's API documentation before going live.

---

## Project Structure

```
Project_1/
│
├── start-mysql.ps1              ← Windows user-local MySQL launcher
├── docker-compose.yml           ← Docker config (future use)
│
├── backend/
│   ├── .env                     ← your credentials (gitignored)
│   ├── .env.example             ← template for above
│   ├── requirements.txt
│   ├── Dockerfile               ← future Docker deployment
│   └── app/
│       ├── main.py              ← FastAPI app, routes, scan workflow
│       ├── api/
│       │   └── endpoints.py     ← all API client classes
│       ├── core/
│       │   ├── database.py      ← SQLAlchemy engine (MySQL + pymysql)
│       │   └── models.py        ← ORM models (4 tables)
│       └── services/
│           ├── data_aggregator.py  ← Phase 1+2 parallel API fan-out
│           ├── llm_service.py      ← Gemini 2.0 Flash integration
│           └── token_manager.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── electron/
│   │   └── main.ts              ← Electron entry point
│   └── src/
│       ├── App.tsx              ← Router: / → /scan/:id → /dashboard/:id
│       └── components/
│           ├── IntakeForm.tsx   ← vendor input form + Excel upload
│           ├── ScanSelector.tsx ← quick / deep scan choice
│           ├── Dashboard.tsx    ← top-level report view + polling
│           └── dashboard/
│               ├── OverviewTab.tsx    ← risk summary + source heatmap
│               ├── FindingsTab.tsx    ← adverse findings list
│               ├── NewsTab.tsx        ← AI-scored articles
│               ├── WebTab.tsx         ← domain, reviews, places
│               └── IndiaTab.tsx       ← AuthBridge checks (India)
│
├── inputs/
│   └── VendorLens_Intake_Template.xlsx   ← Excel template for batch
│
└── docs/
    ├── VendorLens_PRD_Techincal.md
    └── KEYS.md
```

---

## Database Schema

### `vendor_inputs` — intake records
| Column | Type | Notes |
|--------|------|-------|
| `input_id` | UUID PK | auto-generated |
| `legal_name` | VARCHAR(255) | indexed |
| `website_domain` | VARCHAR(255) | |
| `jurisdiction_country` | VARCHAR(10) | e.g. `IN`, `US` |
| `tax_identifier` | VARCHAR(100) | GSTIN for India |
| `pan_number` | VARCHAR(50) | India |
| `msmed_certificate_number` | VARCHAR(100) | India |
| `director_names` | JSON | array of strings |
| `corporate_email_domain` | VARCHAR(255) | used for email verification |
| `source_method` | VARCHAR(10) | `manual` or `excel` |

### `kyb_scans` — scan jobs
| Column | Type | Notes |
|--------|------|-------|
| `scan_id` | UUID PK | |
| `input_id` | FK | → vendor_inputs |
| `scan_type` | VARCHAR | `quick` or `deep` |
| `status` | VARCHAR | `PENDING` · `COMPLETED` · `ERROR` |
| `overall_risk_level` | VARCHAR | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `risk_score` | INTEGER | 0–100 |
| `raw_data_summary` | JSON | full aggregated report |

### `adverse_findings` — risk findings
| Column | Type | Notes |
|--------|------|-------|
| `finding_id` | UUID PK | |
| `scan_id` | FK | → kyb_scans |
| `category` | VARCHAR | `sanctions_match` · `news_adverse` · `regulatory_issue` … |
| `severity` | VARCHAR | `critical` · `high` · `medium` · `low` |
| `confidence_score` | INTEGER | 0–100 |
| `source_tool` | VARCHAR | originating API |
| `recommended_action` | VARCHAR | |

### `scan_subjects` — screened entities
| Column | Type | Notes |
|--------|------|-------|
| `subject_id` | UUID PK | |
| `scan_id` | FK | → kyb_scans |
| `subject_type` | VARCHAR | `entity` · `director` · `founder` |
| `is_pep` | BOOLEAN | Politically Exposed Person flag |

---

## Dashboard Tabs

| Tab | Visible | Contents |
|-----|---------|----------|
| **Overview** | Always | Overall risk level, finding count, per-source relevance/criticality heatmap |
| **Findings** | Always | Structured adverse findings sorted by severity with source citations |
| **News & Media** | Always | All articles from GDELT · NewsAPI · Serper with Gemini relevance scores |
| **Web & Reviews** | Always | Domain intel (WHOIS, SSL, Microlink), Google Places, review excerpts, Wikipedia |
| **AuthBridge Checks** | India only | Email verification · Global Sanctions · Court records · Defaulting Director · GSTIN/PAN/MSME |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/intake` | Submit a single vendor (JSON body) |
| `POST` | `/intake/excel` | Upload a batch `.xlsx` file |
| `POST` | `/scan` | Trigger scan for an existing `input_id` |
| `GET` | `/scan/{id}/status` | Poll scan status |
| `GET` | `/scan/{id}/report` | Retrieve full risk report |

---

## Scan Modes

| Mode | Sources | Phase 2 Enrichment | Duration |
|------|---------|--------------------|----------|
| **Quick** | Sanctions · GDELT · Serper adverse | No | ~15 s |
| **Deep** | All 12+ sources + India checks | Yes (if GSTIN present) | 30–60 s |

---

## Useful Commands

**Run tests**
```bash
# Windows
cd backend && .\venv\Scripts\activate && pytest tests/

# macOS
cd backend && source venv/bin/activate && pytest tests/
```

**Smoke-test backend imports**
```bash
python -c "from app.main import app; print('OK')"
```

**Type-check frontend**
```bash
cd frontend && npx tsc --noEmit
```

**Production frontend build**
```bash
cd frontend && npm run build
```

---

## Docker (Future Deployment)

`backend/Dockerfile` and `docker-compose.yml` are included but require WSL2 and admin access — not available on standard office laptops. Use the native setup above for local development. The Docker configuration is ready for IT-managed server or cloud deployment.

```bash
# Future: deploy with Docker Compose
cp backend/.env.example backend/.env  # fill in keys
docker compose up --build
# Backend:  http://localhost:8000
# MySQL:    port 3306 (internal)
```

---

## Excel Intake Template

Use `inputs/VendorLens_Intake_Template.xlsx` for batch uploads. Column mapping is flexible — headers are matched by keyword, not exact name.

| Column | Recognized Aliases |
|--------|--------------------|
| `legal_name` | name, supplier, vendor name |
| `website_domain` | domain, website |
| `jurisdiction_country` | country |
| `tax_identifier` | tax no, gstin |
| `pan_number` | pan, pan no |
| `director_names` | directors, board |
| `founder_ceo_name` | ceo, founder |
| `corporate_email_domain` | email domain |
