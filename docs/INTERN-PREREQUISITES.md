# What You Need To Know Before You Start

For new interns joining NoticeDesk or Tender Pocket. Plain language. Read
`WHAT-WE-ARE-BUILDING.md` first so you know what the products do.

This document has three parts:

- **Part A** — what you must already be able to do on day one.
- **Part B** — what you will learn in your first two weeks, not before.
- **Part C** — the words, rules and setup you should have seen once.

Nothing here is a test. If you are missing something in Part A, say so early
and we will find you the right first ticket.

---

# Part A — What you must already be able to do

These are the five things where a gap causes real problems, not just slow
progress.

## 1. Use Git without help

You should be able to:

- Copy a project from GitHub to your computer (`clone`).
- Make a branch, change some files, and save that change with a message
  (`commit`).
- Send it back to GitHub (`push`) and open a pull request.
- Handle it when two people changed the same line (a "merge conflict").

You will never save changes directly to the main version of the project.
Everything goes through a branch and a review by someone else.

**One rule above all others:** passwords, API keys and database addresses must
never be saved into the code. They live in something called an *environment
variable*, which is a setting on the machine rather than a line in a file. If
you ever accidentally commit a password, tell someone immediately. It is
fixable. Hiding it is not.

## 2. Write SQL

SQL is the language for asking a database questions. Both products keep almost
everything in a database, and both of them use plain SQL rather than hiding it
behind a tool. So you cannot avoid it.

You should be comfortable with:

- `SELECT`, `WHERE`, `ORDER BY`
- Joining two tables together
- `GROUP BY` and counting things
- What `NULL` means, and why it behaves strangely
- What an index is and why a query might be slow without one

If you have only ever used SQL through a library that writes it for you, spend
a weekend writing it by hand first.

## 3. Know one of our languages properly

You do not need all of them. You need the one for the project you join.

- **NoticeDesk — Python.** Version 3.11. You must know functions, classes,
  virtual environments, and `async` / `await`. Our code is fully type-annotated
  and checked strictly, so writing Python without type hints will fail the
  automatic checks.
- **Tender Pocket — Java.** Version 21. Classes, interfaces, collections,
  exceptions, and how to build a project with Maven.
- **Either front end — TypeScript.** Not just JavaScript. TypeScript adds types,
  and our settings are strict. Writing `any` everywhere to make errors go away
  is not acceptable.

## 4. Be comfortable in a terminal

Move between folders, run commands, read an error message, install packages,
set an environment variable, stop a process that is stuck. You will spend a
lot of time here.

## 5. Understand how the web actually works

Not deeply — but you should know what a request and a response are, what
`GET` and `POST` mean, what a `404` and a `500` mean, and what a cookie or a
login token does. Both products are ordinary web applications talking over
HTTP.

---

# Part B — What you will learn here, not before

Do not study these in advance. Nobody expects them at interview or on day one.
They are listed so you know what is coming.

**If you join NoticeDesk:**

| Thing | What it is, in one line |
|---|---|
| FastAPI | The Python tool we use to build the server. |
| PostgreSQL | The database. Serious, free, widely used. |
| Row-Level Security | A database feature that hides one CA firm's rows from another firm. If you forget to switch it on for a request, you get zero results — that is deliberate. |
| Migrations | Numbered SQL files that change the database structure, applied in order. We write them by hand and never edit an old one. |
| Next.js and React | The tools the website is built with. |
| Docker | Runs the database on your machine without installing it properly. |
| Temporal, Terraform, AWS | Background jobs and cloud servers. Later, not now. |

**If you join Tender Pocket:**

| Thing | What it is, in one line |
|---|---|
| Spring Boot | The Java framework the whole server is built on. |
| JPA / Hibernate | Turns Java objects into database rows. Careful: here the database structure follows the Java classes automatically, so changing a field changes the real database. |
| Jsoup | Reads a web page's HTML so we can pull tender details out of it. |
| Apache POI / PDFBox | Create Word and PDF files from code. |
| Tesseract | Free OCR — turns scanned pages into text. |
| Gemini | The AI model that reads specifications. |
| Docker | How the whole application is packaged and deployed. |

**Both projects use AI models.** You do not need to have used one before. You
do need to accept one rule from day one: **we never trust what the model says**.
Its answer is checked by our own code before it is saved or shown to anyone.
"The AI said so" is not a reason for anything.

---

# Part C — Things to have seen once

## Words you will hear in your first meeting

**NoticeDesk**

| Word | Meaning |
|---|---|
| PAN | A ten-character code identifying a taxpayer. Everything in the system is organised around it. |
| GSTIN | A fifteen-character GST number. Characters 3 to 12 are the holder's PAN. One business can have several, one per state. |
| Notice | A letter from the tax department asking a taxpayer to explain something. |
| Matter | The case file that a notice belongs to. |
| Draft | The reply letter the firm sends back. |
| Due date | The deadline for replying. Missing it hurts a real client. |
| Tenant | One CA firm. Many firms share one system but must never see each other's data. |

**Tender Pocket**

| Word | Meaning |
|---|---|
| Tender | A government announcement that they want to buy something. |
| Bid | Our customer's response to a tender. |
| GeM | Government e-Marketplace — the main government website we collect tenders from. |
| EMD | Earnest money deposit. Money paid up front to take part in a bid. |
| Corrigendum | An official correction to a tender that has already been published. Can change dates and specifications. |
| Pre-bid | A meeting before the deadline where bidders may ask questions. |
| Specification | The list of technical requirements the product must meet. |

## Five rules of the house

1. **Never commit a password or key.** Covered above, and worth repeating.
2. **Do not tidy up code you were not asked to touch.** Some files are long and
   ugly. They also work, and other things depend on them. Change only what your
   task needs. Rewriting things is the most expensive mistake an intern makes.
3. **Do not trust AI output.** Ours or your own coding assistant's. Read it,
   understand it, then use it.
4. **Ask early.** Stuck for two hours is completely normal. Stuck for two days
   without telling anyone is not. No one will think less of you for asking on
   day three.
5. **The data is real.** Real client tax notices, real bid deadlines. Be careful
   with anything that sends an email, writes to a shared database, or contacts
   a government website.

## Install before your first day

- **Git**
- **Docker Desktop**
- A code editor you like — VS Code is fine
- **Node.js**, version 20
- Then, depending on the project: **Python 3.11**, or a **Java 21** kit with
  **Maven**

If any of these fight you, that is a perfectly good first question to ask.

## Read in this order

1. `docs/WHAT-WE-ARE-BUILDING.md` — what the products do and who uses them.
2. This document.
3. The `README.md` of the project you have been given.
4. `docs/ONBOARDING-PREREQUISITES.md` — the long, technical version of this
   page. Skim it now; come back to it in week two.

---

# You are ready when you can do these

Not a test, and not day one. This is what "settled in" looks like, usually
after a week or two.

**Everyone**

- [ ] Copy the project, make a branch, change something small, and open a pull
      request that passes the automatic checks.
- [ ] Start a database on your own machine and ask it a question.
- [ ] Follow one action in the website all the way through to the database
      change it causes.
- [ ] Explain, in your own words, what the product does for the person paying
      for it.

**NoticeDesk**

- [ ] Get the whole thing running locally and all the checks passing.
- [ ] Explain why a query can return nothing at all when the firm's identity
      has not been set on the request.
- [ ] Draw the chain: PAN → registration → matter → notice → draft.
- [ ] Add one new field end to end, including the database change and its test.

**Tender Pocket**

- [ ] Build the project and run it against a local database.
- [ ] Build and run it inside Docker.
- [ ] Add one new field to a tender and see it appear in the API's output.
- [ ] Explain what happens to our code when the GeM website changes its layout.

## What nobody expects from you on day one

To know Indian tax law or government procurement. To have used these exact
tools. To write code without asking questions. To be fast.

What is expected: read carefully, keep your changes small, and say clearly
when you do not understand something.
