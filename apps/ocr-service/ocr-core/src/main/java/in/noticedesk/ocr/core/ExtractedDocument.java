package in.noticedesk.ocr.core;

import java.util.List;

/**
 * The output of one OCR pass over a whole document.
 *
 * <p>This is the JVM-side analogue of the Python {@code ExtractedDoc}
 * dataclass. {@link #text()}, {@link #pageCount()} and {@link #engine()} map
 * directly onto its fields; {@link #pages()} carries the structured layout the
 * Python side stores as {@code layout_json}.
 *
 * @param text           full document text, pages joined by form feed ({@code \f})
 * @param pageCount      number of pages processed
 * @param engine         engine name, e.g. {@code "tesseract"}
 * @param meanConfidence mean word confidence in [0, 100] across the document
 * @param pages          per-page results (text + optional layout)
 */
public record ExtractedDocument(
        String text,
        int pageCount,
        String engine,
        float meanConfidence,
        List<PageResult> pages) {

    /** Page separator used when joining page text into {@link #text()}. */
    public static final String PAGE_SEPARATOR = "\f";

    public ExtractedDocument {
        pages = pages == null ? List.of() : List.copyOf(pages);
    }
}
