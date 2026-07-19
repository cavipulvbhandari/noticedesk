package com.noticedesk.api.controller;

import com.noticedesk.api.config.AppProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class DemoController {

    private final AppProperties properties;

    @GetMapping("/demo/providers")
    public Map<String, Object> getProviders() {
        Map<String, Object> response = new LinkedHashMap<>();

        String llmProvider = "stub";
        String ocrProvider = "stub";
        String storageBackend = "local";
        String emailProvider = "stub";
        String workflowBackend = "inline";
        String environment = "development";

        if (properties.getLlm() != null && properties.getLlm().getProviderPrimary() != null) {
            llmProvider = properties.getLlm().getProviderPrimary();
        }
        if (properties.getOcr() != null && properties.getOcr().getProviderPrimary() != null) {
            ocrProvider = properties.getOcr().getProviderPrimary();
        }
        if (properties.getStorage() != null && properties.getStorage().getBackend() != null) {
            storageBackend = properties.getStorage().getBackend();
        }
        if (properties.getEmail() != null && properties.getEmail().getProvider() != null) {
            emailProvider = properties.getEmail().getProvider();
        }
        if (properties.getWorkflow() != null && properties.getWorkflow().getBackend() != null) {
            workflowBackend = properties.getWorkflow().getBackend();
        }
        if (properties.getEnvironment() != null) {
            environment = properties.getEnvironment();
        }

        response.put("llm_provider", llmProvider);
        response.put("ocr_provider", ocrProvider);
        response.put("storage_backend", storageBackend);
        response.put("email_provider", emailProvider);
        response.put("workflow_backend", workflowBackend);
        response.put("environment", environment);

        return response;
    }
}
