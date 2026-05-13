# Partner demo — walkthrough

A 25-minute structured walkthrough for the first CA-partner demo. Times are
rough; adjust to the partner's questions.

## Prep — 15 minutes before the partner sits down

1. **Set environment variables in the shell that will run uvicorn:**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-…              # real Claude
   export LLM_PROVIDER_PRIMARY=anthropic
   export CITATION_PROVIDER=indiankanoon          # optional but punchy
   export INDIANKANOON_API_TOKEN=…                # if you have one; stub is fine otherwise

   # The OCR provider is still the stub by default (Google Doc AI is the
   # production option). To make the stub-parser produce a sensible canned
   # response for ANY PDF the partner uploads — instead of only
   # "GST Notice.pdf" / "drc-01.pdf" — set:
   export STUB_DEFAULT_CANNED=acme_mh_asmt10      # any .pdf → Acme MH ASMT-10
   ```

2. **Reset the demo dataset** so the partner sees a known state:
   ```bash
   make db-reset
   ```
   Expected: 5 clients · 40 notices · 30 matters.

3. **Pre-generate a draft on the Acme DRC-01 (n3)** so you don't burn 60s
   live. The pre_seed_draft script below does this; run once before the demo.
   See `scripts/preseed_demo_draft.py`.

4. **Start both servers** and confirm the demo banner shows "Claude · claude-opus-4-7":
   ```bash
   # Terminal 1
   cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000
   # Terminal 2
   cd apps/web && npm run dev
   ```

5. **Open `http://localhost:3000/dashboard`** in a clean browser window
   (no extra tabs). Log in with the prefilled seed IDs.

6. **Confirm**: the demo banner at the top should read
   `Demo mode · LLM Claude · claude-opus-4-7 · …`. If it says "stub", your
   env vars didn't propagate to the uvicorn process.

## The 25-minute walkthrough

### 0:00 — 0:03 — Dashboard ("today, in one screen")

Open `/dashboard`. Talking points:
- "Eight states of every notice across the firm, with counts."
- "Filter pills — All partners / Both laws / All clients / All states — let
  the partner slice the same view."
- Click **Due Date Over** → red highlight + Acme DRC-01 visible.
- "One overdue notice across the firm right now. The partner sees this in
  the morning standup."

### 0:03 — 0:08 — Clients

Click **Clients** in the sidebar.
- "Five clients. PAN is the canonical identifier — once set it can't
  change. Every client has exactly one Income Tax registration and zero or
  more GST registrations."
- Click **Acme Industries Private Limited**.
- Two-card layout: IT (6 active notices) + GST (3 state registrations,
  Maharashtra / Gujarat / Karnataka).
- "Each state is a separate ledger. A Maharashtra notice never pulls facts
  from Gujarat. We'll prove that in a moment."

Click **+ Add GST registration**. Type the matching Maharashtra GSTIN
`27AAACA9876B1ZK`. Show the PAN-derivation box:
- GSTIN entered → State 27 / Maharashtra → Derived PAN AAACA9876B → matches
  client PAN → ✓ MATCH. Save enabled.

Clear the field. Type Sunteck's GSTIN `27AABCS5678C1Z7`:
- Derived PAN AABCS5678C ≠ AAACA9876B → ✗ MISMATCH with the exact line
  "Positions 3-12 derive AABCS5678C, which is a different PAN."
- Save stays disabled.

Close the modal.

### 0:08 — 0:14 — Notice routing (parse + reconciliation)

Click **Inbox** in the sidebar.
- "Three documents awaiting routing. PDF upload, email forward, mobile
  capture all land here."
- i1 (clean route), i2 (PAN extracted but client doesn't exist),
  i3 (Acme PAN matches but a new GSTIN was found in the document).
- "Routing isn't auto-confirmed when there's ambiguity. The partner
  resolves anomalies manually — Add Client, Confirm new GST registration,
  or Reject."

Show i3: click the row → side panel opens → click **Add this Karnataka
GSTIN to Acme**. The notice routes to its matter; the registration is
created.

**Live upload (the killer demo):** drag any PDF the partner has on their
laptop into the upload zone. With `STUB_DEFAULT_CANNED=acme_mh_asmt10`
set, the file flows through:
1. Storage write
2. OCR (stub or Google Doc AI)
3. Parse via Claude (or the canned fallback)
4. PAN/GSTIN reconciliation against the client tree
5. Matter + notice creation

Inbox row state changes live — OCR "pending → in_progress → completed",
then routing fires and the row disappears with a toast pointing at the
new matter. The partner experiences "I dropped a file in and 4 seconds
later I'm on a matter view with the parsed facts."

For a hands-off rehearsal of the same path (run from a second terminal
on your laptop, **not** in front of the partner):

```bash
STUB_DEFAULT_CANNED=acme_mh_asmt10 make demo-walk
# or with their real PDF:
STUB_DEFAULT_CANNED=acme_mh_asmt10 make demo-walk PDF=~/Downloads/some-notice.pdf
```

`make demo-walk` posts the file, polls the inbox row through every
status transition, and prints the final notice + draft URL. Use it to
sanity-check the pipeline 5 minutes before the partner sits down.

### 0:14 — 0:20 — Matter view + Draft reply

Back in the dashboard, click any Acme row → matter view loads.

Header card:
- Notice type, issue ("ITC denial — fake vendor allegation, ₹22.7 lakh"),
  identity context (Maharashtra · 27AAACA9876B1Z5 · FY 2021-22).
- Clickable red **Due Date Over** lifecycle chip → two-step wizard.
- 8-field meta grid: PAN, GSTIN, FY/AY, Authority, DIN, Due date with
  days remaining, Assigned to.

Click the lifecycle chip → pick **In Progress** → no reason needed → Confirm
→ chip flips. "Lifecycle transitions are audit-logged with risk-tier; the
brief required reasons for closed/on_hold/reply_submitted. Watch."

Click chip again → **Reply Submitted** → reason textarea appears with red
required mark → confirm without reason → error → type a reason → Confirm.
Switch to **Timeline tab** → shows both events with reason in italics and
risk_tier.

### 0:20 — 0:30 — The drafting agent (the centrepiece)

Switch to **Draft reply** tab.

If you pre-seeded a draft, it's already there. Skip the Generate step
and walk straight into the split-pane:
- Left: 13 sections (Sec 08 Cross-Examination Request skipped because no
  third-party statement).
- Right: verification panel.
- "Section 06 cites real Indian case law. Each citation was independently
  verified against IndianKanoon — green chip means VERIFIED with a source
  URL, amber means partial match, red means we stripped it because we
  couldn't confirm it. **No unverified citation reaches your screen.**"

Show the Citations tab on the right. Click the source URL on one citation
→ opens IndianKanoon.

Click **Source map** tab → "Every section maps back to a source: the
parsed notice JSON, the documents you attached, the citation cluster, or
explicitly the agent's synthesis. The partner can audit where any fact
came from."

Click **Edit** on Section 4 (Issue-wise Response). Type a partner-flavoured
sentence. Save as new version → toolbar flips to v2 → toast confirms. "Edit
history is preserved as immutable versions; we never overwrite v1."

Click **Compare versions** → side-by-side diff opens. Your edit shows up
in green on the right, the old text in red on the left.

Click **Export to Word** → **Filing version**. Open the .docx:
- Cover sheet (client name, PAN, GSTIN, FY, authority, due date).
- Times New Roman, A4, no hyperlinks.
- Sections 1-12 + 15 only. **No Internal Partner Note.**
- Page numbers in footer.

"That's the filing-grade output. The partner reviews, signs, and files."

Repeat for **Internal review version** → shows the partner note at the end
("Officer historically open to reconciliation-based closure…"). "This
section stays inside the firm. It's never in the version you give the
client or send to the Department."

### 0:30 — end — Q&A

Likely questions to anticipate:

- **"What about my limitation dates?"** → "Reminder + limitation
  engine is Phase 2."
- **"Can it file the reply on the GST portal automatically?"** → "No.
  We never auto-file. Phase 2 will pre-fill the form for you to review,
  but the click always belongs to the partner."
- **"What if Claude hallucinates a case?"** → "Every citation is
  verified against IndianKanoon (or paid Tier 2/3 in Phase 2). Failures
  are stripped and footnoted, so the partner sees what was removed and
  why."
- **"How is my data protected?"** → "DPDP-compliant: data resident in
  ap-south-1. Per-tenant row-level security at the database layer (we
  don't even trust application code to filter by firm). Audit-log is
  append-only at the trigger level — no one can delete the record of
  what was generated or who edited it."
- **"What's the price?"** → That's your conversation, not the demo's.

## What to NOT show in the first demo

- Settings → Portal Connectors → it shows "Coming Soon" cards. Don't
  navigate there unless asked; it surfaces what's deferred.
- Documents tab drag-drop → safe to show only if you have a sample PDF
  ready; otherwise skip.
- The dev login form → demo banner makes it clear we're in dev; you
  shouldn't sign out and back in mid-demo.

## After the demo

- Run `make db-reset` again so the next session starts clean.
- Capture any partner concerns in a Linear / Notion log; the brief has
  explicit Phase 2/3 carve-outs but the partner may surface something
  new.
