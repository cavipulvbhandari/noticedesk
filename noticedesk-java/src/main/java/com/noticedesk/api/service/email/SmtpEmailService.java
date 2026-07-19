package com.noticedesk.api.service.email;

import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;

@Slf4j
@RequiredArgsConstructor
public class SmtpEmailService implements EmailService {

    private final JavaMailSender mailSender;
    private final String fromAddress;
    private final String fromName;

    @Override
    public void send(String to, String subject, String htmlBody, String textBody) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(fromAddress, fromName);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(textBody != null ? textBody : "", htmlBody != null ? htmlBody : "");
            mailSender.send(message);
            log.info("smtp_email_sent to={} subject={}", to, subject);
        } catch (Exception e) {
            log.error("smtp_email_failed to={} error={}", to, e.getMessage());
            throw new RuntimeException("email send failed: " + e.getMessage(), e);
        }
    }
}
