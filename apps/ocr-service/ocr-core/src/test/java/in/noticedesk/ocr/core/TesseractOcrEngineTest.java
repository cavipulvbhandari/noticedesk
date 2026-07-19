package in.noticedesk.ocr.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import in.noticedesk.ocr.core.render.PageRasterizer;
import in.noticedesk.ocr.core.tesseract.TesseractConfig;
import in.noticedesk.ocr.core.tesseract.TesseractOcrEngine;
import in.noticedesk.ocr.core.tesseract.TesseractPool;
import java.awt.Rectangle;
import java.awt.image.BufferedImage;
import java.util.List;
import java.util.concurrent.TimeUnit;
import net.sourceforge.tess4j.ITesseract;
import net.sourceforge.tess4j.TesseractException;
import net.sourceforge.tess4j.Word;
import org.junit.jupiter.api.Test;

/**
 * Exercises the engine's page loop, text joining and confidence averaging
 * without native Tesseract by injecting a pool over a mocked {@link ITesseract}.
 */
class TesseractOcrEngineTest {

    /** A rasterizer that yields {@code n} blank pages, so no PDF/native needed. */
    private static PageRasterizer fixedPages(int n) {
        return new PageRasterizer() {
            @Override
            public boolean supports(String mimeType) {
                return true;
            }

            @Override
            public List<BufferedImage> rasterize(byte[] content, String mimeType, int dpi) {
                return java.util.stream.IntStream.range(0, n)
                        .mapToObj(i -> new BufferedImage(200, 300, BufferedImage.TYPE_INT_RGB))
                        .toList();
            }
        };
    }

    private static TesseractPool poolOf(ITesseract instance) {
        return new TesseractPool(1, 1, TimeUnit.SECONDS, () -> instance);
    }

    private static TesseractOcrEngine engine(PageRasterizer rasterizer, TesseractPool pool) {
        return new TesseractOcrEngine(TesseractConfig.defaults(null), rasterizer, pool);
    }

    @Test
    void joinsPageTextWithFormFeedAndAveragesConfidence() throws TesseractException {
        ITesseract tess = mock(ITesseract.class);
        when(tess.doOCR(any(BufferedImage.class))).thenReturn("PAGE ONE", "PAGE TWO");
        when(tess.getWords(any(BufferedImage.class), anyInt())).thenReturn(
                List.of(new Word("PAGE", 90f, new Rectangle(1, 2, 3, 4)),
                        new Word("ONE", 80f, new Rectangle(5, 6, 7, 8))),
                List.of(new Word("PAGE", 70f, new Rectangle(0, 0, 1, 1)),
                        new Word("TWO", 60f, new Rectangle(0, 0, 1, 1))));

        ExtractedDocument doc = engine(fixedPages(2), poolOf(tess))
                .extract(OcrRequest.of(new byte[] {1, 2, 3}, "application/pdf"));

        assertEquals(2, doc.pageCount());
        assertEquals("PAGE ONE\fPAGE TWO", doc.text());
        assertEquals("tesseract", doc.engine());
        // page1 mean = 85, page2 mean = 65, doc mean = 75
        assertEquals(75f, doc.meanConfidence(), 0.01f);
        assertEquals(2, doc.pages().get(0).words().size());
        assertEquals(200, doc.pages().get(0).widthPx());
    }

    @Test
    void skipsLayoutWhenNotRequested() throws TesseractException {
        ITesseract tess = mock(ITesseract.class);
        when(tess.doOCR(any(BufferedImage.class))).thenReturn("HELLO");

        OcrRequest req = new OcrRequest(
                new byte[] {9}, "application/pdf",
                OcrOptions.builder().includeLayout(false).build());

        ExtractedDocument doc = engine(fixedPages(1), poolOf(tess)).extract(req);

        assertEquals("HELLO", doc.text());
        assertTrue(doc.pages().get(0).words().isEmpty());
        // getWords must never be called when layout is off.
        org.mockito.Mockito.verify(tess, org.mockito.Mockito.never())
                .getWords(any(BufferedImage.class), anyInt());
    }

    @Test
    void missingLanguageDataIsPermanent() throws TesseractException {
        ITesseract tess = mock(ITesseract.class);
        when(tess.doOCR(any(BufferedImage.class)))
                .thenThrow(new TesseractException("Failed loading language 'hin'"));

        TesseractOcrEngine engine = engine(fixedPages(1), poolOf(tess));
        OcrRequest req = new OcrRequest(
                new byte[] {1}, "application/pdf",
                OcrOptions.builder().languages(List.of("hin")).build());

        OcrException ex = assertThrows(OcrException.class, () -> engine.extract(req));
        assertTrue(!(ex instanceof OcrTransientException),
                "missing language data must be permanent, not transient");
    }

    @Test
    void genericTesseractFailureIsTransient() throws TesseractException {
        ITesseract tess = mock(ITesseract.class);
        when(tess.doOCR(any(BufferedImage.class)))
                .thenThrow(new TesseractException("some transient native hiccup"));

        TesseractOcrEngine engine = engine(fixedPages(1), poolOf(tess));
        assertThrows(OcrTransientException.class,
                () -> engine.extract(OcrRequest.of(new byte[] {1}, "application/pdf")));
    }
}
