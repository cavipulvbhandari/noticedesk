package in.noticedesk.ocr.server.web;

import in.noticedesk.ocr.core.ExtractedDocument;
import in.noticedesk.ocr.core.OcrEngine;
import in.noticedesk.ocr.core.OcrException;
import in.noticedesk.ocr.core.OcrOptions;
import in.noticedesk.ocr.core.OcrRequest;
import in.noticedesk.ocr.server.config.OcrProperties;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

/**
 * OCR endpoint.
 *
 * <pre>
 * POST /v1/extract        (multipart/form-data)
 *   file          (required) the document bytes
 *   languages     (optional) comma-separated Tesseract langs, e.g. "eng,hin"
 *   dpi           (optional) PDF rasterization DPI
 *   includeLayout (optional) return word bounding boxes (default true)
 * </pre>
 *
 * The controller is thin: it validates input, delegates to the {@link OcrEngine},
 * and maps the result. All error translation lives in
 * {@link OcrExceptionHandler}.
 */
@RestController
@RequestMapping("/v1")
public class OcrController {

    private static final Logger log = LoggerFactory.getLogger(OcrController.class);

    private final OcrEngine engine;
    private final OcrProperties props;

    public OcrController(OcrEngine engine, OcrProperties props) {
        this.engine = engine;
        this.props = props;
    }

    @PostMapping(
            path = "/extract",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ExtractResponse extract(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "languages", required = false) String languages,
            @RequestParam(value = "dpi", required = false) Integer dpi,
            @RequestParam(value = "includeLayout", required = false) Boolean includeLayout)
            throws IOException {

        if (file == null || file.isEmpty()) {
            throw new OcrException("no file provided (multipart part 'file' is required)");
        }

        OcrOptions options = OcrOptions.builder()
                .languages(parseLanguages(languages))
                .dpi(dpi != null ? dpi : props.dpi())
                .includeLayout(includeLayout == null || includeLayout)
                .build();

        String mimeType = file.getContentType();
        long start = System.nanoTime();
        ExtractedDocument doc =
                engine.extract(new OcrRequest(file.getBytes(), mimeType, options));
        long millis = (System.nanoTime() - start) / 1_000_000;

        log.info(
                "ocr.extract engine={} filename={} bytes={} mime={} pages={} conf={} took_ms={}",
                engine.name(),
                file.getOriginalFilename(),
                file.getSize(),
                mimeType,
                doc.pageCount(),
                String.format("%.1f", doc.meanConfidence()),
                millis);

        return ExtractResponse.from(doc);
    }

    private List<String> parseLanguages(String languages) {
        if (languages == null || languages.isBlank()) {
            return props.defaultLanguages();
        }
        // Accept both "eng,hin" and Tesseract's own "eng+hin" spelling.
        return Arrays.stream(languages.split("[,+]"))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .toList();
    }
}
