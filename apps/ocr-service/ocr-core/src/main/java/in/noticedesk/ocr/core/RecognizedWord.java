package in.noticedesk.ocr.core;

/**
 * One word Tesseract recognized on a page.
 *
 * @param text       the word text
 * @param confidence Tesseract confidence in [0, 100]
 * @param box        pixel bounding box on the rasterized page
 */
public record RecognizedWord(String text, float confidence, BoundingBox box) {
}
