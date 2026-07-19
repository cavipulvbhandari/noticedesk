package com.noticedesk.api.exception;

public class ConflictException extends AppException {
    public ConflictException(String message) {
        super(message, "pan_gstin_mismatch", 409);
    }
}
