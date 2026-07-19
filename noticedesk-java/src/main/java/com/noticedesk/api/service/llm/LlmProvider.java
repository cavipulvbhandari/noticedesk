package com.noticedesk.api.service.llm;

public interface LlmProvider {
    String getName();
    String getModel();
    LlmResponse generateText(String system, String user, int maxOutputTokens, double temperature);

    default LlmResponse generateText(String system, String user) {
        return generateText(system, user, 4096, 0.0);
    }
}
