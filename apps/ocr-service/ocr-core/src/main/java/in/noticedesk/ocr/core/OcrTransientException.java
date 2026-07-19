package in.noticedesk.ocr.core;

/**
 * Temporary failure (native timeout, resource exhaustion, a page that
 * momentarily failed to rasterize) that is safe to retry.
 *
 * <p>Mirrors the Python {@code OCRTransientError}; the HTTP layer maps it to a
 * 503 so the caller's retry loop kicks in.
 */
public class OcrTransientException extends OcrException {

    public OcrTransientException(String message) {
        super(message);
    }

    public OcrTransientException(String message, Throwable cause) {
        super(message, cause);
    }
}
