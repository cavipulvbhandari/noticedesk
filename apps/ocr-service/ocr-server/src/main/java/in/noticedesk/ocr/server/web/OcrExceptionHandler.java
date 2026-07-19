package in.noticedesk.ocr.server.web;

import in.noticedesk.ocr.core.OcrException;
import in.noticedesk.ocr.core.OcrTransientException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

/**
 * Translates the core error taxonomy into HTTP status codes the caller's retry
 * logic understands:
 *
 * <ul>
 *   <li>{@link OcrTransientException} → 503 (retryable)</li>
 *   <li>{@link OcrException} → 422 (permanent — bad input / missing lang data)</li>
 *   <li>oversized upload → 413</li>
 *   <li>missing params → 400</li>
 *   <li>anything else → 500</li>
 * </ul>
 *
 * The Python {@code SelfHostedOCRProvider} maps 5xx to {@code OCRTransientError}
 * and 4xx to {@code OCRError}, so this mapping is the contract between the two.
 */
@RestControllerAdvice
public class OcrExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(OcrExceptionHandler.class);

    @ExceptionHandler(OcrTransientException.class)
    public ResponseEntity<ErrorResponse> handleTransient(OcrTransientException e) {
        log.warn("ocr.transient {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(new ErrorResponse("transient", e.getMessage(), true));
    }

    @ExceptionHandler(OcrException.class)
    public ResponseEntity<ErrorResponse> handlePermanent(OcrException e) {
        log.warn("ocr.permanent {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(new ErrorResponse("permanent", e.getMessage(), false));
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<ErrorResponse> handleTooLarge(MaxUploadSizeExceededException e) {
        return ResponseEntity.status(HttpStatus.PAYLOAD_TOO_LARGE)
                .body(new ErrorResponse("payload_too_large", e.getMessage(), false));
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<ErrorResponse> handleMissingParam(
            MissingServletRequestParameterException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(new ErrorResponse("bad_request", e.getMessage(), false));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception e) {
        log.error("ocr.internal", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ErrorResponse("internal", "internal OCR error", true));
    }
}
