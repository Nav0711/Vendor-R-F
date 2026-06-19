# Vendor Risk Analysis - Free & Easy API Providers (MVP)

## 1. News Search

| Provider | Free Tier        | API Key Required | Ease of Access | Recommended |
| -------- | ---------------- | ---------------- | -------------- | ----------- |
| NewsAPI  | 100 requests/day | Yes              | Very Easy      | ✅           |
| GNews    | 100 requests/day | Yes              | Very Easy      | ✅           |

---

## 2. Company Website Discovery

| Provider                          | Free Tier          | API Key Required | Ease of Access | Recommended   |
| --------------------------------- | ------------------ | ---------------- | -------------- | ------------- |
| Google Programmable Search Engine | 100 queries/day    | Yes              | Easy           | ✅             |
| Serper API                        | 2,500 free queries | Yes              | Very Easy      | ✅ Best Option |

---

## 3. Google Maps / Business Presence

| Provider          | Free Tier              | API Key Required | Ease of Access | Recommended |
| ----------------- | ---------------------- | ---------------- | -------------- | ----------- |
| Google Places API | $200/month free credit | Yes              | Easy           | ✅           |

Use Cases:

* Business existence validation
* Address verification
* Business ratings
* Location confidence scoring

---

## 4. Open Company Data

| Provider       | Free Tier           | API Key Required | Ease of Access | Recommended |
| -------------- | ------------------- | ---------------- | -------------- | ----------- |
| OpenCorporates | Limited Free Access | Yes              | Medium         | ⚠️ Optional |

Use Cases:

* Global company lookup
* Corporate registry data
* Director information
* Registration status

---

## 5. Domain & Website Intelligence

| Provider          | Free Tier       | API Key Required | Ease of Access | Recommended |
| ----------------- | --------------- | ---------------- | -------------- | ----------- |
| WhoisXML API      | Small Free Tier | Yes              | Easy           | Optional    |
| Microlink API     | Free Tier       | Yes              | Very Easy      | ✅           |
| Clearbit Logo API | Free            | No               | Very Easy      | ✅           |

Use Cases:

* Website metadata
* Domain information
* Company logo retrieval
* Website validation

---

## 6. GST Verification

| Provider              | Free Tier | API Key Required | Recommended       |
| --------------------- | --------- | ---------------- | ----------------- |
| GST Sandbox TSP       | Yes       | Yes              | ✅ MVP Development |
| Masters India GST API | No        | Yes              | Production        |
| Clear GST API         | No        | Yes              | Production        |

Notes:

* No unlimited free production GST API exists.
* Use GST Sandbox TSP during development.
* Move to Masters India or ClearTax for production.

---

## 7. PAN Verification

| Provider | Free Tier | API Key Required | Recommended |
| -------- | --------- | ---------------- | ----------- |
| Karza    | No        | Yes              | Enterprise  |
| Signzy   | No        | Yes              | Enterprise  |
| Surepass | No        | Yes              | Enterprise  |

MVP Approach:

* Validate PAN format locally.

Regex:

```regex
[A-Z]{5}[0-9]{4}[A-Z]
```

---

## 8. MSME / Udyam Verification

| Provider | Free Tier | API Key Required | Recommended |
| -------- | --------- | ---------------- | ----------- |
| Karza    | No        | Yes              | Enterprise  |
| Signzy   | No        | Yes              | Enterprise  |

MVP Approach:

* Store MSME/Udyam Number
* Upload MSME Certificate
* Manual verification workflow

---

# Recommended MVP API Stack

## Required

```env
SERPER_API_KEY=
NEWS_API_KEY=
GOOGLE_MAPS_API_KEY=
OPENAI_API_KEY=
```

## Optional

```env
OPENCORPORATES_API_KEY=
MICROLINK_API_KEY=
WHOISXML_API_KEY=
```

---

# Vendor Risk Signals Supported

| Signal                       | Source                            |
| ---------------------------- | --------------------------------- |
| Website Exists               | Serper                            |
| Company Website Metadata     | Microlink                         |
| Google Business Presence     | Google Places                     |
| Business Location Validation | Google Places                     |
| News Coverage                | NewsAPI / GNews                   |
| Negative News Detection      | NewsAPI + AI                      |
| Company Registration Lookup  | OpenCorporates                    |
| Domain Intelligence          | WhoisXML                          |
| GST Validation               | GST Sandbox / Production GST APIs |
| PAN Format Validation        | Local Regex                       |
| MSME Tracking                | Manual / Enterprise APIs          |

---

# Recommended V1 Architecture

Vendor Import (SAP CSV/Excel)

↓

Vendor Name + GSTIN

↓

Serper Search

↓

Google Places

↓

News API

↓

AI Risk Analysis

↓

Risk Score

↓

Procurement Dashboard

This stack is sufficient for an internal procurement proof-of-concept without purchasing enterprise data-provider subscriptions.
