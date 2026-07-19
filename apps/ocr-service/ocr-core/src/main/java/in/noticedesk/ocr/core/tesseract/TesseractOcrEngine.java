package in.noticedesk.ocr.core.tesseract;

import in.noticedesk.ocr.core.BoundingBox;
import in.noticedesk.ocr.core.ExtractedDocument;
import in.noticedesk.ocr.core.OcrEngine;
import in.noticedesk.ocr.core.OcrException;
import in.noticedesk.ocr.core.OcrRequest;
import in.noticedesk.ocr.core.OcrTransientException;
import in.noticedesk.ocr.core.PageResult;
import in.noticedesk.ocr.core.RecognizedWord;
import in.noticedesk.ocr.core.render.CompositePageRasterizer;
import in.noticedesk.ocr.core.render.PageRasterizer;
import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.List;
import net.sourceforge.tess4j.ITessAPI;
import net.sourceforge.tess4j.ITesseract;
import net.sourceforge.tess4j.Tesseract;
import net.sourceforge.tess4j.TesseractException;
import net.sourceforge.tess4j.Word;

/**
 * {@link OcrEngine} backed by Tesseract via Tess4J.
 *
 * <p>Flow: rasterize the document to page images, then OCR each page on a
 * borrowed native worker. Full page text always comes from {@code doOCR}
 * (accurate layout-aware text). When {@link OcrRequest#options() layout is
 * requested}, a second {@code getWords} pass adds per-word bounding boxes.
 *
 * <p>Thread-safe: all native access goes through a {@link TesseractPool}.
 */
public final class TesseractOcrEngine implements OcrEngine {

    public static final String ENGINE_NAME = "tesseract";

    private final TesseractConfig config;
    private final PageRasterizer rasterizer;
    private final TesseractPool pool;

    public TesseractOcrEngine(TesseractConfig config) {
        this(config, CompositePageRasterizer.standard(config.maxPdfPages()));
    }

    public TesseractOcrEngine(TesseractConfig config, PageRasterizer rasterizer) {
        this(config, rasterizer, new TesseractPool(
                config.poolSize(),
                config.borrowTimeoutMillis(),
                java.util.concurrent.TimeUnit.MILLISECONDS,
                () -> newInstance(config)));
    }

    /**
     * Full-injection constructor — lets tests supply a pool over mocked native
     * instances so the aggregation logic is exercised without real Tesseract.
     */
    public TesseractOcrEngine(
            TesseractConfig config, PageRasterizer rasterizer, TesseractPool pool) {
        this.config = config;
        this.rasterizer = rasterizer;
        this.pool = pool;
    }

    @Override
    public String name() {
        return ENGINE_NAME;
    }

    @Override
    public ExtractedDocument extract(OcrRequest request) {
        List<BufferedImage> pageImages =
                rasterizer.rasterize(request.content(), request.mimeType(), request.options().dpi());

        String language = request.options().languageString();
        boolean includeLayout = request.options().includeLayout();

        List<PageResult> pages = new ArrayList<>(pageImages.size());
        for (int i = 0; i < pageImages.size(); i++) {
            BufferedImage image = pageImages.get(i);
            pages.add(ocrPage(i + 1, image, language, includeLayout));
        }

        String joinedText = joinPages(pages);
        float docConfidence = meanConfidence(pages);
        return new ExtractedDocument(
                joinedText, pages.size(), ENGINE_NAME, docConfidence, pages);
    }

    private PageResult ocrPage(
            int pageNumber, BufferedImage image, String language, boolean includeLayout) {
        return pool.withInstance(tess -> {
            tess.setLanguage(language);
            String text;
            try {
                text = tess.doOCR(image);
            } catch (TesseractException e) {
                throw classify(e, language);
            }

            List<RecognizedWord> words = List.of();
            float confidence = 0f;
            if (includeLayout) {
                List<Word> tessWords = tess.getWords(
                        image, ITessAPI.TessPageIteratorLevel.RIL_WORD);
                words = new ArrayList<>(tessWords.size());
                double confSum = 0;
                for (Word w : tessWords) {
                    words.add(new RecognizedWord(
                            w.getText(),
                            w.getConfidence(),
                            BoundingBox.from(w.getBoundingBox())));
                    confSum += w.getConfidence();
                }
                confidence = tessWords.isEmpty() ? 0f : (float) (confSum / tessWords.size());
            }

            return new PageResult(
                    pageNumber,
                    text == null ? "" : text,
                    image.getWidth(),
                    image.getHeight(),
                    confidence,
                    words);
        });
    }

    /**
     * Map a native failure to our taxonomy. A missing/broken language pack is a
     * configuration problem the caller can't fix by retrying (permanent);
     * everything else we treat as transient and let the retry loop handle.
     */
    private OcrException classify(TesseractException e, String language) {
        String msg = e.getMessage() == null ? "" : e.getMessage().toLowerCase();
        if (msg.contains("failed loading language")
                || msg.contains("could not initialize tesseract")
                || msg.contains("data file")) {
            return new OcrException(
                    "Tesseract cannot load language '" + language
                            + "'; is the traineddata installed? (" + e.getMessage() + ")",
                    e);
        }
        return new OcrTransientException("Tesseract OCR failed: " + e.getMessage(), e);
    }

    private static String joinPages(List<PageResult> pages) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < pages.size(); i++) {
            if (i > 0) {
                sb.append(ExtractedDocument.PAGE_SEPARATOR);
            }
            sb.append(pages.get(i).text());
        }
        return sb.toString();
    }

    private static float meanConfidence(List<PageResult> pages) {
        List<PageResult> scored = pages.stream().filter(p -> !p.words().isEmpty()).toList();
        if (scored.isEmpty()) {
            return 0f;
        }
        double sum = 0;
        for (PageResult p : scored) {
            sum += p.meanConfidence();
        }
        return (float) (sum / scored.size());
    }

    private static ITesseract newInstance(TesseractConfig config) {
        Tesseract t = new Tesseract();
        if (config.dataPath() != null && !config.dataPath().isBlank()) {
            t.setDatapath(config.dataPath());
        }
        t.setLanguage(String.join("+", config.defaultLanguages()));
        t.setPageSegMode(config.pageSegMode());
        t.setOcrEngineMode(config.ocrEngineMode());
        return t;
    }
}
