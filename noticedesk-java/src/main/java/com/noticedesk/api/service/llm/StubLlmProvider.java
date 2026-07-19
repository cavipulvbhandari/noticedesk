package com.noticedesk.api.service.llm;

import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

/**
 * Deterministic LLM stub for tests and local dev.
 *
 * <p>When {@code cannedKey} is provided (from {@code noticedesk.llm.stub-default-canned} /
 * {@code STUB_DEFAULT_CANNED} env var), each call loads
 * {@code classpath:stub-canned/{cannedKey}.json} and returns it verbatim.
 *
 * <p>Without a canned key, the stub detects the agent from system-prompt keywords:
 * <ul>
 *   <li>{@code document_type}, {@code parse}, {@code ocr} → parsing response</li>
 *   <li>{@code sections}, {@code draft}, {@code reply}    → drafting response</li>
 *   <li>{@code triage}, {@code checklist}                 → triage response</li>
 *   <li>anything else                                     → {@code {"status":"ok"}}</li>
 * </ul>
 */
@Slf4j
public class StubLlmProvider implements LlmProvider {

    private static final String PARSE_RESPONSE = """
            {
              "document_type": "needs_review",
              "law": null,
              "client_name_on_document": null,
              "pans_extracted": [],
              "gstins_extracted": [],
              "notice_number": null,
              "din_or_rfn": null,
              "issue_date": null,
              "receipt_date": null,
              "due_date": null,
              "hearing_date": null,
              "financial_year": null,
              "assessment_year": null,
              "authority": null,
              "demand_amount": null,
              "issues": [],
              "documents_required": [],
              "parse_confidence": 0.0,
              "fields_needing_review": ["document_type"]
            }
            """;

    private static final String DRAFT_RESPONSE = """
            {
              "sections": [
                {"num": 1, "title": "Overview",       "body_html": "<p>Stub draft — Section 1 Overview.</p>"},
                {"num": 2, "title": "Facts of the Case", "body_html": "<p>Stub draft — Section 2 Facts.</p>"},
                {"num": 3, "title": "Legal Grounds",  "body_html": "<p>Stub draft — Section 3 Grounds.</p>"},
                {"num": 4, "title": "Submissions",    "body_html": "<p>Stub draft — Section 4 Submissions.</p>"},
                {"num": 5, "title": "Prayer",         "body_html": "<p>Stub draft — Section 5 Prayer.</p>"}
              ],
              "internal_partner_note": "Stub draft generated for testing.",
              "client_summary": "This is a stub response. Please configure a real LLM provider."
            }
            """;

    private static final String TRIAGE_RESPONSE = """
            {
              "summary": "Stub triage summary. Please configure a real LLM provider.",
              "checklist": [
                {"label": "Copy of Notice", "rationale": "Original notice required for filing", "doc_type": "notice",   "is_required": true},
                {"label": "PAN Card",       "rationale": "Identity proof",                      "doc_type": "pan_card", "is_required": true}
              ]
            }
            """;

    /** When non-null, every call loads {@code classpath:stub-canned/{cannedKey}.json}. */
    private final String cannedKey;

    /** No-arg constructor — keyword-detection mode, no canned overrides. */
    public StubLlmProvider() {
        this(null);
    }

    /**
     * @param cannedKey value of {@code noticedesk.llm.stub-default-canned}; may be null/blank.
     */
    public StubLlmProvider(String cannedKey) {
        this.cannedKey = (cannedKey != null && !cannedKey.isBlank()) ? cannedKey.trim() : null;
    }

    @Override
    public String getName() { return "stub"; }

    @Override
    public String getModel() { return "stub-model"; }

    @Override
    public LlmResponse generateText(String system, String user, int maxOutputTokens, double temperature) {
        log.debug("stub_llm_call system_length={} user_length={}", system.length(), user.length());
        String content = resolveContent(system);
        return new LlmResponse(content, "stub-model", "stub", 100, 200);
    }

    // -----------------------------------------------------------------------

    private String resolveContent(String system) {
        if (cannedKey != null) {
            String loaded = loadClasspathResource("stub-canned/" + cannedKey + ".json");
            if (loaded != null) {
                log.info("stub_llm_canned key={}", cannedKey);
                return loaded;
            }
            log.warn("stub_llm_canned_missing key={} — falling back to keyword detection", cannedKey);
        }
        return detectAgentType(system);
    }

    private String detectAgentType(String system) {
        String lower = system.toLowerCase();
        if (lower.contains("document_type") || lower.contains("parse") || lower.contains("ocr")) {
            return PARSE_RESPONSE;
        }
        if (lower.contains("sections") || lower.contains("draft") || lower.contains("reply")) {
            return DRAFT_RESPONSE;
        }
        if (lower.contains("triage") || lower.contains("checklist")) {
            return TRIAGE_RESPONSE;
        }
        return "{\"status\": \"ok\"}";
    }

    private static String loadClasspathResource(String path) {
        try {
            ClassPathResource resource = new ClassPathResource(path);
            if (resource.exists()) {
                return resource.getContentAsString(StandardCharsets.UTF_8);
            }
        } catch (IOException e) {
            log.warn("stub_llm_classpath_load_failed path={} error={}", path, e.getMessage());
        }
        return null;
    }
}
