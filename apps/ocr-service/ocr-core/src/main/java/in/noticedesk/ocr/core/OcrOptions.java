package in.noticedesk.ocr.core;

import java.util.List;
import java.util.Objects;

/**
 * Per-request knobs for an OCR pass. Immutable; build with {@link #builder()}.
 *
 * <ul>
 *   <li>{@code languages} — Tesseract language codes, e.g. {@code ["eng"]} or
 *       {@code ["eng", "hin"]}. The corresponding {@code <lang>.traineddata}
 *       must be installed on the host.</li>
 *   <li>{@code dpi} — resolution PDF pages are rasterized at before OCR.
 *       300 is the Tesseract sweet spot; higher costs CPU/memory for little
 *       gain, lower degrades accuracy.</li>
 *   <li>{@code includeLayout} — whether to compute word-level bounding boxes.
 *       Skipping it is a meaningful speedup when only plain text is needed.</li>
 * </ul>
 */
public final class OcrOptions {

    private final List<String> languages;
    private final int dpi;
    private final boolean includeLayout;

    private OcrOptions(List<String> languages, int dpi, boolean includeLayout) {
        this.languages = List.copyOf(languages);
        this.dpi = dpi;
        this.includeLayout = includeLayout;
    }

    /** Sensible defaults: English, 300 DPI, layout on. */
    public static OcrOptions defaults() {
        return builder().build();
    }

    public List<String> languages() {
        return languages;
    }

    /** Tesseract's {@code +}-joined language string, e.g. {@code "eng+hin"}. */
    public String languageString() {
        return String.join("+", languages);
    }

    public int dpi() {
        return dpi;
    }

    public boolean includeLayout() {
        return includeLayout;
    }

    public static Builder builder() {
        return new Builder();
    }

    public Builder toBuilder() {
        return new Builder()
                .languages(languages)
                .dpi(dpi)
                .includeLayout(includeLayout);
    }

    public static final class Builder {
        private List<String> languages = List.of("eng");
        private int dpi = 300;
        private boolean includeLayout = true;

        public Builder languages(List<String> languages) {
            if (languages != null && !languages.isEmpty()) {
                this.languages = languages;
            }
            return this;
        }

        public Builder dpi(int dpi) {
            if (dpi > 0) {
                this.dpi = dpi;
            }
            return this;
        }

        public Builder includeLayout(boolean includeLayout) {
            this.includeLayout = includeLayout;
            return this;
        }

        public OcrOptions build() {
            Objects.requireNonNull(languages, "languages");
            return new OcrOptions(languages, dpi, includeLayout);
        }
    }
}
