package in.noticedesk.ocr.core;

import java.util.Objects;

/**
 * A single unit of OCR work: the raw document bytes plus their MIME type and
 * the options to run under.
 *
 * @param content   raw file bytes (PDF or image); never {@code null} or empty
 * @param mimeType  IANA media type, e.g. {@code application/pdf},
 *                  {@code image/png}; used to pick the rasterizer
 * @param options   per-request OCR knobs
 */
public record OcrRequest(byte[] content, String mimeType, OcrOptions options) {

    public OcrRequest {
        Objects.requireNonNull(content, "content");
        Objects.requireNonNull(options, "options");
        if (content.length == 0) {
            throw new OcrException("document content is empty");
        }
        if (mimeType == null || mimeType.isBlank()) {
            // Default to PDF: it is by far the dominant notice format, and the
            // rasterizer will reject the bytes if that guess is wrong.
            mimeType = "application/pdf";
        }
    }

    public static OcrRequest of(byte[] content, String mimeType) {
        return new OcrRequest(content, mimeType, OcrOptions.defaults());
    }
}
