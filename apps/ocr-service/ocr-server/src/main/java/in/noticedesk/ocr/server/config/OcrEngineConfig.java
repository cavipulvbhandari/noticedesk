package in.noticedesk.ocr.server.config;

import in.noticedesk.ocr.core.OcrEngine;
import in.noticedesk.ocr.core.tesseract.TesseractConfig;
import in.noticedesk.ocr.core.tesseract.TesseractOcrEngine;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Wires the framework-free {@link OcrEngine} into the Spring context. Swapping
 * engines (a future ONNX/PaddleOCR backend, say) is a one-line change here and
 * nothing else in the service needs to know.
 */
@Configuration
public class OcrEngineConfig {

    @Bean(destroyMethod = "")
    public OcrEngine ocrEngine(OcrProperties props) {
        TesseractConfig cfg = new TesseractConfig(
                props.dataPath(),
                props.defaultLanguages(),
                props.pageSegMode(),
                props.ocrEngineMode(),
                props.poolSize(),
                props.borrowTimeoutMillis(),
                props.maxPdfPages());
        return new TesseractOcrEngine(cfg);
    }
}
