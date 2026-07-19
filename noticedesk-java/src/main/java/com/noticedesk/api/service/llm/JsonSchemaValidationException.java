package com.noticedesk.api.service.llm;

public class JsonSchemaValidationException extends LlmException {
    public JsonSchemaValidationException(String message) { super(message); }
    public JsonSchemaValidationException(String message, Throwable cause) { super(message, cause); }
}
