package com.noticedesk.api.controller;

import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.exception.AppValidationException;
import com.noticedesk.api.exception.NotFoundException;
import com.noticedesk.api.service.AuditService;
import com.noticedesk.api.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class RegistrationController {

    private static final Set<String> ALLOWED_UPDATE_FIELDS = Set.of(
            "state_code", "state_name", "jurisdiction_office", "registration_status");

    private final NamedParameterJdbcTemplate jdbc;
    private final AuditService auditService;
    private final AppProperties properties;

    @GetMapping("/registrations/{id}/notices")
    @Transactional
    public List<Map<String, Object>> getNoticesForRegistration(@PathVariable UUID id) {
        String tenantId = TenantContextHolder.getTenantId();

        jdbc.update("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId));

        // Verify registration exists
        var regRows = jdbc.queryForList(
                "SELECT registration_id FROM client_registrations WHERE registration_id = :rid",
                Map.of("rid", id));
        if (regRows.isEmpty()) {
            throw new NotFoundException("Registration not found: " + id);
        }

        List<Map<String, Object>> notices = jdbc.queryForList(
                """
                SELECT n.notice_id, n.law, n.document_type, n.due_date, n.lifecycle_status,
                       n.financial_year, n.assessment_year
                FROM notices n
                WHERE n.registration_id = :rid
                ORDER BY n.due_date ASC NULLS LAST
                """,
                Map.of("rid", id));

        return notices.stream()
                .map(HashMap::new)
                .map(m -> (Map<String, Object>) m)
                .toList();
    }

    @PatchMapping("/registrations/{id}")
    @Transactional
    public Map<String, Object> updateRegistration(
            @PathVariable UUID id,
            @RequestBody Map<String, Object> body) {

        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.update("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId));

        var existing = jdbc.queryForList(
                """
                SELECT registration_id, registration_type, identifier_value, state_code,
                       state_name, jurisdiction_office, registration_status
                FROM client_registrations WHERE registration_id = :rid
                """,
                Map.of("rid", id));

        if (existing.isEmpty()) {
            throw new NotFoundException("Registration not found: " + id);
        }

        Map<String, Object> params = new HashMap<>();
        params.put("rid", id);
        List<String> setClauses = new ArrayList<>();

        for (Map.Entry<String, Object> entry : body.entrySet()) {
            String field = toSnakeCase(entry.getKey());
            if (ALLOWED_UPDATE_FIELDS.contains(field)) {
                setClauses.add(field + " = :" + field);
                params.put(field, entry.getValue());
            }
        }

        if (setClauses.isEmpty()) {
            throw new AppValidationException("No valid fields to update");
        }

        setClauses.add("updated_at = NOW()");
        String sql = "UPDATE client_registrations SET " + String.join(", ", setClauses)
                + " WHERE registration_id = :rid";

        jdbc.update(sql, params);

        auditService.emit(tenantId, userId, "registration.updated", "client_registrations",
                id.toString(), existing.get(0), params, 1);

        log.info("Registration updated: reg_id={} tenant={}", id, tenantId);

        var updated = jdbc.queryForList(
                """
                SELECT registration_id, registration_type, identifier_value, state_code,
                       state_name, jurisdiction_office, registration_status, created_at
                FROM client_registrations WHERE registration_id = :rid
                """,
                Map.of("rid", id));

        return new HashMap<>(updated.get(0));
    }

    private String toSnakeCase(String camelCase) {
        return camelCase.replaceAll("([a-z])([A-Z])", "$1_$2").toLowerCase();
    }
}
