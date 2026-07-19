package com.noticedesk.api.security;

import com.noticedesk.api.config.AppProperties;
import com.noticedesk.api.exception.AuthException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class AuthFilter extends OncePerRequestFilter {

    private final AppProperties properties;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getServletPath();
        // Health and actuator endpoints skip auth
        return path.equals("/v1/health") || path.startsWith("/actuator");
    }

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain
    ) throws ServletException, IOException {
        try {
            AuthClaims claims = verify(request);
            TenantContextHolder.set(claims);
            filterChain.doFilter(request, response);
        } catch (AuthException e) {
            sendError(response, HttpStatus.UNAUTHORIZED, "unauthorized", e.getMessage());
        } finally {
            TenantContextHolder.clear();
        }
    }

    private AuthClaims verify(HttpServletRequest request) {
        String provider = properties.getAuth().getProvider();
        if ("dev".equals(provider)) {
            return verifyDev(request);
        }
        return verifyClerk(request);
    }

    private AuthClaims verifyDev(HttpServletRequest request) {
        if (!properties.isDevAuthAllowed()) {
            throw new AuthException("dev auth bypass is not allowed in this environment");
        }
        String userId = request.getHeader("x-dev-user-id");
        String tenantId = request.getHeader("x-dev-tenant-id");
        String email = request.getHeader("x-dev-email");
        if (userId == null || userId.isBlank() || tenantId == null || tenantId.isBlank()) {
            throw new AuthException("missing X-Dev-User-Id or X-Dev-Tenant-Id headers");
        }
        return new AuthClaims(userId.trim(), tenantId.trim(), email);
    }

    private AuthClaims verifyClerk(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.toLowerCase().startsWith("bearer ")) {
            throw new AuthException("missing bearer token");
        }
        // Sprint 1 stub: full Clerk JWKS verification pending
        throw new AuthException("clerk auth verification is not yet implemented");
    }

    private void sendError(HttpServletResponse response, HttpStatus status, String code, String message)
            throws IOException {
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write(
                String.format("{\"error\":{\"code\":\"%s\",\"message\":\"%s\",\"details\":{}}}", code, message)
        );
    }
}
