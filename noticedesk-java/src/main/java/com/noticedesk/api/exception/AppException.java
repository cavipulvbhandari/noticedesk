package com.noticedesk.api.exception;

import java.util.Map;

public class AppException extends RuntimeException {

    private final String code;
    private final int httpStatus;
    private final Map<String, Object> details;

    public AppException(String message, String code, int httpStatus, Map<String, Object> details) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
        this.details = details != null ? details : Map.of();
    }

    public AppException(String message, String code, int httpStatus) {
        this(message, code, httpStatus, null);
    }

    public String getCode() { return code; }
    public int getHttpStatus() { return httpStatus; }
    public Map<String, Object> getDetails() { return details; }
}
