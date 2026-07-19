package com.noticedesk.api.agent;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Citation Verification Agent — Tier 1 (IndianKanoon or stub).
 *
 * Extracts citations from a draft text blob using a simple "v." pattern,
 * then verifies each against the configured provider. Stub returns an empty
 * result set (used in dev/CI); IndianKanoon calls the public search API.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class CitationVerificationAgent {

    /** Matches "Foo Bar v. Baz Corp" — case names that contain " v. " */
    private static final Pattern CITATION_RE = Pattern.compile(
            "([A-Za-z][^\\n.]{2,60})\\s+v\\.\\s+([A-Za-z][^\\n,.(]{2,60})",
            Pattern.CASE_INSENSITIVE);

    private static final String IK_BASE_URL  = "https://api.indiankanoon.org/search/";
    private static final int    HTTP_TIMEOUT_SECS = 10;

    private final ObjectMapper objectMapper;

    // ---- Public data types -----------------------------------------------

    public record VerifiedCitation(
            String caseName,
            String citationString,
            String rawText,
            String status,           // VERIFIED | VERIFIED_PARTIAL | UNVERIFIED
            String sourceUrl,
            String verifiedParagraphText,
            Double propositionMatchConfidence,
            String actionTaken) {}   // passed | flagged | stripped

    public record CitationVerificationResult(
            Map<String, Object>   summary,
            List<VerifiedCitation> citations) {}

    // ---- Public API ------------------------------------------------------

    /**
     * Extract citations from {@code draftText} and verify them.
     *
     * @param draftText        concatenated HTML/text of all draft sections
     * @param citationProvider {@code "stub"} or {@code "indiankanoon"}
     */
    public CitationVerificationResult verify(String draftText, String citationProvider) {
        if ("stub".equalsIgnoreCase(citationProvider) || draftText == null || draftText.isBlank()) {
            return stubResult();
        }

        List<String> caseNames = extractCaseNames(draftText);
        if (caseNames.isEmpty()) {
            return emptyResult();
        }

        if ("indiankanoon".equalsIgnoreCase(citationProvider)) {
            return verifyWithIndianKanoon(caseNames);
        }

        // Unknown provider — degrade gracefully to stub
        log.warn("unknown citation provider '{}', falling back to stub", citationProvider);
        return stubResult();
    }

    // ---- Private: extraction ---------------------------------------------

    private List<String> extractCaseNames(String text) {
        Set<String>  seen  = new LinkedHashSet<>();
        List<String> names = new ArrayList<>();
        Matcher m = CITATION_RE.matcher(text);
        while (m.find()) {
            String caseName = (m.group(1).strip() + " v. " + m.group(2).strip()).trim();
            if (seen.add(caseName.toLowerCase())) {
                names.add(caseName);
            }
        }
        return names;
    }

    // ---- Private: IndianKanoon verification ------------------------------

    private CitationVerificationResult verifyWithIndianKanoon(List<String> caseNames) {
        HttpClient httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();

        String token = System.getenv("INDIANKANOON_API_TOKEN");

        List<VerifiedCitation> citations = new ArrayList<>();
        int verified = 0, partial = 0, stripped = 0;

        for (String caseName : caseNames) {
            VerifiedCitation vc = lookupIndianKanoon(httpClient, token, caseName);
            citations.add(vc);
            switch (vc.status()) {
                case "VERIFIED"         -> verified++;
                case "VERIFIED_PARTIAL" -> partial++;
                default                 -> stripped++;
            }
        }

        Map<String, Object> summary = Map.of(
                "total",      citations.size(),
                "verified",   verified,
                "partial",    partial,
                "unverified", stripped,
                "removed",    stripped);

        log.info("citation verification complete provider=indiankanoon total={} verified={} stripped={}",
                citations.size(), verified, stripped);
        return new CitationVerificationResult(summary, citations);
    }

    private VerifiedCitation lookupIndianKanoon(HttpClient client, String token, String caseName) {
        String encoded = URLEncoder.encode(caseName, StandardCharsets.UTF_8);
        String url = IK_BASE_URL + "?formInput=" + encoded + "&pagenum=0";

        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(HTTP_TIMEOUT_SECS))
                .GET();
        if (token != null && !token.isBlank()) {
            builder.header("Authorization", "Token " + token);
        }

        try {
            HttpResponse<String> response = client.send(
                    builder.build(), HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() != 200) {
                log.warn("indiankanoon returned {} for '{}'", response.statusCode(), caseName);
                return unverified(caseName, null);
            }

            Map<String, Object> data = objectMapper.readValue(
                    response.body(), new TypeReference<>() {});

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> docs =
                    (List<Map<String, Object>>) data.getOrDefault("docs", List.of());

            if (docs.isEmpty()) {
                return unverified(caseName, null);
            }

            Map<String, Object> first = docs.get(0);
            String tid  = first.get("tid")   != null ? first.get("tid").toString()   : null;
            String docUrl = tid != null ? "https://indiankanoon.org/doc/" + tid + "/" : null;

            return new VerifiedCitation(
                    caseName, null, caseName,
                    "VERIFIED", docUrl, null, 0.85, "passed");

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return unverified(caseName, null);
        } catch (Exception e) {
            log.warn("indiankanoon lookup failed for '{}': {}", caseName, e.getMessage());
            return unverified(caseName, null);
        }
    }

    // ---- Private: helpers ------------------------------------------------

    private VerifiedCitation unverified(String caseName, String rawText) {
        return new VerifiedCitation(caseName, null,
                rawText != null ? rawText : caseName,
                "UNVERIFIED", null, null, null, "stripped");
    }

    private CitationVerificationResult stubResult() {
        return new CitationVerificationResult(
                Map.of("total", 0, "verified", 0, "unverified", 0, "removed", 0),
                List.of());
    }

    private CitationVerificationResult emptyResult() {
        return new CitationVerificationResult(
                Map.of("total", 0, "verified", 0, "unverified", 0, "removed", 0),
                List.of());
    }
}
