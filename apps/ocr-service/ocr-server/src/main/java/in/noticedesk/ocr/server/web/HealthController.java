package in.noticedesk.ocr.server.web;

import in.noticedesk.ocr.core.OcrEngine;
import in.noticedesk.ocr.server.config.OcrProperties;
import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Lightweight readiness probe distinct from Actuator's {@code /actuator/health}:
 * it reports the OCR engine and which Tesseract language packs are actually
 * installed on disk, so an operator can tell at a glance whether e.g. Hindi is
 * available before pointing traffic at the pod.
 *
 * <p>Returns 200 when at least one language pack is present, 503 otherwise.
 */
@RestController
public class HealthController {

    private final OcrEngine engine;
    private final OcrProperties props;

    public HealthController(OcrEngine engine, OcrProperties props) {
        this.engine = engine;
        this.props = props;
    }

    @GetMapping("/health")
    public ResponseEntity<HealthResponse> health() {
        List<String> languages = installedLanguages();
        boolean ready = !languages.isEmpty();
        HealthResponse body = new HealthResponse(
                ready ? "UP" : "DOWN",
                engine.name(),
                languages,
                effectiveTessdataPath().orElse(null));
        return ResponseEntity
                .status(ready ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE)
                .body(body);
    }

    private Optional<String> effectiveTessdataPath() {
        String configured = props.dataPath();
        if (configured != null && !configured.isBlank()) {
            return Optional.of(configured);
        }
        return Optional.ofNullable(System.getenv("TESSDATA_PREFIX"));
    }

    private List<String> installedLanguages() {
        Optional<String> base = effectiveTessdataPath();
        if (base.isEmpty()) {
            return List.of();
        }
        // TESSDATA_PREFIX may point either at the parent of tessdata or at
        // tessdata itself, depending on the distro — scan both.
        return Stream.of(new File(base.get()), new File(base.get(), "tessdata"))
                .filter(File::isDirectory)
                .flatMap(dir -> {
                    File[] files = dir.listFiles((d, n) -> n.endsWith(".traineddata"));
                    return files == null ? Stream.<File>empty() : Arrays.stream(files);
                })
                .map(f -> f.getName().replace(".traineddata", ""))
                .distinct()
                .sorted()
                .toList();
    }

    public record HealthResponse(
            String status, String engine, List<String> languages, String tessdataPath) {
    }
}
