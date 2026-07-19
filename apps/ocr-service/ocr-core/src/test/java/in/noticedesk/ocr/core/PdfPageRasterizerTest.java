package in.noticedesk.ocr.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import in.noticedesk.ocr.core.render.PdfPageRasterizer;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.List;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.junit.jupiter.api.Test;

/** Rasterization is pure-Java (PDFBox) so it runs without native Tesseract. */
class PdfPageRasterizerTest {

    private static byte[] pdfWithPages(int pages) throws Exception {
        try (PDDocument doc = new PDDocument()) {
            for (int i = 0; i < pages; i++) {
                PDPage page = new PDPage(PDRectangle.A4);
                doc.addPage(page);
                try (PDPageContentStream cs = new PDPageContentStream(doc, page)) {
                    cs.beginText();
                    cs.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA), 24);
                    cs.newLineAtOffset(72, 700);
                    cs.showText("Page " + (i + 1) + " NOTICE");
                    cs.endText();
                }
            }
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            doc.save(out);
            return out.toByteArray();
        }
    }

    @Test
    void rasterizesOneImagePerPage() throws Exception {
        byte[] pdf = pdfWithPages(3);
        List<BufferedImage> images =
                new PdfPageRasterizer(0).rasterize(pdf, "application/pdf", 150);
        assertEquals(3, images.size());
        assertTrue(images.get(0).getWidth() > 0);
        assertTrue(images.get(0).getHeight() > 0);
    }

    @Test
    void supportsPdfOnly() {
        PdfPageRasterizer r = new PdfPageRasterizer(0);
        assertTrue(r.supports("application/pdf"));
        assertFalse(r.supports("image/png"));
    }

    @Test
    void rejectsPdfOverPageLimit() throws Exception {
        byte[] pdf = pdfWithPages(3);
        PdfPageRasterizer capped = new PdfPageRasterizer(2);
        assertThrows(OcrException.class,
                () -> capped.rasterize(pdf, "application/pdf", 150));
    }

    @Test
    void rejectsNonPdfBytes() {
        PdfPageRasterizer r = new PdfPageRasterizer(0);
        assertThrows(OcrException.class,
                () -> r.rasterize("not a pdf".getBytes(), "application/pdf", 150));
    }
}
