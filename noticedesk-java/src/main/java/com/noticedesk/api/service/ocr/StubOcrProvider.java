package com.noticedesk.api.service.ocr;

public class StubOcrProvider implements OcrProvider {

    @Override
    public String getName() { return "stub"; }

    @Override
    public OcrResult process(byte[] fileBytes, String filename, String mimeType) {
        return new OcrResult(
                "STUB OCR TEXT: This is a test income tax notice for PAN AABCP1234C. " +
                "Assessment Year 2024-25. Authority: Income Tax Department, Mumbai. " +
                "Notice Number: ITO/Mumbai/2024/1234. Due Date: 2025-03-31.",
                1,
                "stub"
        );
    }
}
