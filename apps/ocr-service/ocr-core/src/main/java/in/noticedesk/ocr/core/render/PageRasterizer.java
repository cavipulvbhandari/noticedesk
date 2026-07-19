package in.noticedesk.ocr.core.render;

import java.awt.image.BufferedImage;
import java.util.List;

/**
 * Turns raw document bytes into one {@link BufferedImage} per page, ready for
 * OCR. Decoupled from the OCR engine so PDF/image handling can evolve (or be
 * swapped for a native renderer) without touching Tesseract code.
 */
public interface PageRasterizer {

    /**
     * @param content  raw document bytes
     * @param mimeType IANA media type of {@code content}
     * @param dpi      target resolution for vector formats (PDF); ignored for
     *                 raster formats, which are decoded at their native size
     * @return one image per page, in document order (never empty)
     */
    List<BufferedImage> rasterize(byte[] content, String mimeType, int dpi);

    /** Whether this rasterizer can handle the given MIME type. */
    boolean supports(String mimeType);
}
