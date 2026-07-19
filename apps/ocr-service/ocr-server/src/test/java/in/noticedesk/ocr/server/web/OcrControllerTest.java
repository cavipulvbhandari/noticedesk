package in.noticedesk.ocr.server.web;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import in.noticedesk.ocr.core.BoundingBox;
import in.noticedesk.ocr.core.ExtractedDocument;
import in.noticedesk.ocr.core.OcrEngine;
import in.noticedesk.ocr.core.OcrException;
import in.noticedesk.ocr.core.OcrTransientException;
import in.noticedesk.ocr.core.PageResult;
import in.noticedesk.ocr.core.RecognizedWord;
import in.noticedesk.ocr.server.config.OcrProperties;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.mockito.Mockito;

/** MockMvc slice: exercises the HTTP contract with a mocked engine (no native). */
@WebMvcTest(controllers = {OcrController.class, HealthController.class})
@Import(OcrControllerTest.MockConfig.class)
class OcrControllerTest {

    @Autowired
    MockMvc mvc;

    @Autowired
    OcrEngine engine;

    @org.junit.jupiter.api.BeforeEach
    void resetMock() {
        // The mock bean is a context singleton reused across test methods;
        // reset so stubbings from one test don't leak into the next.
        Mockito.reset(engine);
    }

    @TestConfiguration
    static class MockConfig {
        @Bean
        OcrEngine ocrEngine() {
            return Mockito.mock(OcrEngine.class);
        }

        @Bean
        OcrProperties ocrProperties() {
            return new OcrProperties(null, List.of("eng"), 300, 3, 1, 1, 30_000L, 500);
        }
    }

    private MockMultipartFile pdfPart() {
        return new MockMultipartFile(
                "file", "notice.pdf", "application/pdf", new byte[] {1, 2, 3, 4});
    }

    @Test
    void extractReturnsTextAndLayout() throws Exception {
        ExtractedDocument doc = new ExtractedDocument(
                "HELLO NOTICE", 1, "tesseract", 92.5f,
                List.of(new PageResult(1, "HELLO NOTICE", 200, 300, 92.5f,
                        List.of(new RecognizedWord("HELLO", 95f, new BoundingBox(1, 2, 3, 4))))));
        when(engine.extract(any())).thenReturn(doc);

        mvc.perform(multipart("/v1/extract").file(pdfPart()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.text").value("HELLO NOTICE"))
                .andExpect(jsonPath("$.pageCount").value(1))
                .andExpect(jsonPath("$.engine").value("tesseract"))
                .andExpect(jsonPath("$.layout.pages[0].words[0].text").value("HELLO"))
                .andExpect(jsonPath("$.layout.pages[0].words[0].box.width").value(3));
    }

    @Test
    void permanentErrorMapsTo422() throws Exception {
        when(engine.extract(any())).thenThrow(new OcrException("corrupt file"));

        mvc.perform(multipart("/v1/extract").file(pdfPart()))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.error").value("permanent"))
                .andExpect(jsonPath("$.retryable").value(false));
    }

    @Test
    void transientErrorMapsTo503() throws Exception {
        when(engine.extract(any())).thenThrow(new OcrTransientException("pool saturated"));

        mvc.perform(multipart("/v1/extract").file(pdfPart()))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error").value("transient"))
                .andExpect(jsonPath("$.retryable").value(true));
    }
}
