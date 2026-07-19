package in.noticedesk.ocr.server.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Externalized OCR configuration, bound from {@code ocr.*} properties /
 * {@code OCR_*} environment variables. See {@code application.yml} for defaults.
 *
 * @param dataPath          {@code TESSDATA_PREFIX}; null falls back to the env var
 * @param defaultLanguages  languages used when a request omits them
 * @param dpi               PDF rasterization DPI
 * @param pageSegMode       Tesseract PSM
 * @param ocrEngineMode     Tesseract OEM
 * @param poolSize          native workers / max concurrency (0 -> #CPUs)
 * @param borrowTimeoutMillis wait for a free worker before returning 503
 * @param maxPdfPages       reject PDFs with more pages than this (0 = unbounded)
 */
@ConfigurationProperties(prefix = "ocr")
public record OcrProperties(
        String dataPath,
        List<String> defaultLanguages,
        Integer dpi,
        Integer pageSegMode,
        Integer ocrEngineMode,
        Integer poolSize,
        Long borrowTimeoutMillis,
        Integer maxPdfPages) {

    public OcrProperties {
        if (defaultLanguages == null || defaultLanguages.isEmpty()) {
            defaultLanguages = List.of("eng");
        }
        if (dpi == null || dpi <= 0) {
            dpi = 300;
        }
        if (pageSegMode == null) {
            pageSegMode = 3; // PSM_AUTO
        }
        if (ocrEngineMode == null) {
            ocrEngineMode = 1; // OEM_LSTM_ONLY
        }
        if (poolSize == null) {
            poolSize = 0; // 0 -> derived from #CPUs by the engine
        }
        if (borrowTimeoutMillis == null || borrowTimeoutMillis <= 0) {
            borrowTimeoutMillis = 30_000L;
        }
        if (maxPdfPages == null) {
            maxPdfPages = 500;
        }
    }
}
