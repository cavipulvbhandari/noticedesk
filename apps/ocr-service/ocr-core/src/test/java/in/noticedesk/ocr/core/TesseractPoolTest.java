package in.noticedesk.ocr.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import in.noticedesk.ocr.core.tesseract.TesseractPool;
import java.util.concurrent.TimeUnit;
import net.sourceforge.tess4j.ITesseract;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

class TesseractPoolTest {

    @Test
    void returnsInstanceToPoolAfterUse() {
        ITesseract inst = Mockito.mock(ITesseract.class);
        TesseractPool pool = new TesseractPool(1, 1, TimeUnit.SECONDS, () -> inst);

        String a = pool.withInstance(i -> "a");
        String b = pool.withInstance(i -> "b"); // would block forever if not returned
        assertEquals("a", a);
        assertEquals("b", b);
    }

    @Test
    void saturatedPoolTimesOutTransiently() throws InterruptedException {
        ITesseract inst = Mockito.mock(ITesseract.class);
        TesseractPool pool = new TesseractPool(1, 50, TimeUnit.MILLISECONDS, () -> inst);

        // Hold the single instance on another thread, then a borrow must 503.
        Thread holder = new Thread(() -> pool.withInstance(i -> {
            try {
                Thread.sleep(300);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            return null;
        }));
        holder.start();
        Thread.sleep(30); // let the holder grab it

        assertThrows(OcrTransientException.class, () -> pool.withInstance(i -> "x"));
        holder.join();
    }
}
