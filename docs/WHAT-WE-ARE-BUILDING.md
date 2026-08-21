# What We Are Building

For new interns. No technical knowledge needed to read this. Read it before
you look at any code.

There are two products. They are for two completely different kinds of
customer. But underneath, they are the same shape, and it helps to see that
early:

> **Important paper arrives. A deadline comes with it. A person has to read
> the paper, understand it, and produce a document in reply — correctly and on
> time. We build software that does the reading, the remembering, and the
> first draft. A human still checks and approves everything.**

---

# Part 1 — NoticeDesk

## Who uses it

Chartered accountant firms in India. A "CA firm" is a company of accountants.
Businesses and individuals hire them to handle their taxes.

One firm may look after 200, 500, or 2,000 clients. The firm is responsible
for keeping every one of those clients out of trouble with the tax department.

## The problem we are solving

The Indian tax department sends letters to taxpayers. These letters are called
**notices**.

A notice might say something like:

> "In your tax return for the year 2023–24, you claimed ₹8,00,000 of business
> expenses. Please explain this amount and provide supporting documents.
> Reply within 15 days."

Here is what makes this hard for the CA firm:

1. **Notices arrive from everywhere.** Some by email. Some as paper post. Some
   only appear when someone logs in to a government website and checks. There
   are several different government websites.
2. **There are many of them.** A firm with hundreds of clients receives
   notices constantly.
3. **Every notice has a deadline.** Usually 15 or 30 days. Sometimes the law
   sets a final date after which the firm simply cannot reply at all.
4. **Missing a deadline is serious.** The client can be fined. The client can
   lose the case automatically. The firm can be blamed and sued.
5. **Replying takes real skill.** A reply is a formal legal letter. It has to
   quote the correct section of the law, answer exactly what was asked, and
   attach the right proof.

Today most firms manage all of this with an Excel sheet, a shared email
inbox, and someone's memory. Things get missed. That is the problem.

## What NoticeDesk does

Think of it as an assistant that never forgets and never sleeps.

**Step 1 — The notice comes in.**
Someone uploads a PDF or a photo of the letter. Or the notice is emailed to a
special address that belongs to the firm, and it arrives automatically.

**Step 2 — The computer reads it.**
Many notices are scans — a photograph of a printed page. A computer cannot
read a photograph directly. So we first run **OCR**, which stands for Optical
Character Recognition. That is just a technical way of saying: *turn a picture
of text into actual text*.

**Step 3 — AI pulls out the important facts.**
An AI model reads the text and picks out the things that matter: which
taxpayer, which tax, which section of law, what is being asked for, and the
deadline date.

**Step 4 — The system files it under the right client.**
This is the most important step in the whole product.

Every taxpayer in India has a **PAN** — a ten-character code, like
`ABCDE1234F`. It is unique to that person or business. NoticeDesk uses PAN as
the one true identity of a client. Everything hangs off it.

Deciding which client a notice belongs to is done by **fixed rules, not by
AI**. That is a deliberate choice. If AI guesses wrong here, one firm's
confidential tax notice lands in another client's file. That is the single
worst thing this product could do. So we do not let AI make that decision.

**Step 5 — A case file opens, and the deadline goes on the calendar.**
We call the case file a **matter**. The partner can now see the deadline
coming.

**Step 6 — The system says what to collect.**
Before you can write a reply, you need proof: invoices, bank statements,
contracts. The AI reads the notice and produces a checklist of what to ask the
client for.

**Step 7 — AI writes the first draft of the reply.**
Not the final letter. A first draft — with the legal points laid out and
relevant past court decisions referenced. The partner reads it, edits it,
and takes responsibility for it. Then it can be exported as a Word document
and sent.

## What makes it difficult

- **Notices look different every time.** Different departments, different
  states, different years, different layouts. There is no single format.
- **The scans are often bad.** Crooked, dark, photographed on a phone.
- **AI can be confidently wrong.** It can invent a PAN number that looks
  perfectly real. So we check every single field the AI returns and throw away
  anything that does not pass. Never assume the AI is right.
- **Firms must never see each other's data.** Many CA firms use the same
  system. The database has a strict wall between them, enforced by the
  database itself and not just by the code.

## What success looks like

A partner opens NoticeDesk in the morning. In one screen they see every notice
that arrived, who it belongs to, what is due this week, and a draft reply
already waiting for the urgent ones. Nothing was missed. Nobody had to check
five websites.

---

# Part 2 — Tender Pocket

## Who uses it

A company that sells products to the government. In our case, mainly medical
equipment — hospital beds, ECG machines, operating theatre equipment,
laboratory analysers, and so on.

Their customers are government hospitals, health departments, and medical
colleges.

## The problem we are solving

Governments cannot simply buy things. By law, they must announce publicly what
they want to buy and let companies compete. That public announcement is called
a **tender**.

A tender looks roughly like this:

> "District Hospital, Nashik invites bids for the supply of 50 ICU beds
> meeting the attached technical specification. Estimated value ₹1.2 crore.
> Earnest money deposit ₹2,40,000. Bids close 12 September, 3:00 PM."

To win business, our customer has to find these announcements and respond to
them properly. Here is why that is painful:

1. **There are thousands of tenders.** They are published on government
   websites — the biggest is **GeM**, the Government e-Marketplace — and sent
   out by subscription email services. Almost all of them are irrelevant. A
   company selling ICU beds does not care about a tender for road repair.
   Somebody has to sift through them every single day.
2. **Each response is a thick packet of paperwork.** Company documents, price
   sheets, certificates, and a point-by-point statement showing that your
   product meets every technical requirement in the tender.
3. **The technical requirements are long and fussy.** A single tender may list
   sixty separate specifications. You must answer every one.
4. **You must pay a deposit to take part.** This is the **EMD** — earnest
   money deposit. Real money, paid before the deadline, refunded later.
5. **Deadlines are absolute.** One minute late and your bid is not accepted,
   no matter how good your price was.
6. **Tenders change after publication.** The government issues a
   **corrigendum** — an official correction. Dates move. Specifications
   change. If you miss the corrigendum, you prepare the wrong bid.

So the work is: find the right tenders, keep track of every deadline, and
produce a large correct document pack for each one. Done by hand, this is
several people's full-time job, and mistakes are expensive.

## What Tender Pocket does

**Step 1 — It goes looking, every day, by itself.**
The system automatically checks the GeM website and an email inbox for new
tenders. It runs when the application starts, every six hours, and again every
morning at 8:00 AM Indian time.

**Step 2 — It keeps only the relevant ones.**
It matches tender titles against a long list of product keywords — "ICU Bed",
"ECG Machine", "Defibrillator", and so on — and ignores everything else.

**Step 3 — It records each tender properly.**
Reference number, buying authority, estimated value, EMD amount, location,
publication date, bid deadline, opening date. All in one place, searchable.

**Step 4 — It downloads the bid documents.**
The actual PDF files the government published.

**Step 5 — AI reads the technical specification.**
This is the clever part. The AI reads the specification — including scanned
pages, using OCR again — and turns a wall of text into a clean table: what the
tender demands, clause by clause, and how our product answers each one.

**Step 6 — It generates the bid documents.**
The system produces the Word and PDF paperwork automatically, with the
company's letterhead, signature and stamp already in place. Work that took a
day now takes minutes.

**Step 7 — It tracks the bid through the office.**
Who is responsible for this tender. Has the EMD been paid, and how. Have the
specifications been verified. Has it been submitted. Did we win or lose, and
if we lost, why. Every change is logged.

**Step 8 — It sends warnings.**
As a deadline approaches, the system emails the people responsible.

## What makes it difficult

- **GeM is a website, not a proper data feed.** We have to fetch its pages and
  pull the information out of the HTML, the way a person reading the page
  would. When the government changes their website design, our code breaks.
  That is expected, and part of the job.
- **It is a live public website.** We must be polite: no hammering it with
  requests, no running it in a loop while testing.
- **Documents are messy.** Scanned, rotated, mixed formats, sometimes
  handwritten.
- **The generated documents must be exactly right.** A bid can be rejected on
  formatting alone, even when the price and product were the best.

## What success looks like

Nobody sits and scrolls government websites any more. Every relevant tender
appears in the system by itself. No deadline is missed. The document pack for
a bid is generated, checked by a human, and submitted the same day.

---

# The common thread

| | NoticeDesk | Tender Pocket |
|---|---|---|
| Who sends the paperwork | The tax department | Government buyers |
| What arrives | A notice | A tender |
| Why it is urgent | A legal deadline to reply | A bid submission deadline |
| What the computer reads | Scanned notice PDFs | Scanned tender PDFs |
| What the AI produces | A draft reply letter | A specification compliance table |
| What the human does | Checks, edits, signs, sends | Checks, approves, submits |
| Cost of a mistake | A fined or damaged client | A lost contract |

Both products do the same three jobs: **read documents that were never meant
for computers, never forget a deadline, and produce a strong first draft that
a qualified human then approves.**

That is what you are building. Everything technical you will learn is in
service of those three jobs.
