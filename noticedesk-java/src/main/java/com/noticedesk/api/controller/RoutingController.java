package com.noticedesk.api.controller;

import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.exception.AppValidationException;
import com.noticedesk.api.exception.ForbiddenException;
import com.noticedesk.api.exception.NotFoundException;
import com.noticedesk.api.service.AuditService;
import com.noticedesk.api.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class RoutingController {

    private static final Pattern PAN_PATTERN = Pattern.compile("^[A-Z]{5}[0-9]{4}[A-Z]$");
    private static final Pattern GSTIN_PATTERN = Pattern.compile("^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$");

    private final NamedParameterJdbcTemplate jdbc;
    private final AuditService auditService;
    private final AppProperties properties;

    @GetMapping("/inbox/{id}/parsed")
    @Transactional
    public Map<String, Object> getParsedInbox(@PathVariable UUID id) {
        String tenantId = TenantContextHolder.getTenantId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        var rows = jdbc.queryForList(
                """
                SELECT inbox_id, filename, ocr_text, parsed_json, routing_status, routing_error,
                       routed_notice_id, routed_matter_id, created_at
                FROM documents_inbox WHERE inbox_id = :id
                """,
                Map.of("id", id));

        if (rows.isEmpty()) {
            throw new NotFoundException("Inbox item not found: " + id);
        }

        return new HashMap<>(rows.get(0));
    }

    @PostMapping("/inbox/{id}/route_manually")
    @Transactional
    public Map<String, Object> routeManually(
            @PathVariable UUID id,
            @RequestBody Map<String, Object> body) {

        String tenantId = TenantContextHolder.getTenantId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        // Verify inbox item exists
        var rows = jdbc.queryForList(
                "SELECT inbox_id, routing_status FROM documents_inbox WHERE inbox_id = :id",
                Map.of("id", id));
        if (rows.isEmpty()) {
            throw new NotFoundException("Inbox item not found: " + id);
        }

        UUID matterId = body.containsKey("matter_id") ? UUID.fromString((String) body.get("matter_id")) : null;
        UUID noticeId = body.containsKey("notice_id") ? UUID.fromString((String) body.get("notice_id")) : null;

        jdbc.update(
                """
                UPDATE documents_inbox
                SET routing_status = 'manual', routed_matter_id = :mid, routed_notice_id = :nid
                WHERE inbox_id = :id
                """,
                Map.of("id", id, "mid", matterId, "nid", noticeId));

        log.info("Inbox item manually routed: inbox_id={} matter_id={} tenant={}", id, matterId, tenantId);

        return Map.of("inbox_id", id, "routing_status", "manual");
    }

    @PostMapping("/inbox/{id}/reject")
    @Transactional
    public Map<String, Object> rejectInbox(
            @PathVariable UUID id,
            @RequestBody(required = false) Map<String, Object> body) {

        String tenantId = TenantContextHolder.getTenantId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        var rows = jdbc.queryForList(
                "SELECT inbox_id FROM documents_inbox WHERE inbox_id = :id",
                Map.of("id", id));
        if (rows.isEmpty()) {
            throw new NotFoundException("Inbox item not found: " + id);
        }

        String reason = (body != null && body.containsKey("reason")) ? (String) body.get("reason") : null;

        jdbc.update(
                "UPDATE documents_inbox SET routing_status = 'rejected', routing_error = :reason WHERE inbox_id = :id",
                Map.of("id", id, "reason", reason != null ? reason : ""));

        log.info("Inbox item rejected: inbox_id={} tenant={}", id, tenantId);

        return Map.of("inbox_id", id, "routing_status", "rejected");
    }

    @PostMapping("/clients")
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public Map<String, Object> createClient(@RequestBody CreateClientRequest request) {
        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        if (request.pan() == null || !PAN_PATTERN.matcher(request.pan().toUpperCase()).matches()) {
            throw new AppValidationException("Invalid PAN format. Expected pattern: ABCDE1234F");
        }

        String pan = request.pan().toUpperCase();

        UUID clientId = jdbc.queryForObject(
                """
                INSERT INTO clients (tenant_id, pan, legal_name, trade_name, entity_type, industry, email, phone)
                VALUES (CAST(:tid AS UUID), :pan, :legal, :trade, :entity, :industry, :email, :phone)
                RETURNING client_id
                """,
                Map.of(
                        "tid", tenantId,
                        "pan", pan,
                        "legal", request.legalName() != null ? request.legalName() : "",
                        "trade", request.tradeName() != null ? request.tradeName() : "",
                        "entity", request.entityType() != null ? request.entityType() : "",
                        "industry", request.industry() != null ? request.industry() : "",
                        "email", request.email() != null ? request.email() : "",
                        "phone", request.phone() != null ? request.phone() : ""),
                UUID.class);

        String legalName = request.legalName() != null ? request.legalName() : "";
        auditService.emit(tenantId, userId, "client.created", "clients", clientId.toString(),
                null, Map.of("pan", pan, "legal_name", legalName), 1);

        log.info("Client created: client_id={} pan={} tenant={}", clientId, pan, tenantId);

        return Map.of("client_id", clientId, "pan", pan, "legal_name", legalName);
    }

    @PostMapping("/clients/{id}/registrations")
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public Map<String, Object> addRegistration(
            @PathVariable UUID id,
            @RequestBody AddRegistrationRequest request) {

        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        // Verify client exists
        var clientRows = jdbc.queryForList(
                "SELECT client_id, pan FROM clients WHERE client_id = :cid AND deleted_at IS NULL",
                Map.of("cid", id));
        if (clientRows.isEmpty()) {
            throw new NotFoundException("Client not found: " + id);
        }
        String clientPan = (String) clientRows.get(0).get("pan");

        if (request.registrationType() == null) {
            throw new AppValidationException("registrationType is required (GST or IT)");
        }

        String rtype = request.registrationType().toUpperCase();

        // Validate identifier based on type
        if ("IT".equals(rtype)) {
            if (request.identifierValue() == null || !PAN_PATTERN.matcher(request.identifierValue().toUpperCase()).matches()) {
                throw new AppValidationException("Invalid PAN format for IT registration");
            }
        } else if ("GST".equals(rtype)) {
            if (request.identifierValue() == null || !GSTIN_PATTERN.matcher(request.identifierValue().toUpperCase()).matches()) {
                throw new AppValidationException("Invalid GSTIN format for GST registration");
            }
            // Check PAN-GSTIN consistency: characters 3-12 of GSTIN should match PAN
            String gstinPanPart = request.identifierValue().substring(2, 12).toUpperCase();
            if (!gstinPanPart.equals(clientPan.toUpperCase())) {
                throw new AppValidationException(
                        "GSTIN PAN segment does not match client PAN. GSTIN[2:12]=" + gstinPanPart + " expected=" + clientPan);
            }
        } else {
            throw new AppValidationException("registrationType must be GST or IT");
        }

        UUID registrationId = jdbc.queryForObject(
                """
                INSERT INTO client_registrations
                    (tenant_id, client_id, registration_type, identifier_value, state_code, state_name, jurisdiction_office)
                VALUES (:tid, :cid, :rtype, :identifier, :sc, :sn, :jo)
                RETURNING registration_id
                """,
                Map.of(
                        "tid", tenantId,
                        "cid", id,
                        "rtype", rtype,
                        "identifier", request.identifierValue().toUpperCase(),
                        "sc", request.stateCode() != null ? request.stateCode() : "",
                        "sn", request.stateName() != null ? request.stateName() : "",
                        "jo", request.jurisdictionOffice() != null ? request.jurisdictionOffice() : ""),
                UUID.class);

        auditService.emit(tenantId, userId, "registration.created", "client_registrations",
                registrationId.toString(),
                null, Map.of("client_id", id.toString(), "type", rtype), 1);

        log.info("Registration added: reg_id={} client_id={} type={} tenant={}", registrationId, id, rtype, tenantId);

        return Map.of(
                "registration_id", registrationId,
                "client_id", id,
                "registration_type", rtype,
                "identifier_value", request.identifierValue().toUpperCase());
    }

    // ---- Request records ----

    public record CreateClientRequest(
            String pan,
            String legalName,
            String tradeName,
            String entityType,
            String industry,
            String email,
            String phone) {}

    public record AddRegistrationRequest(
            String registrationType,
            String identifierValue,
            String stateCode,
            String stateName,
            String jurisdictionOffice) {}
}
