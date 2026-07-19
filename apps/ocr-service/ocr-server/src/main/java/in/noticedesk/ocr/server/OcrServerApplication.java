package in.noticedesk.ocr.server;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/** Entry point for the NoticeDesk self-hosted OCR service. */
@SpringBootApplication
@ConfigurationPropertiesScan
public class OcrServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(OcrServerApplication.class, args);
    }
}
