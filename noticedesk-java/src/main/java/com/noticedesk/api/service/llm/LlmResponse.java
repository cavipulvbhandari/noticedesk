package com.noticedesk.api.service.llm;

public record LlmResponse(
        String content,
        String model,
        String providerName,
        Integer inputTokens,
        Integer outputTokens
) {}
