# VendorLens — Tool & API Reference Matrix

Complete inventory of every external tool/API referenced in the PRD: purpose, what it requires to integrate, and the specific automation limitations/drawbacks of each.

---

## A. Entity & Corporate Registry Verification

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **OpenCorporates API** | Legal entity verification, incorporation status, registered address, officer list | API token (`api_token` param) | ~500 req/month or 10 req/min | Free tier ceiling hit almost immediately at any real scan volume; officer/filing data often incomplete for non-UK/US jurisdictions; many emerging-market entities not indexed at all, returning false negatives that look like "not found" |
| **GLEIF (Global LEI)** | LEI lookup, ownership hierarchy (Level 2 data) | None (public, no key) | No published hard limit, but fuzzy-match endpoint is rate-sensitive | Only covers entities that voluntarily registered for an LEI — most SMEs and most non-EU/non-financial companies have no LEI at all, so coverage gap is the norm, not the exception |
| **UK Companies House API** | UK entity status, officer list, PSC (ownership) | API key (Basic Auth, base64) | ~600 req/5 min per key | UK-only; officer endpoint requires a second sequential call per entity; no equivalent free API exists for most other countries, so this can't be templated globally |
| **MCA (India)** | Indian company registration, DIN verification | No official public API | N/A — must scrape or use paid aggregator | No sanctioned API exists; "integration" in practice means scraping a government portal, which breaks on any UI change and may violate terms of use |

---

## B. Sanctions, Watchlists & PEP Screening

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **OpenSanctions** | Entity + individual sanctions/PEP fuzzy matching across 100+ aggregated lists | API key (`Authorization: ApiKey`) | Concurrency-limited per key; exact RPS not published, enforced via 429 | Fuzzy match scores (0.60–0.85 "possible match") generate false positives requiring human review at scale; aggregation lag means newly added sanctions entries may not appear immediately; paid tier needed for production SLA |
| **OFAC SDN List (raw XML)** | US sanctions ground-truth | None (public download) | N/A — static file | Not an API — it's a downloadable XML/CSV that must be re-fetched and re-indexed on your own schedule; no webhook/push for updates, so staleness risk if refresh job fails silently |
| **UN Consolidated Sanctions List** | Global UN sanctions | None (public XML) | N/A — static file | Same as OFAC: self-hosted refresh required; XML schema has changed historically without notice, breaking parsers |
| **EU/UK (OFSI) Sanctions Lists** | EU/UK sanctions | None (public download) | N/A — static file | Same self-hosting burden; three separate lists (OFAC, UN, EU/UK) must be reconciled and deduplicated yourself if not using OpenSanctions as the aggregator |
| **Wikidata SPARQL** | PEP / politician identification fallback | None (public endpoint) | Query timeout ~60s, soft throttling on heavy queries | SPARQL query writing has a real learning curve; data is crowd-sourced so currency and accuracy of "current office" fields is inconsistent |

---

## C. Domain & Digital Infrastructure Intelligence

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **WHOIS API (WhoisXML or similar)** | Domain age, registrant info, registrar masking detection | API key | Varies by vendor, typically 500–1000 req/month free | Privacy/GDPR-driven WHOIS redaction (since 2018) means registrant contact fields are blank for most domains regardless of plan; burst-pattern detection can trigger temporary key suspension |
| **SSL Labs API** | Certificate validity/grade check | None (public, but rate-limited) | Explicitly rate-limited by SSL Labs ToS — bulk/automated use discouraged | SSL Labs' own usage policy asks for non-commercial, low-volume use; full scan (`all=done`) can take 60–120 seconds per domain — not suitable for synchronous Tier 1 flow without async polling |
| **VirusTotal (domain reputation)** | Malicious domain flagging | API key | 4 req/min, 500/day on free tier | Extremely low free-tier ceiling makes it unusable at any real concurrent scan volume without a paid plan |

---

## D. Adverse Media & News Intelligence

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **GDELT 2.0** | Global news search with tone/sentiment scoring | None (public, no key) | No official hard limit, but undocumented soft-throttling from high-volume static IPs | Coverage is real-time but historical depth/index quality varies by region and language; tone score is a blunt sentiment instrument — can mis-score satire, quotes, or neutral legal reporting as adverse |
| **NewsAPI** | Keyword + boolean adverse news search | API key | Free dev tier limited to 100 req/day **and only last 30 days of articles** | The 30-day history cap on free tier makes it nearly useless for due diligence (which needs years of history) — paid plan is mandatory for real use |
| **Google Programmable Search Engine (CSE)** | Site-scoped search (court records, regulators) | API key + Custom Search Engine ID (`cx`) | 100 queries/day free, then $5/1000 | At 3 queries per entity (as used in the pipeline), free tier supports only ~33 full scans/day; queries are billed per-call regardless of result quality |

---

## E. Beneficial Ownership & Address Verification

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **OpenOwnership (BODS)** | UBO/beneficial ownership graph | None (public register) | No published hard limit | Coverage is strong only in jurisdictions with mandatory UBO disclosure (UK, EU, partial elsewhere) — most of Asia, Middle East, and Africa have little to no data, producing systematic blind spots, not just occasional gaps |
| **Google Geocoding + Places API** | Address verification, shell-address cluster detection | API key (billing-enabled GCP project) | $200/month free credit, then pay-per-call | Requires a billing account even to start; abnormal/templated calling patterns (batch address lookups) can trigger temporary platform-level throttling independent of quota; "shell address" detection requires you to maintain your own blocklist — Google doesn't provide this |

---

## F. OCR & Document Processing

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **Tesseract 5 (local)** | OCR extraction from uploaded GST/invoice/license docs | None (self-hosted binary) | N/A — local compute only | Accuracy drops sharply on low-quality scans, skewed images, or non-Latin scripts; no built-in layout/table understanding, so structured fields (GSTIN boxes, tables) often need custom pre-processing |
| **AWS Textract (fallback)** | OCR fallback for complex documents | AWS account + IAM credentials | 1,000 pages/month free (first 3 months only) | Cost scales fast post-free-tier; introduces a hard cloud-vendor dependency the rest of the public-data-first architecture otherwise avoids |
| **pdf2image / poppler** | PDF-to-image conversion before OCR | System dependency (`poppler-utils`) | N/A | Not an API — a system binary dependency that must be present in every container image; multi-page PDFs at 300 DPI are memory-intensive at scale |

---

## G. Social / Digital Footprint (Highest Risk Category)

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **LinkedIn (company/personnel check)** | Bot-inflation, complaint detection on official handles | No public API for this use case | N/A | No legitimate API exists for this; any automated check is either manual review or scraping, which violates LinkedIn's ToS and triggers Cloudflare/PerimeterX-class bot detection almost immediately |
| **X / Twitter** | Same as above | API requires paid tier for meaningful access (v2 API) | Free tier removed read access for most use cases in 2023 | Read access for arbitrary account analysis now requires a paid API tier; scraping fallback is blocked aggressively by rate-limiting and login walls |
| **Facebook Graph API** | Same as above | App review + business verification required | Limited, app-specific | Requires Meta app review approval before any production access — not a quick integration; public page data access has shrunk significantly since 2018 platform lockdowns |
| **SERP API (generic, for social scraping fallback)** | Workaround for the above | Third-party API key (e.g., SerpAPI, ScraperAPI) | Paid, tiered by request volume | This is explicitly a scraping proxy service — it inherits all underlying target-site blocking risk, just outsourced; cost scales linearly with volume and offers no guarantee against future blocks |

---

## H. LLM Synthesis Layer

| Tool | Used For | Auth/Setup Required | Free Tier Limit | Automation Drawbacks |
|---|---|---|---|---|
| **Anthropic Claude API** | Adverse findings extraction, OCR entity parsing, JSON synthesis | API key | Pay-per-token, no perpetual free tier at production volume | Output is probabilistic — strict JSON schema adherence requires prompt discipline and still needs a parsing/validation layer for malformed responses; cost scales with the size of merged raw JSON per scan (large payloads = real token cost) |
| **OpenAI GPT-4o (alternative)** | Same as above | API key | Same cost model as Claude | Same structural drawbacks as Claude; switching providers mid-project means re-validating prompt behavior since JSON adherence and reasoning style differ across model families |

---

## Quick-Reference: Severity of Automation Risk by Category

| Risk Tier | Tools | Why |
|---|---|---|
| **Will break immediately at any real scale** | LinkedIn, X/Twitter, Facebook scraping; VirusTotal free tier; NewsAPI free tier | Either no legitimate API exists, or the free quota is too small to matter |
| **Will break under moderate concurrent load** | OpenCorporates, Google CSE, UK Companies House, WHOIS API | Free/standard tiers have real per-minute or per-day ceilings that 50-concurrent-scan targets will exceed |
| **Will degrade silently, not hard-fail** | GDELT, SSL Labs, OpenSanctions | No hard documented limit, but soft-throttling, slow responses, or quietly dropped requests under sustained automated load |
| **Structural coverage gaps, not rate issues** | OpenOwnership, GLEIF, MCA India | The problem isn't request volume — it's that the underlying data simply doesn't exist for large parts of the world |
| **Self-hosted maintenance burden, not API risk** | OFAC/UN/EU sanctions XML, Tesseract, pdf2image | These aren't rate-limited because they're not live APIs — risk is staleness or pipeline breakage on your own infrastructure |

---

## What This Table Implies for the Architecture

Every tool in categories with a "Free Tier Limit" column showing a real number needs either a paid plan budgeted before launch, or a caching/dedup layer to avoid re-querying the same entity. Every tool in Section G (Social Footprint) needs a product decision — not an engineering fix — about whether that feature ships in v1 at all, since no amount of retry logic solves "no legitimate API exists."