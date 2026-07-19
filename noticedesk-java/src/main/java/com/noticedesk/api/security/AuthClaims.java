package com.noticedesk.api.security;

public record AuthClaims(String userId, String tenantId, String email) {}
