package com.noticedesk.api.service.email;

public interface EmailService {
    void send(String to, String subject, String htmlBody, String textBody);
}
