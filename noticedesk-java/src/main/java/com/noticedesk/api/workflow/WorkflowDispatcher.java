package com.noticedesk.api.workflow;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.service.llm.LlmFactory;
import com.noticedesk.api.service.llm.LlmProvider;
import com.noticedesk.api.service.llm.LlmResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Dispatches long-running agent workflows (drafting, OCR-parse-route).
 *
 * <p>In development (inline mode), everything runs synchronously in the
 * current thread. Production will route through Temporal for retries,
 * replay, and visibility.
 *
 * <p><strong>TODO (Sprint N):</strong> implement Temporal dispatcher;
 * extract draft-generation logic into a proper DraftingAgent class.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class WorkflowDispatcher {

    private final LlmFactory llmFactory;
    private final NamedParameterJdbcTemplate jdbc;
    private final ObjectMapper objectMapper;
    private final AppProperties properties;

    /**
     * Generates a reply draft for the given notice.
     *
     * @param job map with {@code notice_id}, {@code matter_id},
     *            {@code tenant_id}, {@code user_id}
     * @return map with {@code draftId}, {@code version},
     *         {@code citationSummary}, {@code sectionsKept}
     */
    public Map<String, Object> dispatchGenerateDraft(Map<String, Object> job) {
        String tenantId  = (String) job.get("tenant_id");
        String matterId  = (String) job.get("matter_id");
        String noticeId  = (String) job.get("notice_id");
        String userId    = (String) job.get("user_id");

        log.info("dispatch_generate_draft notice_id={} matter_id={} tenant={}", noticeId, matterId, tenantId);

        // ---- 1. Load matter context ----------------------------------------
        var rows = jdbc.queryForList(
                """
                SELECT n.notice_id, n.document_type, n.law, n.financial_year, n.assessment_year,
                       n.authority, n.due_date, n.demand_amount,
                       c.legal_name AS client_legal_name, c.pan AS client_pan,
                       r.registration_type, r.identifier_value, r.state_name,
                       LEFT(COALESCE(ib.ocr_text, ''), :ocrChars) AS notice_ocr_excerpt
                FROM notices n
                JOIN matters m   ON m.matter_id  = n.matter_id
                JOIN clients c   ON c.client_id  = m.client_id
                JOIN client_registrations r ON r.registration_id = m.registration_id
                LEFT JOIN documents_inbox ib ON ib.inbox_id = n.source_inbox_id
                WHERE n.notice_id = :nid
                LIMIT 1
                """,
                Map.of("nid", UUID.fromString(noticeId),
                       "ocrChars", properties.getDrafting().getOcrExcerptChars()));

        if (rows.isEmpty()) {
            throw new IllegalArgumentException("Notice not found: " + noticeId);
        }
        Map<String, Object> ctx = rows.get(0);

        // ---- 2. Call drafting LLM ------------------------------------------
        String systemPrompt = loadSystemPrompt();
        String userPrompt   = buildUserPrompt(ctx, tenantId);

        LlmProvider llm = llmFactory.getLlmForAgent("drafting");
        LlmResponse resp = llm.generateText(
                systemPrompt, userPrompt,
                properties.getDrafting().getMaxOutputTokens(), 0.0);

        // ---- 3. Parse sections ---------------------------------------------
        List<Map<String, Object>> sections;
        String internalNote;
        try {
            String text = resp.content().strip();
            if (text.startsWith("```")) {
                int firstNl = text.indexOf('\n');
                if (firstNl != -1) text = text.substring(firstNl + 1);
                if (text.endsWith("```")) text = text.substring(0, text.length() - 3);
                text = text.strip();
            }
            Map<String, Object> parsed = objectMapper.readValue(text,
                    new TypeReference<Map<String, Object>>() {});
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> rawSections =
                    (List<Map<String, Object>>) parsed.getOrDefault("sections", List.of());
            sections    = rawSections;
            internalNote = (String) parsed.getOrDefault("internal_partner_note", "");
        } catch (Exception e) {
            log.warn("draft_parse_failed notice_id={} error={} — storing raw response", noticeId, e.getMessage());
            sections     = List.of(Map.of("num", 1, "title", "Draft", "body_html", resp.content()));
            internalNote = "";
        }

        // ---- 4. Persist draft ----------------------------------------------
        int version = nextVersion(UUID.fromString(matterId));
        String sectionsJson;
        try {
            sectionsJson = objectMapper.writeValueAsString(sections);
        } catch (Exception e) {
            sectionsJson = "[]";
        }

        UUID draftId = jdbc.queryForObject(
                """
                INSERT INTO drafts
                    (tenant_id, matter_id, version, status, content, sections,
                     internal_partner_note, model_used, generated_by_user_id)
                VALUES
                    (:tid, :mid, :version, 'draft', :sections::jsonb, :sections::jsonb,
                     :note, :model, :userId)
                RETURNING draft_id
                """,
                Map.of(
                        "tid",     tenantId,
                        "mid",     UUID.fromString(matterId),
                        "version", version,
                        "sections", sectionsJson,
                        "note",    internalNote,
                        "model",   resp.model() != null ? resp.model() : "stub",
                        "userId",  userId != null ? UUID.fromString(userId) : null),
                UUID.class);

        log.info("draft_persisted draft_id={} version={} sections={}", draftId, version, sections.size());

        return Map.of(
                "draftId",         draftId.toString(),
                "version",         version,
                "citationSummary", Map.of(),
                "sectionsKept",    sections.size());
    }

    // -----------------------------------------------------------------------

    private int nextVersion(UUID matterId) {
        Integer max = jdbc.queryForObject(
                "SELECT COALESCE(MAX(version), 0) FROM drafts WHERE matter_id = :mid",
                Map.of("mid", matterId), Integer.class);
        return (max != null ? max : 0) + 1;
    }

    private String loadSystemPrompt() {
        try {
            ClassPathResource res = new ClassPathResource("prompts/drafting_v1.md");
            if (res.exists()) {
                String md = res.getContentAsString(StandardCharsets.UTF_8);
                return extractFenced(md.split("## System prompt", 2)[1]);
            }
        } catch (Exception e) {
            log.warn("drafting_prompt_load_failed: {}", e.getMessage());
        }
        return "You are a drafting agent. Produce a JSON reply draft with sections array.";
    }

    private String buildUserPrompt(Map<String, Object> ctx, String tenantId) {
        return "Matter context:\n" + ctx.toString();
    }

    private static String extractFenced(String s) {
        int start = s.indexOf("```");
        if (start == -1) return s;
        int nl = s.indexOf('\n', start);
        if (nl == -1) return s;
        int end = s.indexOf("```", nl + 1);
        if (end == -1) return s;
        return s.substring(nl + 1, end).strip();
    }
}
