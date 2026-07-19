package com.noticedesk.api.exception;

public class AuthException extends AppException {
    public AuthException(String message) {
        super(message, "unauthorized", 401);
    }
}
