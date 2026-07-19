package in.noticedesk.ocr.server.web;

import in.noticedesk.ocr.core.ExtractedDocument;
import in.noticedesk.ocr.core.PageResult;
import in.noticedesk.ocr.core.RecognizedWord;
import java.util.List;

/**
 * Wire response for {@code POST /v1/extract}. Deliberately a flat, stable
 * contract independent of the core model so we can evolve internals without
 * breaking clients (notably the Python {@code SelfHostedOCRProvider}).
 */
public record ExtractResponse(
        String text,
        int pageCount,
        String engine,
        float meanConfidence,
        Layout layout) {

    public record Layout(List<Page> pages) {
    }

    public record Page(
            int pageNumber,
            int width,
            int height,
            float meanConfidence,
            List<Word> words) {
    }

    public record Word(String text, float confidence, Box box) {
    }

    public record Box(int x, int y, int width, int height) {
    }

    public static ExtractResponse from(ExtractedDocument doc) {
        List<Page> pages = doc.pages().stream().map(ExtractResponse::toPage).toList();
        return new ExtractResponse(
                doc.text(),
                doc.pageCount(),
                doc.engine(),
                doc.meanConfidence(),
                new Layout(pages));
    }

    private static Page toPage(PageResult p) {
        List<Word> words = p.words().stream().map(ExtractResponse::toWord).toList();
        return new Page(p.pageNumber(), p.widthPx(), p.heightPx(), p.meanConfidence(), words);
    }

    private static Word toWord(RecognizedWord w) {
        return new Word(
                w.text(),
                w.confidence(),
                new Box(w.box().x(), w.box().y(), w.box().width(), w.box().height()));
    }
}
