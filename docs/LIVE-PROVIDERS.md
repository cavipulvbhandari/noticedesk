# Wiring up real Anthropic + real Google Document AI

The smallest possible step from "stub demo" to "real intelligence in the
pipeline". Roughly 30 minutes of clicking + 5 minutes of env-var setting.
After this:

- The drafting agent calls Claude Opus 4.7 (not the canned template).
- The OCR pipeline calls Google Document AI on real PDF bytes (not the
  hash-based placeholder).
- The demo banner's LLM and OCR chips both turn green.

Auth, storage, citations, workflow, email — all still stubbed. Those land
in a later step (see `docs/PRODUCTION-CONFIG.md`).

---

## 1. Anthropic — 5 minutes

### 1.1 Get a key

- `console.anthropic.com` → API Keys → **Create Key**.
- Settings → Limits → set a monthly cap (₹2,000 is plenty for the first
  ten demos; production cap is ₹30,000-50,000 per pilot firm).
- Copy the key — it starts with `sk-ant-`.

### 1.2 Export env vars

```bash
export ANTHROPIC_API_KEY=sk-ant-…
export LLM_PROVIDER_PRIMARY=anthropic
export ANTHROPIC_MODEL=claude-opus-4-7   # default; or claude-sonnet-4-6 for ~5× cheaper
```

That's it for Anthropic config.

---

## 2. Google Document AI — 25 minutes

### 2.1 Enable the API

- GCP Console → **APIs & Services → Library** → search "Document AI API"
  → **Enable** on a project you control. (Create a new project if you
  don't already have a NoticeDesk-scoped one.)

### 2.2 Pick a region

Mumbai (`asia-south1`) for DPDP residency. If you're only demoing and
don't care yet, `us` works and processors are sometimes faster there —
but switch to `asia-south1` before a paid firm.

### 2.3 Create a processor

- **Document AI → Processors → Create Processor** → **Form Parser**.
  (Form Parser is the fast general-purpose extractor. The Custom
  Extractor is what you'd train later on your own labelled notices.)
- Region: `asia-south1` (or `us`).
- Name: `noticedesk-form-parser`.
- After creation, copy the **Processor ID** from the address bar
  (`…/processors/<id>/edit`). Looks like `e8c1a4b9d2f3e7a5`.
- Also note: the **Project ID** (Console top bar) and the **Location**
  you picked.

### 2.4 Create a service account + key

- IAM & Admin → **Service Accounts → Create Service Account**.
  - Name: `noticedesk-docai`
  - Role: **Document AI API User** (`roles/documentai.apiUser`). Don't
    grant broader scope.
- Open the account → **Keys → Add Key → Create new key → JSON**.
- Save the downloaded JSON somewhere the API process can read.
  - Local Mac dev: `~/.noticedesk/docai-sa.json` is conventional.
  - Production: `/etc/noticedesk/docai-sa.json` mounted from a secret.
- **Never check this file into git.**

### 2.5 Export env vars

```bash
export OCR_PROVIDER_PRIMARY=google_doc_ai
export GOOGLE_DOC_AI_PROJECT_ID=your-gcp-project
export GOOGLE_DOC_AI_LOCATION=asia-south1
export GOOGLE_DOC_AI_PROCESSOR_ID=e8c1a4b9d2f3e7a5
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/.noticedesk/docai-sa.json
```

The Google SDK reads `GOOGLE_APPLICATION_CREDENTIALS` automatically; the
provider class never touches the path itself.

---

## 3. Install the SDKs

Both are optional extras in `apps/api/pyproject.toml`. One command:

```bash
make demo-live-install
# = cd apps/api && .venv/bin/pip install -e ".[live]"
```

That installs `anthropic>=0.34.0` and `google-cloud-documentai>=2.27.0`
alongside whatever you already had.

---

## 4. Preflight — call both providers once each

```bash
make demo-preflight
```

What you should see if everything's wired:

```
== NoticeDesk live-provider preflight ==

LLM provider: anthropic
  ✓ anthropic · claude-opus-4-7 · 1.24s · 'ok'
    tokens in=24 out=2

OCR provider: google_doc_ai
  ✓ google_doc_ai · 1.82s · 1 pages · text='Hello from NoticeDesk preflight'

Citation provider: stub
  stub mode — set CITATION_PROVIDER=indiankanoon to flip

All configured providers responded.
```

If you see `✗`:
- **anthropic auth failure** → check the key starts with `sk-ant-` and
  has the model permission. Re-create the key.
- **`google-cloud-documentai not installed`** → `make demo-live-install`
  didn't run successfully. Re-run.
- **Doc AI permission denied** → service account role isn't
  `documentai.apiUser`, or `GOOGLE_APPLICATION_CREDENTIALS` points at a
  file the process can't read. Run `cat
  "$GOOGLE_APPLICATION_CREDENTIALS"` to confirm.
- **Doc AI 404** → processor ID typo or processor lives in a different
  region than `GOOGLE_DOC_AI_LOCATION`.

---

## 5. Restart uvicorn + verify in the UI

```bash
cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000
```

Open the dashboard. The gold demo banner at the top should now read:

```
Demo mode · LLM Claude · claude-opus-4-7 · OCR google_doc_ai · Citations stub · Auth dev-cookie · Storage local /tmp
```

LLM and OCR chips both green; the others stay grey.

### Live e2e walk

```bash
make demo-walk PDF=~/some-real-notice.pdf
```

Watch the script:
- Upload completes
- OCR polls: pending → in_progress → completed (Google Doc AI ran, real text in `documents_inbox.ocr_text`)
- Parse polls: completed (Claude parsed the OCR text — no canned filename match needed)
- Route: routed (PAN reconciled to a seeded client; or anomaly if the PDF is for a client you haven't seeded)
- Draft generates against the parsed notice + matter context

The whole pipeline takes 90-120s end-to-end with real Anthropic + real Doc AI. The draft pane in the UI shows real Claude prose with citations the verifier will mark VERIFIED_PARTIAL (stub citation provider returns `partial` for unknown cases by default — flip to IndianKanoon when you're ready).

---

## 6. Cost watch

Run `make demo-preflight` after every change. It prints token counts:

```
tokens in=24 out=2
```

A real draft generation is roughly:
- Parsing: ~3K tokens in, ~1K out (one call per upload)
- Drafting: ~8K tokens in, ~6K out (one call per draft)
- Total per uploaded notice end-to-end: ~₹4-8 at Opus 4.7 list.

Doc AI Form Parser: ₹0.10-0.15 per page (₹150 per 1000 pages).

A 10-minute partner demo = roughly ₹40-80 of API spend. Keep your
monthly cap at ₹2,000 and you can run ~25-50 full demos before topping
up.

---

## 7. What you've NOT done yet

Six surfaces are still stubbed:

| Surface | Cost to remove | When |
|---|---|---|
| Citation verification | 15 min + ₹3K/mo paid tier | Before signing a firm |
| Auth (Clerk) | ~1 day code + ₹1.5K/mo | **Required** before signing a firm |
| Storage (S3) | 2 hrs + AWS | Required before signing a firm |
| Workflow (Temporal) | 1 day code + ₹800/mo | Recommended (UX) |
| Email inbound (SES) | 4 hrs + domain | Required for the email-ingestion feature |
| Sentry | 10 min + ₹2K/mo | Required for production |

Full guide for each in `docs/PRODUCTION-CONFIG.md`.
