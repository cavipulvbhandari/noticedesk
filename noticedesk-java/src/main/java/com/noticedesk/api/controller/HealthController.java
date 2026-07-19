package com.noticedesk.api.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/v1")
public class HealthController {

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok");
    }
}
