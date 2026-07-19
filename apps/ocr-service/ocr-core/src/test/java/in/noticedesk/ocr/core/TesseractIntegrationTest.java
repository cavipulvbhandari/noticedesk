package in.noticedesk.ocr.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import in.noticedesk.ocr.core.tesseract.TesseractConfig;
import in.noticedesk.ocr.core.tesseract.TesseractOcrEngine;
import java.io.ByteArrayOutputStream;
import java.io.File;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.junit.jupiter.api.Test;

/**
 * Real end-to-end OCR against native Tesseract. Skipped (not failed) when the
 * native library / language data is absent, so hermetic CI stays green while a
 * developer machine or the container image exercises the true path.
 */
class TesseractIntegrationTest {

    private static String tessdata() {
        String env = System.getenv("TESSDATA_PREFIX");
        if (env != null && (new File(env, "eng.traineddata").isFile()
                || new File(env, "tessdata/eng.traineddata").isFile())) {
            return env;
        }
        // Common Linux install locations.
        for (String p : new String[] {
                "/usr/share/tesseract-ocr/5/tessdata",
                "/usr/share/tesseract-ocr/4.00/tessdata",
                "/usr/share/tessdata"}) {
            if (new File(p, "eng.traineddata").isFile()) {
                return p;
            }
        }
        return null;
    }

    private static byte[] noticePdf(String line) throws Exception {
        try (PDDocument doc = new PDDocument()) {
            PDPage page = new PDPage(PDRectangle.A4);
            doc.addPage(page);
            try (PDPageContentStream cs = new PDPageContentStream(doc, page)) {
                cs.beginText();
                cs.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD), 28);
                cs.newLineAtOffset(60, 720);
                cs.showText(line);
                cs.endText();
            }
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            doc.save(out);
            return out.toByteArray();
        }
    }

    @Test
    void recognizesTextFromAGeneratedPdf() throws Exception {
        String dataPath = tessdata();
        assumeTrue(dataPath != null, "native Tesseract eng data not found; skipping");

        TesseractOcrEngine engine =
                new TesseractOcrEngine(TesseractConfig.defaults(dataPath));

        byte[] pdf = noticePdf("INCOME TAX ASSESSMENT NOTICE");
        ExtractedDocument doc =
                engine.extract(OcrRequest.of(pdf, "application/pdf"));

        assertEquals(1, doc.pageCount());
        String text = doc.text().toUpperCase();
        assertTrue(text.contains("NOTICE"),
                "expected 'NOTICE' in OCR output, got: " + doc.text());
        assertTrue(text.contains("ASSESSMENT"),
                "expected 'ASSESSMENT' in OCR output, got: " + doc.text());
        assertFalse(doc.pages().get(0).words().isEmpty(), "expected word-level layout");
        assertTrue(doc.meanConfidence() > 0, "expected a positive mean confidence");
    }
}
