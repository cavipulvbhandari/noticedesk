package com.noticedesk.api;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(properties = {
    "spring.datasource.url=jdbc:postgresql://localhost:5432/noticedesk_test",
    "spring.flyway.enabled=false",
    "noticedesk.llm.provider-primary=stub",
    "noticedesk.ocr.provider-primary=stub",
    "noticedesk.storage.backend=local",
    "noticedesk.email.provider=stub",
    "noticedesk.workflow.backend=inline",
    "noticedesk.auth.provider=dev"
})
class NoticedeskApiApplicationTests {

    @Test
    void contextLoads() {
        // Spring context loads without error — verifies bean wiring
    }
}
