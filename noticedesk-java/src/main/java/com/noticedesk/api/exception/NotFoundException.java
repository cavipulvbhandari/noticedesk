package com.noticedesk.api.exception;

public class NotFoundException extends AppException {
    public NotFoundException(String message) {
        super(message, "not_found", 404);
    }
}
