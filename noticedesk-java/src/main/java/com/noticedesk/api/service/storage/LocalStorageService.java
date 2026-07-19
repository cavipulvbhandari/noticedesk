package com.noticedesk.api.service.storage;

import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Filesystem-backed storage for development and testing.
 *
 * <p>Keys are treated as relative paths under {@code baseDir}.
 * Absolute paths and keys containing {@code ..} components are rejected
 * to prevent escaping the configured root.
 */
@Slf4j
public class LocalStorageService implements StorageService {

    private final Path baseDir;

    public LocalStorageService(String localDir) {
        this.baseDir = Path.of(localDir).toAbsolutePath().normalize();
        try {
            Files.createDirectories(baseDir);
        } catch (IOException e) {
            log.warn("Could not create local storage dir {}: {}", localDir, e.getMessage());
        }
    }

    @Override
    public String store(byte[] data, String key, String contentType) {
        try {
            Path target = resolve(key);
            Files.createDirectories(target.getParent());
            Files.write(target, data);
            log.debug("stored key={} bytes={}", key, data.length);
            return key;
        } catch (IOException e) {
            throw new RuntimeException("local storage write failed for key=" + key, e);
        }
    }

    @Override
    public byte[] retrieve(String key) {
        Path target = resolve(key);
        if (!Files.exists(target)) {
            throw new RuntimeException("object not found: " + key);
        }
        try {
            return Files.readAllBytes(target);
        } catch (IOException e) {
            throw new RuntimeException("local storage read failed for key=" + key, e);
        }
    }

    @Override
    public boolean exists(String key) {
        try {
            return Files.exists(resolve(key));
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    /**
     * Resolves {@code key} relative to {@code baseDir}, rejecting unsafe keys.
     */
    private Path resolve(String key) {
        if (key == null || key.isBlank() || key.startsWith("/")) {
            throw new IllegalArgumentException("Unsafe storage key: '" + key + "'");
        }
        Path resolved = baseDir.resolve(key).normalize();
        if (!resolved.startsWith(baseDir)) {
            throw new IllegalArgumentException(
                    "Storage key escapes base directory: '" + key + "'");
        }
        return resolved;
    }
}
