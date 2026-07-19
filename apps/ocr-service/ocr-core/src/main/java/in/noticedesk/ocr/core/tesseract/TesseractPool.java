package in.noticedesk.ocr.core.tesseract;

import in.noticedesk.ocr.core.OcrTransientException;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;
import net.sourceforge.tess4j.ITesseract;

/**
 * Bounded pool of {@link ITesseract} instances.
 *
 * <p>Tess4J's {@code Tesseract} is <b>not</b> thread-safe: each native handle
 * holds mutable state and one in-flight recognition. Rather than serialize all
 * OCR behind a single lock (throughput of one) or allocate an unbounded number
 * of native contexts (memory blow-up under load), we keep a fixed pool. The
 * size is the real concurrency knob for the service and the cap on native
 * memory.
 *
 * <p>Borrowing blocks up to a timeout; exceeding it surfaces as a
 * {@link OcrTransientException} so the caller retries rather than failing hard.
 */
public final class TesseractPool implements AutoCloseable {

    private final BlockingQueue<ITesseract> instances;
    private final long borrowTimeoutMillis;
    private final int size;

    /**
     * @param size            number of native contexts (== max concurrent OCR)
     * @param borrowTimeout   how long a caller waits for a free instance
     * @param timeoutUnit     unit for {@code borrowTimeout}
     * @param instanceFactory creates a fully-configured {@link ITesseract}
     */
    public TesseractPool(
            int size,
            long borrowTimeout,
            TimeUnit timeoutUnit,
            Supplier<ITesseract> instanceFactory) {
        if (size <= 0) {
            throw new IllegalArgumentException("pool size must be > 0, was " + size);
        }
        this.size = size;
        this.borrowTimeoutMillis = timeoutUnit.toMillis(borrowTimeout);
        this.instances = new ArrayBlockingQueue<>(size);
        for (int i = 0; i < size; i++) {
            instances.add(instanceFactory.get());
        }
    }

    public int size() {
        return size;
    }

    /** Run {@code work} with an exclusively-borrowed instance, always returning it. */
    public <T> T withInstance(TesseractWork<T> work) {
        ITesseract instance = borrow();
        try {
            return work.apply(instance);
        } finally {
            instances.add(instance);
        }
    }

    private ITesseract borrow() {
        try {
            ITesseract instance = instances.poll(borrowTimeoutMillis, TimeUnit.MILLISECONDS);
            if (instance == null) {
                throw new OcrTransientException(
                        "no OCR worker available within " + borrowTimeoutMillis
                                + "ms (pool of " + size + " saturated)");
            }
            return instance;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new OcrTransientException("interrupted while waiting for an OCR worker", e);
        }
    }

    @Override
    public void close() {
        instances.clear();
    }

    /** Work performed against a borrowed instance. */
    @FunctionalInterface
    public interface TesseractWork<T> {
        T apply(ITesseract instance);
    }
}
