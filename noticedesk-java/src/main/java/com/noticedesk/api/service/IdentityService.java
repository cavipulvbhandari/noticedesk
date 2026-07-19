package com.noticedesk.api.service;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class IdentityService {

    private static final Pattern PAN_REGEX = Pattern.compile("^[A-Z]{5}[0-9]{4}[A-Z]$");
    private static final Pattern GSTIN_REGEX = Pattern.compile(
            "^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$");

    private final NamedParameterJdbcTemplate jdbc;

    public boolean validatePanFormat(String pan) {
        return pan != null && PAN_REGEX.matcher(pan).matches();
    }

    public boolean validateGstinFormat(String gstin) {
        return gstin != null && GSTIN_REGEX.matcher(gstin).matches();
    }

    public String extractPanFromGstin(String gstin) {
        if (!validateGstinFormat(gstin)) {
            throw new IllegalArgumentException("invalid GSTIN: " + gstin);
        }
        return gstin.substring(2, 12);
    }

    public String extractStateCodeFromGstin(String gstin) {
        if (!validateGstinFormat(gstin)) {
            throw new IllegalArgumentException("invalid GSTIN: " + gstin);
        }
        return gstin.substring(0, 2);
    }

    public boolean reconcilePanGstin(String pan, String gstin) {
        if (!validatePanFormat(pan) || !validateGstinFormat(gstin)) return false;
        return extractPanFromGstin(gstin).equals(pan);
    }

    public record ClientRef(UUID clientId, UUID tenantId, String pan, String legalName) {}

    public record RegistrationRef(
            UUID registrationId, UUID tenantId, UUID clientId,
            String registrationType, String identifierValue, String stateCode) {}

    public ClientRef resolveClientByPan(String tenantId, String pan) {
        if (!validatePanFormat(pan)) {
            throw new IllegalArgumentException("invalid PAN: " + pan);
        }
        return jdbc.query(
                "SELECT client_id, tenant_id, pan, legal_name FROM clients " +
                "WHERE tenant_id = :tid AND pan = :pan AND deleted_at IS NULL",
                Map.of("tid", tenantId, "pan", pan),
                rs -> {
                    if (!rs.next()) return null;
                    return new ClientRef(
                            UUID.fromString(rs.getString("client_id")),
                            UUID.fromString(rs.getString("tenant_id")),
                            rs.getString("pan"),
                            rs.getString("legal_name")
                    );
                }
        );
    }

    public RegistrationRef resolveRegistrationByIdentifier(String tenantId, String identifierValue) {
        if (!validatePanFormat(identifierValue) && !validateGstinFormat(identifierValue)) {
            throw new IllegalArgumentException("invalid identifier: " + identifierValue);
        }
        return jdbc.query(
                "SELECT registration_id, tenant_id, client_id, registration_type, " +
                "       identifier_value, state_code " +
                "FROM client_registrations " +
                "WHERE tenant_id = :tid AND identifier_value = :iv",
                Map.of("tid", tenantId, "iv", identifierValue),
                rs -> {
                    if (!rs.next()) return null;
                    return new RegistrationRef(
                            UUID.fromString(rs.getString("registration_id")),
                            UUID.fromString(rs.getString("tenant_id")),
                            UUID.fromString(rs.getString("client_id")),
                            rs.getString("registration_type"),
                            rs.getString("identifier_value"),
                            rs.getString("state_code")
                    );
                }
        );
    }
}
