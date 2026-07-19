package in.noticedesk.ocr.core;

import java.util.List;

/**
 * OCR result for a single page.
 *
 * @param pageNumber     1-based page index
 * @param text           full recognized text for the page
 * @param widthPx        rasterized page width in pixels (layout reference frame)
 * @param heightPx       rasterized page height in pixels
 * @param meanConfidence mean word confidence in [0, 100] for the page
 * @param words          per-word layout; empty when layout was not requested
 */
public record PageResult(
        int pageNumber,
        String text,
        int widthPx,
        int heightPx,
        float meanConfidence,
        List<RecognizedWord> words) {

    public PageResult {
        words = words == null ? List.of() : List.copyOf(words);
    }
}
