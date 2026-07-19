package com.noticedesk.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.exception.AppValidationException;
import com.noticedesk.api.service.ocr.OcrFactory;
import com.noticedesk.api.service.storage.StorageFactory;
import com.noticedesk.api.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class EmailController {

    private final NamedParameterJdbcTemplate jdbc;
    private final AppProperties properties;
    private final StorageFactory storageFactory;
    private final OcrFactory ocrFactory;
    private final ObjectMapper objectMapper;

    @PostMapping("/email/inbound")
    @ResponseStatus(HttpStatus.ACCEPTED)
    @Transactional
    public Map<String, Object> inboundEmail(
            @RequestHeader(value = "X-Webhook-Signature", required = false) String signature,
            @RequestBody byte[] rawBody) throws Exception {

        String tenantId = TenantContextHolder.getTenantId();

        jdbc.update("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId));

        // Validate HMAC signature
        String secret = properties.getEmail() != null ? properties.getEmail().getInboundWebhookSecret() : null;
        if (secret != null) {
            if (signature == null || signature.isBlank()) {
                throw new AppValidationException("Missing X-Webhook-Signature header");
            }
            String expected = computeHmacSha256(secret, rawBody);
            if (!expected.equalsIgnoreCase(signature)) {
                throw new AppValidationException("Invalid webhook signature");
            }
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> payload = objectMapper.readValue(rawBody, Map.class);

        String recipient = (String) payload.get("recipient");
        String sender = (String) payload.get("sender");
        String subject = (String) payload.get("subject");

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> attachments = (List<Map<String, Object>>) payload.getOrDefault("attachments", List.of());

        int processedCount = 0;

        for (Map<String, Object> attachment : attachments) {
            String filename = (String) attachment.get("filename");
            String contentType = (String) attachment.get("content_type");
            String contentBase64 = (String) attachment.get("content_base64");

            if (contentBase64 == null || contentBase64.isBlank()) {
                log.warn("Skipping attachment with no content: {}", filename);
                continue;
            }

            byte[] bytes = Base64.getDecoder().decode(contentBase64);
            String key = UUID.randomUUID().toString();

            storageFactory.getStorage().store(bytes, key, contentType != null ? contentType : "application/octet-stream");

            UUID inboxId = jdbc.queryForObject(
                    """
                    INSERT INTO documents_inbox
                        (tenant_id, filename, storage_key, file_size, mime_type, ingest_channel,
                         email_sender, email_subject, email_recipient, status)
                    VALUES (:tid, :filename, :key, :size, :mime, 'email',
                            :sender, :subject, :recipient, 'pending')
                    RETURNING inbox_id
                    """,
                    Map.of(
                            "tid", tenantId,
                            "filename", filename != null ? filename : "attachment",
                            "key", key,
                            "size", (long) bytes.length,
                            "mime", contentType != null ? contentType : "application/octet-stream",
                            "sender", sender != null ? sender : "",
                            "subject", subject != null ? subject : "",
                            "recipient", recipient != null ? recipient : ""),
                    UUID.class);

            log.info("Email attachment ingested: inbox_id={} filename={} tenant={}", inboxId, filename, tenantId);

            // Trigger OCR inline
            try {
                var ocrResult = ocrFactory.getPrimaryProvider().process(
                        bytes, filename != null ? filename : "attachment", contentType);
                String ocrText = ocrResult.text();
                String ocrProvider = ocrResult.providerName();

                jdbc.update(
                        """
                        UPDATE documents_inbox
                        SET ocr_text = :text, ocr_provider = :provider, status = 'ocr_complete'
                        WHERE inbox_id = :id
                        """,
                        Map.of("text", ocrText, "provider", ocrProvider, "id", inboxId));

            } catch (Exception e) {
                log.warn("OCR failed for inbox_id={}: {}", inboxId, e.getMessage());
                jdbc.update(
                        "UPDATE documents_inbox SET status = 'ocr_failed' WHERE inbox_id = :id",
                        Map.of("id", inboxId));
            }

            processedCount++;
        }

        log.info("Email inbound processed: sender={} attachments={} tenant={}", sender, processedCount, tenantId);

        return Map.of(
                "status", "accepted",
                "processed_attachments", processedCount);
    }

    private String computeHmacSha256(String secret, byte[] data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] hmac = mac.doFinal(data);
        return HexFormat.of().formatHex(hmac);
    }
}
