package com.noticedesk.api.service.storage;

import com.noticedesk.api.config.AppProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

@Slf4j
@Service
@RequiredArgsConstructor
public class StorageFactory {

    private final AppProperties properties;
    private volatile StorageService storageService;

    public StorageService getStorage() {
        if (storageService == null) {
            synchronized (this) {
                if (storageService == null) {
                    AppProperties.Storage cfg = properties.getStorage();
                    storageService = switch (cfg.getBackend()) {
                        case "s3" -> {
                            S3Client s3 = S3Client.builder()
                                    .region(Region.of(cfg.getAwsRegion()))
                                    .build();
                            log.info("storage_backend=s3 bucket={}", cfg.getS3Bucket());
                            yield new S3StorageService(s3, cfg.getS3Bucket());
                        }
                        default -> {
                            log.info("storage_backend=local dir={}", cfg.getLocalDir());
                            yield new LocalStorageService(cfg.getLocalDir());
                        }
                    };
                }
            }
        }
        return storageService;
    }
}
