package in.noticedesk.ocr.core.render;

import in.noticedesk.ocr.core.OcrException;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import javax.imageio.ImageIO;
import javax.imageio.ImageReader;
import javax.imageio.stream.ImageInputStream;

/**
 * Rasterizes raster image formats (PNG, JPEG, TIFF, BMP, GIF) via ImageIO.
 * Multi-page TIFFs — common for scanned notices — expand to one image per
 * frame. DPI is ignored: raster images are decoded at their native resolution.
 */
public final class ImagePageRasterizer implements PageRasterizer {

    private static final Set<String> SUPPORTED_PREFIXES = Set.of(
            "image/png", "image/jpeg", "image/jpg", "image/tiff",
            "image/bmp", "image/gif", "image/x-png");

    @Override
    public boolean supports(String mimeType) {
        if (mimeType == null) {
            return false;
        }
        String lower = mimeType.toLowerCase();
        return SUPPORTED_PREFIXES.stream().anyMatch(lower::startsWith);
    }

    @Override
    public List<BufferedImage> rasterize(byte[] content, String mimeType, int dpi) {
        try (ImageInputStream iis = ImageIO.createImageInputStream(
                new ByteArrayInputStream(content))) {
            if (iis == null) {
                throw new OcrException("could not open image stream for " + mimeType);
            }
            Iterator<ImageReader> readers = ImageIO.getImageReaders(iis);
            if (!readers.hasNext()) {
                throw new OcrException("no image reader available for " + mimeType);
            }
            ImageReader reader = readers.next();
            try {
                reader.setInput(iis);
                int frames = reader.getNumImages(true);
                if (frames <= 0) {
                    frames = 1;
                }
                List<BufferedImage> images = new ArrayList<>(frames);
                for (int i = 0; i < frames; i++) {
                    images.add(reader.read(i));
                }
                return images;
            } finally {
                reader.dispose();
            }
        } catch (IOException e) {
            throw new OcrException("could not decode image (" + mimeType + ")", e);
        }
    }
}
