package in.noticedesk.ocr.core.render;

import in.noticedesk.ocr.core.OcrException;
import java.awt.image.BufferedImage;
import java.util.List;

/**
 * Dispatches to the first delegate that {@link PageRasterizer#supports}
 * a given MIME type. This is what the engine talks to, so adding a new format
 * is a matter of registering another delegate — the engine never changes.
 */
public final class CompositePageRasterizer implements PageRasterizer {

    private final List<PageRasterizer> delegates;

    public CompositePageRasterizer(List<PageRasterizer> delegates) {
        this.delegates = List.copyOf(delegates);
    }

    /** The standard set: PDF (PDFBox) + raster images (ImageIO). */
    public static CompositePageRasterizer standard(int maxPdfPages) {
        return new CompositePageRasterizer(List.of(
                new PdfPageRasterizer(maxPdfPages),
                new ImagePageRasterizer()));
    }

    @Override
    public boolean supports(String mimeType) {
        return delegates.stream().anyMatch(d -> d.supports(mimeType));
    }

    @Override
    public List<BufferedImage> rasterize(byte[] content, String mimeType, int dpi) {
        for (PageRasterizer delegate : delegates) {
            if (delegate.supports(mimeType)) {
                return delegate.rasterize(content, mimeType, dpi);
            }
        }
        throw new OcrException("unsupported document type: " + mimeType);
    }
}
