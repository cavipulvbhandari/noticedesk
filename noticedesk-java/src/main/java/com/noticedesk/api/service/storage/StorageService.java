package com.noticedesk.api.service.storage;

public interface StorageService {
    String store(byte[] data, String key, String contentType);
    byte[] retrieve(String key);
    boolean exists(String key);
}
