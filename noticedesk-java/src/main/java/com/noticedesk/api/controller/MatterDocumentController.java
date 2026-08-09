package com.noticedesk.api.controller;

import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.exception.AppValidationException;
import com.noticedesk.api.exception.NotFoundException;
import com.noticedesk.api.service.ocr.OcrFactory;
import com.noticedesk.api.service.storage.StorageFactory;
import com.noticedesk.api.service.AuditService;
import com.noticedesk.api.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class MatterDocumentController {

    private final NamedParameterJdbcTemplate jdbc;
    private final AuditService auditService;
    private final AppProperties properties;
    private final StorageFactory storageFactory;
    private final OcrFactory ocrFactory;

    // ---- POST /v1/matters/{matter_id}/documents ----

    @PostMapping("/matters/{matter_id}/documents")
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public Map<String, Object> uploadDocument(
            @PathVariable UUID matter_id,
            @RequestParam("file") MultipartFile file,
            @RequestParam(required = false) String document_type) throws Exception {

        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        // Verify matter exists
        var matterRows = jdbc.queryForList(
                "SELECT matter_id FROM matters WHERE matter_id = :mid AND deleted_at IS NULL",
                Map.of("mid", matter_id));
        if (matterRows.isEmpty()) {
            throw new NotFoundException("Matter not found: " + matter_id);
        }

        long maxBytes = properties.getStorage().getMaxUploadBytes();
        if (file.getSize() > maxBytes) {
            throw new AppValidationException(
                    String.format("File size %d exceeds maximum allowed %d bytes", file.getSize(), maxBytes));
        }

        byte[] bytes = file.getBytes();
        String key = UUID.randomUUID().toString();
        String contentType = file.getContentType() != null ? file.getContentType() : "application/octet-stream";
        String filename = file.getOriginalFilename() != null ? file.getOriginalFilename() : "document";
        String dtype = document_type != null ? document_type : "general";

        storageFactory.getStorage().store(bytes, key, contentType);

        UUID documentId = jdbc.queryForObject(
                """
                INSERT INTO documents (tenant_id, matter_id, filename, storage_key, file_size, mime_type, document_type, lifecycle_stage)
                VALUES (:tid, :mid, :fname, :key, :size, :mime, :dtype, 'received')
                RETURNING document_id
                """,
                Map.of(
                        "tid", tenantId,
                        "mid", matter_id,
                        "fname", filename,
                        "key", key,
                        "size", file.getSize(),
                        "mime", contentType,
                        "dtype", dtype),
                UUID.class);

        log.info("Matter document uploaded: doc_id={} matter_id={} tenant={}", documentId, matter_id, tenantId);

        // Trigger OCR inline
        try {
            String extractedText = ocrFactory.getPrimaryProvider().process(bytes, filename, contentType).text();

            jdbc.update(
                    "UPDATE documents SET extracted_text = :text WHERE document_id = :did",
                    Map.of("text", extractedText, "did", documentId));

        } catch (Exception e) {
            log.warn("OCR failed for document_id={}: {}", documentId, e.getMessage());
        }

        auditService.emit(tenantId, userId, "document.uploaded", "documents", documentId.toString(),
                null, Map.of("matter_id", matter_id.toString(), "filename", filename), 1);

        return Map.of(
                "document_id", documentId,
                "matter_id", matter_id,
                "filename", filename,
                "document_type", dtype,
                "lifecycle_stage", "received");
    }

    // ---- GET /v1/matters/{matter_id}/documents ----

    @GetMapping("/matters/{matter_id}/documents")
    @Transactional
    public List<Map<String, Object>> listDocuments(@PathVariable UUID matter_id) {
        String tenantId = TenantContextHolder.getTenantId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        // Verify matter exists
        var matterRows = jdbc.queryForList(
                "SELECT matter_id FROM matters WHERE matter_id = :mid AND deleted_at IS NULL",
                Map.of("mid", matter_id));
        if (matterRows.isEmpty()) {
            throw new NotFoundException("Matter not found: " + matter_id);
        }

        List<Map<String, Object>> documents = jdbc.queryForList(
                """
                SELECT document_id, filename, document_type, mime_type, file_size, lifecycle_stage,
                       LEFT(COALESCE(extracted_text,''), 200) AS excerpt, uploaded_at
                FROM documents WHERE matter_id = :mid ORDER BY uploaded_at ASC
                """,
                Map.of("mid", matter_id));

        return documents.stream().map(HashMap::new).map(m -> (Map<String, Object>) m).toList();
    }

    // ---- PATCH /v1/documents/{id} ----

    @PatchMapping("/documents/{id}")
    @Transactional
    public Map<String, Object> updateDocument(
            @PathVariable UUID id,
            @RequestBody Map<String, Object> body) {

        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        var docRows = jdbc.queryForList(
                "SELECT document_id FROM documents WHERE document_id = :did AND deleted_at IS NULL",
                Map.of("did", id));
        if (docRows.isEmpty()) {
            throw new NotFoundException("Document not found: " + id);
        }

        Map<String, Object> params = new HashMap<>();
        params.put("did", id);
        List<String> setClauses = new java.util.ArrayList<>();

        if (body.containsKey("document_type")) {
            setClauses.add("document_type = :document_type");
            params.put("document_type", body.get("document_type"));
        }
        if (body.containsKey("lifecycle_stage")) {
            setClauses.add("lifecycle_stage = :lifecycle_stage");
            params.put("lifecycle_stage", body.get("lifecycle_stage"));
        }

        if (setClauses.isEmpty()) {
            throw new AppValidationException("No valid fields to update");
        }

        jdbc.update("UPDATE documents SET " + String.join(", ", setClauses) + " WHERE document_id = :did", params);

        auditService.emit(tenantId, userId, "document.updated", "documents", id.toString(),
                null, body, 1);

        log.info("Document updated: doc_id={} tenant={}", id, tenantId);

        var updated = jdbc.queryForList(
                "SELECT document_id, filename, document_type, lifecycle_stage FROM documents WHERE document_id = :did",
                Map.of("did", id));
        return new HashMap<>(updated.get(0));
    }

    // ---- DELETE /v1/documents/{id} ----

    @DeleteMapping("/documents/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Transactional
    public void deleteDocument(@PathVariable UUID id) {
        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        var docRows = jdbc.queryForList(
                "SELECT document_id FROM documents WHERE document_id = :did AND deleted_at IS NULL",
                Map.of("did", id));
        if (docRows.isEmpty()) {
            throw new NotFoundException("Document not found: " + id);
        }

        jdbc.update(
                "UPDATE documents SET deleted_at = NOW() WHERE document_id = :did",
                Map.of("did", id));

        auditService.emit(tenantId, userId, "document.deleted", "documents", id.toString(),
                null, Map.of(), 1);

        log.info("Document soft-deleted: doc_id={} tenant={}", id, tenantId);
    }
}
