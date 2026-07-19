package com.noticedesk.api.service.ocr;

public interface OcrProvider {
    String getName();
    OcrResult process(byte[] fileBytes, String filename, String mimeType);
}
