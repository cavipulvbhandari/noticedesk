package com.noticedesk.api.service.llm;

public class LlmTransientException extends LlmException {
    public LlmTransientException(String message) { super(message); }
    public LlmTransientException(String message, Throwable cause) { super(message, cause); }
}
