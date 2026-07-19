package in.noticedesk.ocr.core;

/**
 * The reusable OCR contract. One method, one responsibility: turn a document
 * into text (plus optional layout).
 *
 * <p>Implementations must be safe for concurrent use — callers share a single
 * engine instance across request threads. Failures are signalled with the
 * {@link OcrException} family so callers can distinguish permanent from
 * retryable.
 */
public interface OcrEngine {

    /**
     * Extract text and layout from a document.
     *
     * @param request document bytes, MIME type and options
     * @return the extracted text and structured layout
     * @throws OcrException          on a permanent failure (bad input,
     *                               missing language data, unsupported type)
     * @throws OcrTransientException on a retryable failure (timeout, transient
     *                               resource exhaustion)
     */
    ExtractedDocument extract(OcrRequest request);

    /** Human-readable engine name recorded on the result, e.g. {@code "tesseract"}. */
    String name();
}
