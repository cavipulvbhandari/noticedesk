package in.noticedesk.ocr.core.render;

import in.noticedesk.ocr.core.OcrException;
import in.noticedesk.ocr.core.OcrTransientException;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.rendering.ImageType;
import org.apache.pdfbox.rendering.PDFRenderer;

/**
 * Rasterizes PDF pages with Apache PDFBox. Pure Java — no native poppler
 * dependency, which keeps the container image small and the build hermetic.
 */
public final class PdfPageRasterizer implements PageRasterizer {

    private static final String PDF_MIME = "application/pdf";

    /**
     * Guard against pathological inputs (a 10,000-page scan) exhausting memory.
     * Zero or negative means unbounded.
     */
    private final int maxPages;

    public PdfPageRasterizer(int maxPages) {
        this.maxPages = maxPages;
    }

    @Override
    public boolean supports(String mimeType) {
        return mimeType != null && mimeType.toLowerCase().startsWith(PDF_MIME);
    }

    @Override
    public List<BufferedImage> rasterize(byte[] content, String mimeType, int dpi) {
        try (PDDocument document = Loader.loadPDF(content)) {
            int pageCount = document.getNumberOfPages();
            if (pageCount == 0) {
                throw new OcrException("PDF has no pages");
            }
            if (maxPages > 0 && pageCount > maxPages) {
                throw new OcrException(
                        "PDF has " + pageCount + " pages, exceeding the limit of " + maxPages);
            }
            PDFRenderer renderer = new PDFRenderer(document);
            List<BufferedImage> images = new ArrayList<>(pageCount);
            for (int i = 0; i < pageCount; i++) {
                try {
                    images.add(renderer.renderImageWithDPI(i, dpi, ImageType.RGB));
                } catch (IOException e) {
                    // A single page failing to render is often transient (a
                    // corrupt object stream we might re-fetch cleanly).
                    throw new OcrTransientException(
                            "failed to rasterize PDF page " + (i + 1), e);
                }
            }
            return images;
        } catch (OcrException e) {
            throw e;
        } catch (IOException e) {
            // loadPDF failing means the bytes are not a usable PDF — permanent.
            throw new OcrException("could not parse PDF document", e);
        }
    }
}
