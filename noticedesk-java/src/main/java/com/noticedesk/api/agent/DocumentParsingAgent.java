package com.noticedesk.api.agent;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.service.IdentityService;
import com.noticedesk.api.service.llm.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
@RequiredArgsConstructor
public class DocumentParsingAgent {

    private static final Set<String> KNOWN_DOCUMENT_TYPES = Set.of(
            "ASMT-10", "DRC-01A", "DRC-01", "GST_HEARING",
            "IT_142(1)", "IT_143(2)", "IT_148_148A", "IT_CITA_NFAC_HEARING", "needs_review");
    private static final Set<String> GST_TYPES = Set.of("ASMT-10", "DRC-01A", "DRC-01", "GST_HEARING");
    private static final Set<String> IT_TYPES = Set.of("IT_142(1)", "IT_143(2)", "IT_148_148A", "IT_CITA_NFAC_HEARING");

    private static final Pattern ISO_DATE = Pattern.compile("^\\d{4}-\\d{2}-\\d{2}$");
    private static final Pattern DMY = Pattern.compile("^(\\d{1,2})[/\\-.](\\d{1,2})[/\\-.](\\d{2,4})$");
    private static final Pattern FY_FULL = Pattern.compile("^(\\d{4})\\s*[-/]\\s*(\\d{2,4})$");
    private static final Pattern NUMBER_RE = Pattern.compile("-?\\d[\\d,]*(?:\\.\\d+)?");

    private final LlmFactory llmFactory;
    private final IdentityService identityService;
    private final AppProperties properties;
    private final ObjectMapper objectMapper;

    public record ParseInput(String inboxId, String filename, String ingestChannel,
                             String ocrText, String ocrProvider, Integer pageCount) {}

    public record ParsedDocument(Map<String, Object> payload, String promptVersion,
                                 String model, String providerName,
                                 Integer inputTokens, Integer outputTokens) {}

    public ParsedDocument parseDocument(ParseInput input) {
        LlmProvider primary = llmFactory.getLlmForAgent("parsing");
        try {
            return callProvider(primary, input);
        } catch (LlmTransientException | JsonSchemaValidationException e) {
            log.warn("document_parsing_primary_failed error={}", e.getMessage());
        }
        Optional<LlmProvider> secondary = llmFactory.getSecondaryLlmForAgent("parsing");
        if (secondary.isEmpty()) {
            throw new LlmException("document parsing primary failed and no secondary configured");
        }
        return callProvider(secondary.get(), input);
    }

    @SuppressWarnings("unchecked")
    private ParsedDocument callProvider(LlmProvider provider, ParseInput input) {
        AppProperties.DocumentParsing cfg = properties.getDocumentParsing();
        String[] prompt = loadPrompt(cfg.getPromptVersion());
        String system = prompt[0];
        String userTemplate = prompt[1];
        String user = userTemplate
                .replace("{filename}", input.filename())
                .replace("{ingest_channel}", input.ingestChannel())
                .replace("{ocr_provider}", input.ocrProvider() != null ? input.ocrProvider() : "unknown")
                .replace("{page_count}", input.pageCount() != null ? String.valueOf(input.pageCount()) : "unknown")
                .replace("{ocr_text}", input.ocrText());

        LlmResponse response = provider.generateText(system, user,
                cfg.getMaxTokens(), cfg.getTemperature());
        String raw = stripCodeFence(response.content());
        try {
            Map<String, Object> parsed = objectMapper.readValue(raw, Map.class);
            Map<String, Object> sanitized = sanitize(parsed);
            return new ParsedDocument(sanitized, cfg.getPromptVersion(),
                    response.model(), response.providerName(),
                    response.inputTokens(), response.outputTokens());
        } catch (Exception e) {
            throw new JsonSchemaValidationException("non-JSON response: " + e.getMessage(), e);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> sanitize(Map<String, Object> raw) {
        Map<String, Object> out = new LinkedHashMap<>();
        List<String> review = new ArrayList<>((List<String>) raw.getOrDefault("fields_needing_review", List.of()));

        String docType = (String) raw.get("document_type");
        if (!KNOWN_DOCUMENT_TYPES.contains(docType)) {
            review.add("document_type");
            docType = "needs_review";
        }
        out.put("document_type", docType);

        String law = (String) raw.get("law");
        if (GST_TYPES.contains(docType)) law = "GST";
        else if (IT_TYPES.contains(docType)) law = "IT";
        else if (!"GST".equals(law) && !"IT".equals(law)) law = null;
        out.put("law", law);

        out.put("client_name_on_document", cleanStr(raw.get("client_name_on_document")));
        out.put("pans_extracted", cleanPans(raw.get("pans_extracted")));
        out.put("gstins_extracted", cleanGstins(raw.get("gstins_extracted")));
        out.put("notice_number", cleanStr(raw.get("notice_number")));
        out.put("din_or_rfn", cleanStr(raw.get("din_or_rfn")));

        for (String f : List.of("issue_date", "receipt_date", "due_date", "hearing_date")) {
            out.put(f, cleanDate(raw.get(f), f, review));
        }
        out.put("financial_year", cleanYearRange(raw.get("financial_year")));
        out.put("assessment_year", cleanYearRange(raw.get("assessment_year")));
        out.put("authority", cleanStr(raw.get("authority")));
        out.put("demand_amount", cleanNumber(raw.get("demand_amount")));
        out.put("issues", cleanStrList(raw.get("issues")));
        out.put("documents_required", cleanStrList(raw.get("documents_required")));

        Object conf = raw.get("parse_confidence");
        double confidence = 0.0;
        if (conf instanceof Number n) {
            double d = n.doubleValue();
            if (d >= 0.0 && d <= 1.0) confidence = d;
            else review.add("parse_confidence");
        } else review.add("parse_confidence");
        out.put("parse_confidence", confidence);

        // Deduplicate review list
        LinkedHashSet<String> deduped = new LinkedHashSet<>();
        for (Object r : review) {
            if (r instanceof String s) deduped.add(s);
        }
        out.put("fields_needing_review", new ArrayList<>(deduped));
        return out;
    }

    private String cleanStr(Object val) {
        if (!(val instanceof String s)) return null;
        String t = s.strip();
        return t.isEmpty() ? null : t;
    }

    @SuppressWarnings("unchecked")
    private List<String> cleanStrList(Object val) {
        if (!(val instanceof List<?> list)) return List.of();
        return list.stream()
                .filter(v -> v instanceof String)
                .map(v -> ((String) v).strip())
                .filter(s -> !s.isEmpty())
                .toList();
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, String>> cleanPans(Object val) {
        if (!(val instanceof List<?> list)) return List.of();
        Set<String> seen = new LinkedHashSet<>();
        List<Map<String, String>> result = new ArrayList<>();
        for (Object item : list) {
            if (!(item instanceof Map<?, ?> m)) continue;
            Object panObj = m.get("value");
            if (!(panObj instanceof String panRaw)) continue;
            String pan = panRaw.strip().toUpperCase();
            if (!identityService.validatePanFormat(pan) || !seen.add(pan)) continue;
            String loc = m.get("location") instanceof String l ? l : "";
            result.add(Map.of("value", pan, "location", loc));
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, String>> cleanGstins(Object val) {
        if (!(val instanceof List<?> list)) return List.of();
        Set<String> seen = new LinkedHashSet<>();
        List<Map<String, String>> result = new ArrayList<>();
        for (Object item : list) {
            if (!(item instanceof Map<?, ?> m)) continue;
            Object gstinObj = m.get("value");
            if (!(gstinObj instanceof String gstinRaw)) continue;
            String gstin = gstinRaw.strip().toUpperCase();
            if (!identityService.validateGstinFormat(gstin) || !seen.add(gstin)) continue;
            String loc = m.get("location") instanceof String l ? l : "";
            String sc = m.get("state_code") instanceof String s && s.matches("^[0-9]{2}$")
                    ? s : gstin.substring(0, 2);
            result.add(Map.of("value", gstin, "location", loc, "state_code", sc));
        }
        return result;
    }

    private String cleanDate(Object val, String field, List<String> review) {
        if (val == null) return null;
        if (!(val instanceof String s)) { review.add(field); return null; }
        String t = s.strip();
        if (t.isEmpty()) return null;
        if (ISO_DATE.matcher(t).matches()) {
            try { LocalDate.parse(t); return t; }
            catch (Exception e) { review.add(field); return null; }
        }
        Matcher m = DMY.matcher(t);
        if (m.matches()) {
            int d = Integer.parseInt(m.group(1)), mo = Integer.parseInt(m.group(2));
            String yStr = m.group(3);
            if (yStr.length() == 2) yStr = "20" + yStr;
            try {
                return LocalDate.of(Integer.parseInt(yStr), mo, d)
                        .format(DateTimeFormatter.ISO_LOCAL_DATE);
            } catch (Exception e) { review.add(field); return null; }
        }
        review.add(field);
        return null;
    }

    private String cleanYearRange(Object val) {
        if (!(val instanceof String s)) return null;
        String t = s.strip().replace(" ", "");
        Matcher m = FY_FULL.matcher(t);
        if (!m.matches()) return null;
        String start = m.group(1), end = m.group(2);
        if (end.length() == 4) end = end.substring(2);
        return start + "-" + end;
    }

    private Double cleanNumber(Object val) {
        if (val == null) return null;
        if (val instanceof Number n) return n.doubleValue();
        if (val instanceof String s) {
            Matcher m = NUMBER_RE.matcher(s);
            if (!m.find()) return null;
            try { return Double.parseDouble(m.group(0).replace(",", "")); }
            catch (NumberFormatException e) { return null; }
        }
        return null;
    }

    private String[] loadPrompt(String version) {
        String path = "prompts/document_parsing_" + version + ".md";
        try {
            String text = new ClassPathResource(path)
                    .getContentAsString(StandardCharsets.UTF_8);
            String system = extractBlock(text, "## System prompt");
            String user = extractBlock(text, "## User prompt template");
            return new String[]{system, user};
        } catch (IOException e) {
            throw new LlmException("prompt version '" + version + "' not found at " + path);
        }
    }

    private String extractBlock(String text, String heading) {
        int idx = text.indexOf(heading);
        if (idx < 0) throw new LlmException("heading '" + heading + "' missing from prompt file");
        String after = text.substring(idx + heading.length());
        int fenceStart = after.indexOf("```");
        if (fenceStart < 0) throw new LlmException("no code block under '" + heading + "'");
        int nl = after.indexOf("\n", fenceStart + 3);
        if (nl < 0) throw new LlmException("malformed code block under '" + heading + "'");
        int fenceEnd = after.indexOf("```", nl + 1);
        if (fenceEnd < 0) throw new LlmException("unterminated code block under '" + heading + "'");
        return after.substring(nl + 1, fenceEnd).strip();
    }

    private String stripCodeFence(String text) {
        String s = text.strip();
        if (!s.startsWith("```")) return s;
        String[] lines = s.split("\n", -1);
        int start = lines[0].startsWith("```") ? 1 : 0;
        int end = lines[lines.length - 1].strip().startsWith("```") ? lines.length - 1 : lines.length;
        return String.join("\n", Arrays.copyOfRange(lines, start, end)).strip();
    }
}
