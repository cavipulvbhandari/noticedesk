# Before You Start — a 15-minute briefing

Read this before your first day. It is not a syllabus: nothing here needs to be
*learned* yet. It is the set of things you should have heard of, so that
nothing in your first week is a complete surprise. The deep version is
`docs/ONBOARDING-PREREQUISITES.md`.

## The two products, in one line each

- **NoticeDesk** — software for Indian CA (chartered accountant) firms that
  receives tax notices from the authorities, files them under the right client,
  and helps a partner draft the reply before the deadline.
- **Tender Pocket** — software that watches government tender portals for
  relevant bids, pulls in the documents, and tracks each bid through the
  internal process up to submission and outcome.

Both are small teams working on live systems with real users. Assume anything
you touch matters to somebody's day.

## Words you will hear in your first meeting

**NoticeDesk**

| Term | What it means |
|---|---|
| PAN | The 10-character permanent account number. It identifies a client, and it is the spine of the whole data model. |
| GSTIN | 15-character GST registration number. Positions 3–12 are the holder's PAN. One client can have many, one per state. |
| Notice | A letter from the tax department to a taxpayer. It has a type, a section of law, and a due date. |
| Matter | The case file a notice belongs to. Notices → matters → drafts. |
| Draft | The reply the firm sends back. Generating a good first draft is the product. |
| ASMT-10 | A common GST scrutiny notice. You will see it in the demo data. |
| Limitation period | The legal deadline for responding. Missing one harms the client — deadlines are not cosmetic here. |
| Tenant | One CA firm. The system holds many firms' data in one database, strictly separated. |

**Tender Pocket**

| Term | What it means |
|---|---|
| GeM | Government e-Marketplace — the portal the system scrapes for bids. |
| Tender / bid | A government body's published request to buy something. |
| EMD | Earnest money deposit — a refundable amount paid to participate in a bid. |
| Document fee | What it costs to obtain the bid documents. |
| Corrigendum | An official amendment to a published tender. Changes dates and specs after the fact. |
| Pre-bid | A meeting before the deadline where bidders can raise questions. |
| Specification compliance | Proving your product meets each technical clause of the tender. Largely what the AI features do. |
| MIS executive | The internal person a tender is assigned to. |

## Technology you will meet

You do not need to know these yet — you need to recognise the names.

**NoticeDesk:** Python, FastAPI, PostgreSQL, SQLAlchemy, Next.js and React,
TypeScript, Tailwind, Docker, and Claude / OpenAI for the AI features. Also
present but not your problem early on: Temporal, Terraform, AWS.

**Tender Pocket:** Java, Spring Boot, PostgreSQL with Hibernate/JPA, Jsoup for
web scraping, Apache POI and PDFBox for generating Word and PDF documents,
Tesseract for OCR, Gemini for the AI features, Docker.

**Both:** Git and GitHub, the command line, SQL, and reading other people's code.

## Five house rules

1. **Secrets never go in a commit.** Every API key, password and database URL
   comes from an environment variable. If you ever commit one, say so
   immediately — it is fixable, quietly hiding it is not.
2. **Don't refactor code you were not asked to refactor.** Some files are long
   and awkward. They also work, and they are load-bearing. Change the minimum
   the ticket needs.
3. **Never trust what an AI model returns.** Both products validate model output
   before it goes anywhere near a database or a user. That check is a feature,
   not friction.
4. **Ask early.** Two hours stuck is normal and fine. Two days stuck, silently,
   is not. Nobody will think less of you for a question on day three.
5. **Assume the data is real.** Client tax notices and live tender deadlines.
   Be careful with anything that sends email, writes to a shared database, or
   hits an external portal.

## What to have installed before day one

Git, Docker Desktop, an editor you are comfortable in (VS Code is fine), and —
depending on which project you are joining — Python 3.11 or a Java 21 JDK with
Maven. Node.js 20 either way. If any of this fights you, that is a fine first
question to ask.

## What to read first, in this order

1. The `README.md` of the repo you have been assigned.
2. `docs/architecture.md` (NoticeDesk) or `application.properties` and the
   Dockerfile (Tender Pocket) — to see how the pieces connect.
3. `docs/ONBOARDING-PREREQUISITES.md` — the full version of this page.

## What nobody expects of you on day one

To know the domain. To have used these exact frameworks. To write code without
asking questions. To be fast. What is expected: that you read carefully, keep
your changes small, and say what you don't understand.
