package in.noticedesk.ocr.core.tesseract;

import java.util.List;

/**
 * Static configuration for {@link TesseractOcrEngine}. Framework-free so the
 * engine can be constructed from Spring properties, a plain main(), or a test.
 *
 * @param dataPath            filesystem path to the parent of {@code tessdata}
 *                            (Tesseract's {@code TESSDATA_PREFIX}); {@code null}
 *                            lets tess4j fall back to the environment variable
 * @param defaultLanguages   languages used when a request doesn't specify any
 * @param pageSegMode        Tesseract PSM (default 3 = fully automatic)
 * @param ocrEngineMode      Tesseract OEM (default 1 = LSTM only)
 * @param poolSize           number of native contexts / max concurrent OCR
 * @param borrowTimeoutMillis how long to wait for a free worker before 503
 * @param maxPdfPages        reject PDFs above this page count (0 = unbounded)
 */
public record TesseractConfig(
        String dataPath,
        List<String> defaultLanguages,
        int pageSegMode,
        int ocrEngineMode,
        int poolSize,
        long borrowTimeoutMillis,
        int maxPdfPages) {

    public TesseractConfig {
        defaultLanguages = (defaultLanguages == null || defaultLanguages.isEmpty())
                ? List.of("eng")
                : List.copyOf(defaultLanguages);
        if (poolSize <= 0) {
            poolSize = Math.max(1, Runtime.getRuntime().availableProcessors());
        }
        if (borrowTimeoutMillis <= 0) {
            borrowTimeoutMillis = 30_000L;
        }
    }

    /** Reasonable defaults: LSTM, auto page segmentation, one worker per CPU. */
    public static TesseractConfig defaults(String dataPath) {
        return new TesseractConfig(
                dataPath,
                List.of("eng"),
                /* pageSegMode = PSM_AUTO */ 3,
                /* ocrEngineMode = OEM_LSTM_ONLY */ 1,
                /* poolSize (0 -> #CPUs) */ 0,
                30_000L,
                /* maxPdfPages */ 500);
    }
}
