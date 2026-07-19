package com.noticedesk.api.exception;

import java.util.Map;

public class AppValidationException extends AppException {
    public AppValidationException(String message) {
        super(message, "validation_error", 422);
    }

    public AppValidationException(String message, Map<String, Object> details) {
        super(message, "validation_error", 422, details);
    }
}
