package com.noticedesk.api.exception;

import java.util.Map;

public class ForbiddenException extends AppException {
    public ForbiddenException(String message) {
        super(message, "forbidden", 403);
    }

    public ForbiddenException(String message, Map<String, Object> details) {
        super(message, "forbidden", 403, details);
    }
}
