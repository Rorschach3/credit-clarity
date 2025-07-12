<div align="center">

![Credit Clarity Logo](https://i.ibb.co/21wJjHWr/Credit-Clarity-Ghost.png)
</div>

<h1 align="center"><span style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #2C3E50;">CreditClarityAI</span></h1>

<p align="center"><em>AI-powered credit report analysis and dispute‐letter generation to improve your credit score.</em></p>

---

<div align="center">

**Table of Contents**

1. [Overview](#overview)
2. [Key Metrics](#key-metrics)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Screenshots](#screenshots)
6. [Getting Started](#getting-started)
7. [Project Structure](#project-structure)
8. [FAQ Highlights](#faq-highlights)

</div>

---

## <span style="color: #16A085;">Overview</span>

<p>
Created by a former credit repair specialist, <strong>CreditClarityAI</strong> uses OCR + AI to:
</p>

<ul>
  <li>Identify credit‐report errors with high accuracy</li>
  <li>Generate customized, FCRA-compliant dispute letters</li>
  <li>Automate the credit-repair workflow</li>
</ul>


---


## <span style="color: #D35400;">Features</span>

- <strong>Dispute Generator</strong>: Upload or enter report, AI drafts letters.
- <strong>OCR Integration</strong>: Scan PDFs & images for errors.
- <strong>Custom Templates</strong>: Review & edit letters pre-send.
- <strong>Progress Dashboard</strong>: Track submissions, responses, score changes.

---

## <span style="color: #27AE60;">Tech Stack</span>

| Layer          | Technology                    |
| -------------- | ----------------------------- |
| Frontend       | React, Tailwind CSS           |
| Backend        | Flask (Python)                |
| OCR Processing | Tesseract, OpenCV             |
| AI / NLP       | PyTorch, Hugging Face         |
| Database       | PostgreSQL                    |
| Auth           | JWT / Flask-Login             |
| Deployment     | Docker, AWS Elastic Beanstalk |

---

## <span style="color: #34495E;">Screenshots</span>

<p align="center">
  <img src="./images/dashboard.png" alt="Dashboard" width="600"/>
  <br><em>Dashboard</em>
</p>
<p align="center">
  <img src="images/disputeGenerator.png" alt="Generator" width="600"/>
  <br><em>Dispute Generator</em>
</p>
<p align="center">
  <img src="images/disputes.png" alt="Disputes" width="600"/>
  <br><em>Disputes</em>
</p>

---

## <span style="color: #7F8C8D;">Getting Started</span>

<ol>
  <li>Clone  
    <pre><code>git clone https://github.com/rorschach3/credit-clarity-ai-assist.git
cd credit-clarity-ai-assist</code></pre>
  </li>
  <li>npm install  
    <pre><code>npm install</code></pre>
  </li>
  <li>Configure  
    <pre><code>.env.example
# Fill in your secrets from the .env example file</code></pre>
  </li>
  <li>Run  
    <pre><code>npm run dev</code></pre>
  </li>
  <li>Test
    <pre><code>run npm test</code></pre>
  </li>
  <li>Extended Tests  
    <pre><code>npm run test:coverage</code></pre>
</ol>

> Open <a href="http://localhost:8080">localhost:8080</a> in your browser.

---

## <span style="color: #2E86C1;">Project Structure</span>

```text
creditclarityai/
├─ app/
│  ├─ templates/   # Jinja2 HTML
│  ├─ static/      # CSS, JS, images
│  ├─ ocr/         # OCR modules
│  ├─ ai/          # Model code
│  ├─ auth.py      # Auth logic
│  └─ disputes.py  # Dispute routes
├─ migrations/     # DB migrations
├─ tests/          # Unit & integration tests
├─ requirements.txt
├─ .env.example
└─ run.py          # App entry point
```
<p style="text-align: center; font-weight: bold; font-size: 1.5rem;">
 Tradeline Data Flow with Duplicate Prevention
</p>

```mermaid
graph TD
    A[User Uploads PDF] --> B(OCR Process)
    B --> C{Extract Raw Tradeline Text}
    C --> D[LLM Parser]
    D --> E{Parsed Tradeline Data}
    E -- Add user_id and enrich data --> F[Edge Function: add-tradeline]
    F --> G{Validate Tradelines
    with Zod Schema}
    G -- If validation fails --> H[Return 400 Error]
    G -- If validation passes --> I{Check for Existing Tradelines}
    I -- Conflict/Duplicate found --> J[UPSERT: Update Existing Tradeline]
    I -- No conflict/New tradeline --> K[UPSERT: Insert New Tradeline]
    J --> L[Supabase Database: tradelines table]
    K --> L
    L --> M[Return Success Response]
    F -- Database/Function Error --> N[Return 500 Error]
  ```
---

## <span style="color: #2C3E50;">FAQ Highlights</span>

> ### Why are dispute letters effective?
>
> Under the FCRA, bureaus must investigate disputes within 30 days. If they do not verify within 30 days they must remove inaccuracies.

> ### How does AI boost success?
>
> Trained on thousands of letters, our models optimize tone, legal wording, and proof patterns.

> ### What can be disputed?
>
> Late payments, collections, charge-offs, repossessions, bankruptcies, student loans, auto loans, mortgages, child support.

For full FAQs, see [`faq.html`](app/templates/faq.html)

------------------------

Tradeline data extraction workflow: 
```mermaid
flowchart TD
    A[User]  --> B["Uploads PDF or document via Web App"]
    B --> C["document-ai-parser.ts Frontend"]
    C -- Converts file to base64 if needed --> D["Converts file to base64 if needed"]
    D -- Sends base64 file to FastAPI backend endpoint --> E["main.py FastAPI Backend"]
    E -- Tries direct Google Document AI Python client --> F["Google Document AI Cloud OCR"]
    F -- Extracted Text --> G["Extracted Text"]
    E -- If Python client fails or unavailable --> H["Fallback Proxy server document-ai.js on Node/Express"]
    H -- Google Document AI via REST API --> I["Google Document AI via REST API"]
    I -- Extracted Text --> J["Extracted Text"]
    E -- If Node proxy unavailable --> K["Supabase Edge Function for OCR optional"]
    K -- Extracted Text --> L["Extracted Text"]
    E -- Text Extraction Success --> M["Text Extraction Success"]
    M --> N["llm_parser.py Backend LLM Parsing"]
    N -- Parsed Tradeline Data JSON --> O["Parsed Tradeline Data JSON"]
    O -- Backend returns parsed data to Frontend --> P["Backend returns parsed data to Frontend"]
    P -- Frontend displays results and saves to Supabase DB --> Q["Frontend displays results and saves to Supabase DB"]
```

```mermaid
flowchart TD
    A[User (Frontend)] --> B[Uploads PDF or document via Web App]
    B --> C[document-ai-parser.ts (Frontend)]
    C --> D[Converts file to base64 (if needed)]
    D --> E[Sends base64 file to FastAPI backend endpoint]
    E --> F[main.py (FastAPI Backend)]
        v
[ document-ai-parser.ts (Frontend) ]
        |
        |---> Converts file to base64 (if needed)
        |
        v
[ Sends base64 file to FastAPI backend endpoint ]
        |
        v
[ main.py (FastAPI Backend) ]
        |
        |---> Tries direct Google Document AI (Python client)
        |         |
        |         |--(If credentials available)
        |         v
        |     [ Google Document AI (Cloud OCR) ]
        |         |
        |         v
        |     [ Extracted Text ]
        |
        |---> If Python client fails or unavailable:
        |         |
        |         v
        |     [ Fallback: Proxy server (document-ai.js on Node/Express) ]
        |         |
        |         v
        |     [ Google Document AI via REST API ]
        |         |
        |         v
        |     [ Extracted Text ]
        |
        |---> If Node proxy unavailable:
        |         |
        |         v
        |     [ Supabase Edge Function for OCR (optional) ]
        |         |
        |         v
        |     [ Extracted Text ]
        |
        v
[ Text Extraction Success ]
        |
        v
[ llm_parser.py (Backend LLM Parsing) ]
        |
        v
[ Parsed Tradeline Data (JSON) ]
        |
        v
[ Backend returns parsed data to Frontend ]
        |
        v
[ Frontend displays results and saves to Supabase DB ]
```

Example Tradeline json
```json
{
  "creditor_name": "Bank or Credit Union",
  "account_number": "000000XXXX",
  "account_balance": "$0",
  "created_at": "0000-00-00",
  "credit_limit": "$0",
  "monthly_payment": "$0",
  "date_opened": "00/0000",
  "is_negative": false,
  "account_type": "credit_card, collection, mortgage, etc.",
  "account_status": "closed",
  "dispute_count": 0
}