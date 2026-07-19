package com.noticedesk.api.service.email;

import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

/**
 * Stub email provider that writes each message to disk for offline preview.
 *
 * <p>Creates {@code {timestamp}_{to}.html} files under
 * {@code noticedesk.email.stub-dir}. Open the HTML file in a browser
 * to preview email templates without SMTP credentials.
 */
@Slf4j
public class StubEmailService implements EmailService {

    private static final DateTimeFormatter TIMESTAMP_FMT =
            DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC);

    private final Path stubDir;

    public StubEmailService(String stubDir) {
        this.stubDir = Path.of(stubDir).toAbsolutePath();
        try {
            Files.createDirectories(this.stubDir);
        } catch (IOException e) {
            log.warn("Could not create email stub dir {}: {}", stubDir, e.getMessage());
        }
    }

    @Override
    public void send(String to, String subject, String htmlBody, String textBody) {
        try {
            String timestamp = TIMESTAMP_FMT.format(Instant.now());
            String filename = timestamp + "_" + sanitize(to) + ".html";
            Path file = stubDir.resolve(filename);
            String body = (htmlBody != null && !htmlBody.isBlank()) ? htmlBody
                    : "<pre>" + escapeHtml(textBody != null ? textBody : "") + "</pre>";
            String content = "<!-- To: " + escapeHtml(to) + " | Subject: " + escapeHtml(subject)
                    + " -->\n" + body;
            Files.writeString(file, content, StandardCharsets.UTF_8);
            log.info("stub_email_written to={} subject={} file={}", to, subject, file);
        } catch (IOException e) {
            log.error("stub_email_write_failed to={} error={}", to, e.getMessage());
        }
    }

    private static String sanitize(String s) {
        if (s == null) return "unknown";
        String safe = s.replaceAll("[^a-zA-Z0-9._@-]", "_");
        return safe.substring(0, Math.min(safe.length(), 50));
    }

    private static String escapeHtml(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
}
