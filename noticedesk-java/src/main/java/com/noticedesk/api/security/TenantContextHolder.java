package com.noticedesk.api.security;

public final class TenantContextHolder {

    private static final ThreadLocal<AuthClaims> CONTEXT = new ThreadLocal<>();

    private TenantContextHolder() {}

    public static void set(AuthClaims claims) {
        CONTEXT.set(claims);
    }

    public static AuthClaims get() {
        return CONTEXT.get();
    }

    public static String getTenantId() {
        AuthClaims c = CONTEXT.get();
        if (c == null) throw new IllegalStateException("No tenant context on this thread");
        return c.tenantId();
    }

    public static String getUserId() {
        AuthClaims c = CONTEXT.get();
        if (c == null) throw new IllegalStateException("No tenant context on this thread");
        return c.userId();
    }

    public static void clear() {
        CONTEXT.remove();
    }
}
