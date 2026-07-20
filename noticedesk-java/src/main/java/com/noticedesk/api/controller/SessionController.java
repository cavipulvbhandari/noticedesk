package com.noticedesk.api.controller;

import com.noticedesk.api.exception.NotFoundException;
import com.noticedesk.api.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/v1")
@RequiredArgsConstructor
public class SessionController {

    private final NamedParameterJdbcTemplate jdbc;

    @GetMapping("/session")
    @Transactional
    public Map<String, Object> getSession() {
        String tenantId = TenantContextHolder.getTenantId();
        String userId = TenantContextHolder.getUserId();

        jdbc.queryForObject("SELECT set_config('app.current_tenant', :tid, true)",
                Map.of("tid", tenantId), String.class);

        var rows = jdbc.queryForList(
                "SELECT user_id, name, email, role, created_at FROM users WHERE user_id = :uid",
                Map.of("uid", userId));

        if (rows.isEmpty()) {
            throw new NotFoundException("User not found");
        }

        Map<String, Object> user = new HashMap<>(rows.get(0));
        user.put("tenant_id", tenantId);

        log.info("Session loaded for user={} tenant={}", userId, tenantId);
        return user;
    }
}
