package com.noticedesk.api.controller;

import com.noticedesk.api.exception.AppValidationException;
import com.noticedesk.api.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class SearchController {

    private final NamedParameterJdbcTemplate jdbc;

    @GetMapping("/search")
    @Transactional
    public Map<String, Object> search(
            @RequestParam String q,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "50") int page_size) {

        String tenantId = TenantContextHolder.getTenantId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        if (q == null || q.isBlank()) {
            throw new AppValidationException("Search query 'q' is required");
        }

        String likeQ = "%" + q.trim() + "%";
        int offset = (page - 1) * page_size;

        List<Map<String, Object>> results = jdbc.queryForList(
                """
                SELECT 'notice' AS result_type, n.notice_id::text AS id,
                       n.document_type AS title, n.lifecycle_status AS subtitle,
                       c.legal_name AS context
                FROM notices n
                JOIN clients c ON c.client_id = n.client_id
                JOIN client_registrations r ON r.registration_id = n.registration_id
                WHERE c.deleted_at IS NULL AND (
                  n.document_type ILIKE :q OR n.din_or_rfn ILIKE :q OR n.notice_number ILIKE :q
                  OR c.legal_name ILIKE :q OR c.pan ILIKE :q
                  OR r.identifier_value ILIKE :q
                )
                UNION ALL
                SELECT 'client' AS result_type, c.client_id::text AS id,
                       c.legal_name AS title, c.pan AS subtitle, c.entity_type AS context
                FROM clients c
                WHERE c.deleted_at IS NULL AND (c.legal_name ILIKE :q OR c.pan ILIKE :q)
                ORDER BY result_type, title
                LIMIT :limit OFFSET :offset
                """,
                Map.of("q", likeQ, "limit", page_size, "offset", offset));

        log.info("Search: q='{}' results={} tenant={}", q, results.size(), tenantId);

        return Map.of(
                "query", q,
                "items", results,
                "page", page,
                "page_size", page_size);
    }
}
