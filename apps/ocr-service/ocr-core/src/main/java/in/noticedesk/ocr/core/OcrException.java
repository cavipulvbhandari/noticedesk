package in.noticedesk.ocr.core;

/**
 * Permanent OCR failure that will not improve on retry (corrupt file,
 * unsupported format, missing language data).
 *
 * <p>Mirrors the Python {@code OCRError} on the calling side so the HTTP layer
 * can map it to a 4xx and callers know not to retry.
 */
public class OcrException extends RuntimeException {

    public OcrException(String message) {
        super(message);
    }

    public OcrException(String message, Throwable cause) {
        super(message, cause);
    }
}
