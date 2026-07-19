# NoticeDesk OCR Service

Self-hosted, vendor-neutral OCR for NoticeDesk. Extracts text and word-level
layout from notice PDFs and scanned images using **Tesseract** — no third-party
cloud OCR, so documents never leave the deployment boundary.

See [ADR-0006](../../docs/adr/0006-self-hosted-ocr-service.md) for the why.

## Modules

| Module       | What it is                                                          |
| ------------ | ------------------------------------------------------------------- |
| `ocr-core`   | Framework-free, embeddable OCR engine library (no Spring, no HTTP). |
| `ocr-server` | Spring Boot HTTP service wrapping `ocr-core`.                       |

`ocr-core` is deliberately reusable: any JVM app (batch job, eval harness) can
depend on it directly and call `OcrEngine.extract(...)` without the HTTP hop.

## Architecture

```
             ┌─────────────── ocr-server (Spring Boot) ───────────────┐
 POST        │  OcrController ──▶ OcrEngine (bean)                     │
 /v1/extract │        │                 │                             │
 (multipart) │        ▼                 ▼                             │
             │  OcrExceptionHandler   ┌──────────── ocr-core ────────┐│
             │  (503/422 mapping)     │ TesseractOcrEngine           ││
             └────────────────────────│   ├─ PageRasterizer          ││
                                      │   │    ├─ PdfPageRasterizer   ││ (PDFBox)
                                      │   │    └─ ImagePageRasterizer ││ (ImageIO)
                                      │   └─ TesseractPool ─▶ Tess4J  ││ (native Tesseract)
                                      └──────────────────────────────┘│
```

## HTTP API

### `POST /v1/extract` — `multipart/form-data`

| Part            | Req? | Meaning                                            |
| --------------- | ---- | -------------------------------------------------- |
| `file`          | yes  | Document bytes (PDF, PNG, JPEG, TIFF, …)            |
| `languages`     | no   | Tesseract langs, `eng` or `eng,hin` (default `eng`)|
| `dpi`           | no   | PDF rasterization DPI (default 300)                |
| `includeLayout` | no   | Return word boxes (default `true`)                 |

**200** response:

```json
{
  "text": "ASSESSMENT NOTICE ...",
  "pageCount": 2,
  "engine": "tesseract",
  "meanConfidence": 91.4,
  "layout": {
    "pages": [
      {
        "pageNumber": 1,
        "width": 2480,
        "height": 3508,
        "meanConfidence": 91.4,
        "words": [
          { "text": "NOTICE", "confidence": 95.2,
            "box": { "x": 10, "y": 20, "width": 100, "height": 30 } }
        ]
      }
    ]
  }
}
```

**Errors** — `{ "error", "message", "retryable" }`:

| Status | `error`             | Meaning                            |
| ------ | ------------------- | ---------------------------------- |
| 422    | `permanent`         | Bad input / missing language data  |
| 503    | `transient`         | Pool saturated / retryable failure |
| 413    | `payload_too_large` | Upload exceeds `OCR_MAX_UPLOAD`    |
| 400    | `bad_request`       | Missing `file` part                |

### `GET /health`

Reports the engine name and which Tesseract language packs are installed;
`503` if none are found. Actuator probes are also at `/actuator/health`.

## Configuration

All `ocr.*` properties map to `OCR_*` environment variables.

| Env var                  | Default | Meaning                                     |
| ------------------------ | ------- | ------------------------------------------- |
| `TESSDATA_PREFIX`        | (image) | Path to Tesseract language data             |
| `OCR_LANGUAGES`          | `eng`   | Default languages when a request omits them |
| `OCR_DPI`                | `300`   | PDF rasterization DPI                        |
| `OCR_PSM`                | `3`     | Tesseract page segmentation mode            |
| `OCR_OEM`                | `1`     | Tesseract engine mode (1 = LSTM)            |
| `OCR_POOL_SIZE`          | `0`     | Native workers / max concurrency (0 = #CPU) |
| `OCR_BORROW_TIMEOUT_MS`  | `30000` | Wait for a free worker before 503           |
| `OCR_MAX_PDF_PAGES`      | `500`   | Reject larger PDFs                          |
| `OCR_MAX_UPLOAD`         | `50MB`  | Max upload size                            |
| `OCR_SERVER_PORT`        | `8080`  | HTTP port                                   |

## Build & run

```bash
# Build everything and run tests (no native Tesseract needed for the tests)
mvn -f apps/ocr-service/pom.xml verify

# Run locally (requires Tesseract installed: `apt install tesseract-ocr tesseract-ocr-eng`)
java -jar apps/ocr-service/ocr-server/target/ocr-server.jar

# Or via Docker (bundles Tesseract + eng/hin language data)
docker build -t noticedesk-ocr apps/ocr-service -f apps/ocr-service/ocr-server/Dockerfile
docker run -p 8080:8080 noticedesk-ocr

# Smoke test
curl -F file=@notice.pdf -F languages=eng http://localhost:8080/v1/extract
```

## Wiring into the API

The FastAPI backend talks to this service through `SelfHostedOCRProvider`
(`apps/api/app/services/ocr/self_hosted.py`), selected by config — no code
change at any call site:

```bash
export OCR_PROVIDER_PRIMARY=self_hosted
export SELF_HOSTED_OCR_URL=http://ocr-service:8080
# optional: keep a cloud fallback for burst / bad scans
export OCR_PROVIDER_FALLBACK=google_doc_ai
```

## Adding a language

Extend the Tesseract package list in `ocr-server/Dockerfile` (e.g.
`tesseract-ocr-mar`, `tesseract-ocr-guj`) and pass it at request time via
`languages=eng,hin,mar`. No code change.
