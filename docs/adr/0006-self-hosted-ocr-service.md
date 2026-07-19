# ADR-0006 — Self-hosted OCR service

- Status: Accepted
- Date: 2026-07-19
- Authors: NoticeDesk Engineering

## Context

ADR-0004 shipped OCR behind a vendor-neutral `OCRProvider` interface with two
cloud implementations — Google Document AI (primary) and Azure Document
Intelligence (fallback). That was the right call to get the inbox working
quickly, but it leaves every notice PDF flowing to a third party. For an
operating system that handles Indian taxpayers' confidential assessment notices
that is a standing liability:

- **Data residency / confidentiality.** Notice PDFs contain PAN, financial
  figures, and litigation detail. Shipping them to a US-region cloud OCR API is
  something firms increasingly cannot accept.
- **Per-page cost.** Cloud OCR is billed per page; at firm scale this is a
  recurring line item for a task that is well within reach of open-source OCR.
- **Vendor lock and outage exposure.** Both current providers are external
  dependencies with their own pricing, quotas, and outages.

We want a first-party OCR path with **no third-party dependency**, without
throwing away the abstraction that already lets us swap providers by config.

## Decision

Add a **self-hosted OCR microservice** (`apps/ocr-service`) and a thin provider
(`self_hosted`) that plugs into the existing `OCRProvider` interface.

**The service** is a JVM application built as two Maven modules:

- `ocr-core` — a framework-free, embeddable OCR engine library. It rasterizes a
  document to page images (Apache PDFBox for PDF — pure Java, no native poppler;
  ImageIO for raster/TIFF) and runs **Tesseract** (via Tess4J) over each page,
  returning text plus optional word-level bounding boxes. Native Tesseract
  access is funneled through a bounded `TesseractPool` because Tess4J is not
  thread-safe; the pool size is the service's real concurrency and native-memory
  knob. No Spring, no HTTP — reusable in any JVM context.
- `ocr-server` — a Spring Boot HTTP wrapper exposing `POST /v1/extract`
  (multipart) and `GET /health`. It owns nothing but request validation, the
  engine bean, and error-code translation.

**The provider**: `SelfHostedOCRProvider` (Python) calls the service over HTTP
and maps the response onto `ExtractedDoc`. The Java error taxonomy is mapped to
HTTP status and back to the Python one:

| Java (`ocr-core`)       | HTTP | Python (`app.services.ocr`) |
| ----------------------- | ---- | --------------------------- |
| `OcrTransientException` | 503  | `OCRTransientError` (retry) |
| `OcrException`          | 422  | `OCRError` (permanent)      |

So the pipeline's existing retry/fallback logic (ADR-0004) works unchanged:
3 attempts against the primary, then the fallback. Adopting the self-hosted
service is a config change only — `OCR_PROVIDER_PRIMARY=self_hosted` with
`SELF_HOSTED_OCR_URL` set — honoring the ADR-0003 invariant that no call site
hard-codes a vendor.

## Consequences

- **A firm can run the entire OCR path with zero third-party calls.** Documents
  never leave the deployment boundary.
- **The abstraction is preserved and extended.** There are now four
  interchangeable providers (`google_doc_ai`, `azure_doc_intel`, `self_hosted`,
  `stub`). Common production setups: self-hosted primary + cloud fallback for
  burst capacity, or self-hosted primary + no fallback for strict residency.
- **New runtime surface: the JVM service.** It must be deployed and scaled
  (stateless, so horizontal scaling is trivial; `ocr.pool-size` bounds native
  memory per pod). The container bundles the Tesseract native lib and English +
  Hindi language data; more languages are an apt-line change, not a code change.
- **OCR quality is now ours to tune.** Tesseract on clean, born-digital notice
  PDFs is strong; on poor scans it trails the cloud vendors. Because layout and
  per-word confidence are returned, a future step can route low-confidence pages
  to a cloud fallback automatically.
- **`ocr-core` is independently reusable.** Batch tooling or an eval harness can
  depend on the library directly without the HTTP hop.

## Alternatives considered

- **A Python OCR service (pytesseract / a native binding) in `apps/api`.**
  Keeps one language, but couples heavy native OCR work to the request/worker
  process, and CPU-bound OCR competes with the API event loop. A separate,
  independently-scalable service is the cleaner boundary. The JVM additionally
  gives us PDFBox (pure-Java rasterization, no poppler) and mature pooling.
- **PaddleOCR / an ONNX model server.** Higher accuracy ceiling on bad scans,
  but a much heavier deployment (Python ML stack or GPU) for Sprint-scope value.
  The `OcrEngine` interface leaves the door open to add this as another engine
  behind the same service later.
- **Keep cloud-only.** Rejected on confidentiality and cost grounds above.
- **Embed OCR inline in the pipeline instead of a service.** Rejected: violates
  the "external/heavy calls run out-of-band" principle from ADR-0004 and would
  make OCR capacity impossible to scale independently of the API.
