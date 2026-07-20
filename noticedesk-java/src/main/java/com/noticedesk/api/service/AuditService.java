package com.noticedesk.api.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuditService {

    private final NamedParameterJdbcTemplate jdbc;
    private final ObjectMapper objectMapper;

    public void emit(
            String tenantId,
            String userId,
            String actionType,
            String entityType,
            Object entityId,
            Map<String, Object> beforeState,
            Map<String, Object> afterState,
            Integer riskTier
    ) {
        try {
            Map<String, Object> params = new HashMap<>();
            params.put("tenant_id", tenantId);
            params.put("user_id", userId);
            params.put("action_type", actionType);
            params.put("entity_type", entityType);
            params.put("entity_id", entityId != null ? entityId.toString() : null);
            params.put("before_state", beforeState != null ? objectMapper.writeValueAsString(beforeState) : null);
            params.put("after_state", afterState != null ? objectMapper.writeValueAsString(afterState) : null);
            params.put("risk_tier", riskTier);
            params.put("ip_address", null);
            params.put("user_agent", null);

            jdbc.update("""
                INSERT INTO audit_logs (
                    tenant_id, user_id, action_type, entity_type, entity_id,
                    before_state, after_state, risk_tier
                ) VALUES (
                    CAST(:tenant_id AS UUID), CAST(:user_id AS UUID),
                    :action_type, :entity_type,
                    CAST(:entity_id AS UUID),
                    CAST(:before_state AS JSONB), CAST(:after_state AS JSONB),
                    :risk_tier
                )
                """, params);
        } catch (Exception e) {
            log.error("audit_emit_failed action={} entity={} error={}", actionType, entityId, e.getMessage());
        }
    }

    public void emit(String tenantId, String userId, String actionType,
                     String entityType, Object entityId, Map<String, Object> afterState) {
        emit(tenantId, userId, actionType, entityType, entityId, null, afterState, null);
    }
}
