package com.noticedesk.api.service.ocr;

public record OcrResult(String text, int pageCount, String providerName) {}
