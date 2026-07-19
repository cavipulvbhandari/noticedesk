package com.noticedesk.api.service.email;

import com.noticedesk.api.config.AppProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailFactory {

    private final AppProperties properties;
    private final JavaMailSender mailSender;

    private volatile EmailService emailService;

    public EmailService getEmailService() {
        if (emailService == null) {
            synchronized (this) {
                if (emailService == null) {
                    AppProperties.Email cfg = properties.getEmail();
                    emailService = switch (cfg.getProvider()) {
                        case "smtp" -> {
                            log.info("email_provider=smtp from={}", cfg.getFromAddress());
                            yield new SmtpEmailService(mailSender, cfg.getFromAddress(), cfg.getFromName());
                        }
                        default -> {
                            log.info("email_provider=stub dir={}", cfg.getStubDir());
                            yield new StubEmailService(cfg.getStubDir());
                        }
                    };
                }
            }
        }
        return emailService;
    }
}
