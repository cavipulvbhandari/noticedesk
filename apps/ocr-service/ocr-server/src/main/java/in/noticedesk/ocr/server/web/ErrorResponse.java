package in.noticedesk.ocr.server.web;

/**
 * Uniform error body.
 *
 * @param error     short machine code: {@code permanent}, {@code transient},
 *                  {@code payload_too_large}, {@code bad_request}, {@code internal}
 * @param message   human-readable detail
 * @param retryable whether the caller should retry the same request
 */
public record ErrorResponse(String error, String message, boolean retryable) {
}
